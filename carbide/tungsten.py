import contextlib
import dataclasses
import enum
import json
import os
import os.path
import requests
import socket
import subprocess

__all__ = ['RenderProduct', 'RenderState', 'RenderStatus',
           'TungstenFinished', 'Tungsten']


def find_free_port():
    with contextlib.closing(
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # rare race condition: some other app binds this port
        # before tungsten_server does
        return s.getsockname()[1]


class TungstenFinished(Exception):
    pass


@dataclasses.dataclass
class RenderProduct:
    scene: str
    output_directory: str
    output_file: str
    hdr_output_file: str = None
    variance_output_file: str = None
    resume_render_file: str = None

    @classmethod
    def _get_key(cls, scene, data, k, default=None):
        try:
            v = data.get('renderer', {}).get(k)
            if v:
                return str(v)
            return default
        except KeyError:
            raise ValueError('malformed scene file `{}`'.format(scene))

    @classmethod
    def parse(cls, scene, output_directory=None, output_file=None,
              hdr_output_file=None):
        kwargs = {'scene': os.path.abspath(scene)}
        base = os.path.split(kwargs['scene'])[0]
        try:
            with open(scene) as f:
                data = json.load(f)
        except Exception:
            raise ValueError('could not open scene file `{}`'.format(scene))

        if output_directory is None:
            output_directory = cls._get_key(scene, data, 'output_directory')

        if output_directory is None:
            output_directory = base

        output_directory = os.path.abspath(output_directory)
        kwargs['output_directory'] = output_directory

        if output_file is None:
            output_file = cls._get_key(scene, data, 'output_file',
                                       'TungstenRender.png')
        if output_file:
            kwargs['output_file'] = os.path.abspath(
                os.path.join(output_directory, output_file))

        if hdr_output_file is None:
            hdr_output_file = cls._get_key(scene, data, 'hdr_output_file')
        if hdr_output_file:
            kwargs['hdr_output_file'] = os.path.abspath(
                os.path.join(output_directory, hdr_output_file))

        variance_output_file = cls._get_key(scene, data,
                                            'variance_output_file')
        if variance_output_file:
            kwargs['variance_output_file'] = os.path.abspath(
                os.path.join(output_directory, variance_output_file)
            )

        resume_render_file = cls._get_key(scene, data, 'resume_render_file')
        if resume_render_file:
            kwargs['resume_render_file'] = os.path.abspath(
                os.path.join(output_directory, resume_render_file)
            )

        return cls(**kwargs)


class RenderState(enum.Enum):
    LOADING = enum.auto()
    RENDERING = enum.auto()
    UNKNOWN = enum.auto()

    @classmethod
    def parse(cls, val):
        if isinstance(val, str):
            val = val.upper()
        if val not in cls.__members__:
            return cls.UNKNOWN
        return cls.__members__[val]

    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self.name)


@dataclasses.dataclass
class RenderStatus:
    state: RenderState = RenderState.UNKNOWN
    start_spp: int = 0
    current_spp: int = 0
    next_spp: int = 0
    total_spp: int = 0
    current_scene: str = ''
    completed_scenes: list = dataclasses.field(default_factory=list)
    queued_scenes: list = dataclasses.field(default_factory=list)
    extra: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def parse(cls, val):
        val = val.copy()
        kwargs = {}
        kwargs['state'] = RenderState.parse(val.get('state', None))
        del val['state']
        for f in dataclasses.fields(cls):
            if f.name in val:
                kwargs[f.name] = val[f.name]
                del val[f.name]
        kwargs['extra'] = val
        return cls(**kwargs)


class Tungsten:
    def __init__(self, *scenes, command=None, port=None, log_file=None,
                 threads=None, restart=False, checkpoint=None,
                 input_directory=None, output_directory=None, spp=None,
                 timeout=None, seed=None,
                 output_file=None, hdr_output_file=None):
        if command is None:
            env_command = os.environ.get('TUNGSTEN_SERVER')
            if env_command:
                command = env_command
            else:
                command = 'tungsten_server'
        args = [str(command)]

        if log_file:
            args += ['--log-file', str(log_file)]

        if threads:
            args += ['--threads', str(threads)]

        if restart:
            args += ['--restart']

        if checkpoint:
            args += ['--checkpoint', str(checkpoint)]

        if input_directory:
            args += ['--input-directory', str(input_directory)]

        if output_directory:
            output_directory = str(output_directory)
            args += ['--output-directory', output_directory]

        if spp:
            args += ['--spp', str(spp)]

        if timeout:
            args += ['--timeout', str(timeout)]

        if seed:
            args += ['--seed', str(seed)]

        if output_file:
            output_file = str(output_file)
            args += ['--output-file', output_file]

        if hdr_output_file:
            hdr_output_file = str(hdr_output_file)
            args += ['--hdr-output-file', hdr_output_file]

        if port is None:
            port = find_free_port()
        args += ['--port', str(port)]

        self.products = [
            RenderProduct.parse(str(s), output_directory=output_directory,
                                output_file=output_file,
                                hdr_output_file=hdr_output_file)
            for s in scenes
        ]
        args += [p.scene for p in self.products]

        self.port = port
        self.process = subprocess.Popen(args)

    def poll(self):
        return self.process.poll() is None

    def finish(self, timeout=None):
        code = self.process.wait(timeout=timeout)
        if code:
            raise subprocess.CalledProcessError(code, self.process.args)
        return self.products

    @property
    def pid(self):
        return self.process.pid

    @property
    def returncode(self):
        return self.process.returncode

    def get(self, path, binary=False):
        timeout = 0.5
        try:
            r = requests.get('http://localhost:{}/{}'.format(self.port, path),
                             timeout=timeout)
            r.raise_for_status()
            if binary:
                return r.content
            else:
                return r.text
        except requests.RequestException as e:
            try:
                self.finish(timeout=timeout)
                raise TungstenFinished('tungsten_server has finished') \
                    from None
            except subprocess.TimeoutExpired:
                raise RuntimeError('tungsten_server is not responding') \
                    from e

    def get_log(self):
        return self.get('log')

    def get_status(self):
        return RenderStatus.parse(json.loads(self.get('status')))

    def get_render(self):
        return self.get('render', binary=True)
