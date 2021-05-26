import os
import tempfile
import time

from carbide.tungsten import Tungsten, TungstenFinished
from carbide.scene.bsdf import Bsdf
from carbide.scene.camera import Camera, PinholeCamera
from carbide.scene.json import Data
from carbide.scene.integrator import Integrator, PathTracer
from carbide.scene.medium import Medium
from carbide.scene.namedcollection import NamedCollection
from carbide.scene.primitive import Primitive


__all__ = ['Renderer', 'Scene']


class Renderer(Data):
    output_directory: str = ''
    output_file: str = 'TungstenRender.png'
    hdr_output_file: str = 'TungstenRenderState.dat'
    variance_output_file: str = ''
    resume_render_file: str = ''
    overwrite_output_files: bool = True
    adaptive_sampling: bool = True
    enable_resume_render: bool = False
    stratified_sampler: bool = True
    scene_bvh: bool = True
    spp: int = 32
    spp_step: int = 16
    # FIXME these are intervals
    checkpoint_interval: float = 0.0
    timeout: float = 0.0
    # FIXME list of output_buffers, containing OutputBufferSettings


class Scene(Data):
    media: NamedCollection[Medium] = \
        Data.field(default_factory=NamedCollection[Medium])
    bsdfs: NamedCollection[Bsdf] = \
        Data.field(default_factory=NamedCollection[Bsdf])
    primitives: NamedCollection[Primitive] = \
        Data.field(default_factory=NamedCollection[Primitive])

    camera: Camera = Data.field(default_factory=PinholeCamera)
    integrator: Integrator = Data.field(default_factory=PathTracer)
    renderer: Renderer = Data.field(default_factory=Renderer)

    @classmethod
    def structure(cls, scene, data):
        # named collections need special care
        scene = cls()
        for k in ['media', 'bsdfs', 'primitives']:
            if k in data:
                getattr(scene, k).structure_in_place(scene, data.get(k, []))
                del data[k]

        # now re-use Data.structure
        cheating = super().structure(scene, data)
        # copy over attrs
        scene.camera = cheating.camera
        scene.integrator = cheating.integrator
        scene.renderer = cheating.renderer

        return scene

    def destructure(self, scene):
        return super().destructure(self)

    def save(self, fname):
        with open(fname, 'w') as f:
            self.dump(self, f)

    def render(self, output, update=None, **kwargs):
        with tempfile.TemporaryDirectory(prefix='carbide.') as tmp:
            scene_name = os.path.join(tmp, 'scene.json')
            self.save(scene_name)

            renderer = Tungsten(scene_name, output_directory=tmp, **kwargs)
            old_status = None
            try:
                while renderer.poll():
                    status = renderer.get_status()
                    if old_status is None or old_status != status:
                        update(status)
                        old_status = status
                    time.sleep(0.2)
            except TungstenFinished:
                pass

            p, = renderer.finish()
            os.replace(p.output_file, output)
