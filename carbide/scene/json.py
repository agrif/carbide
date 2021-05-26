import dataclasses
import enum
import json


class Serializable:
    @classmethod
    def structure(cls, scene, data):
        raise NotImplementedError

    def destructure(self, scene):
        raise NotImplementedError

    @classmethod
    def load(cls, scene, f):
        return cls.structure(scene, json.load(f))

    @classmethod
    def loads(cls, scene, data):
        return cls.structure(scene, json.loads(data))

    def dump(self, scene, f, indent=None):
        return json.dump(self.destructure(scene), f, indent=indent)

    def dumps(self, scene, indent=None):
        return json.dumps(self.destructure(scene), indent=indent)


class NamedSerializable(Serializable):
    collection_name = None

    @classmethod
    def structure(cls, scene, data):
        if isinstance(data, str):
            return getattr(scene, cls.collection_name).find(data)
        return cls.structure_full(scene, data)

    @classmethod
    def structure_full(cls, scene, data):
        return super().structure(scene, data)

    def destructure(self, scene):
        name = getattr(self, 'name', '')
        try:
            if getattr(scene, self.collection_name).find(name) is self:
                return name
        except KeyError:
            pass
        return self.destructure_full(scene)

    def destructure_full(self, scene):
        return super().destructure(scene)


class TypedSerializable(Serializable):
    type = None

    @classmethod
    def structure(cls, scene, data):
        if not isinstance(data, dict):
            raise ValueError('bad value `{!r}` for {}'
                             .format(data, cls.__name__))
        if 'type' not in data:
            raise ValueError('{} needs a type'.format(cls.__name__))
        tag = data['type']

        if cls.type == tag:
            del data['type']
            return super().structure(scene, data)

        def all_subclasses(cls):
            for subcls in cls.__subclasses__():
                yield subcls
                yield from all_subclasses(subcls)

        for subcls in all_subclasses(cls):
            if subcls.type == tag:
                return subcls.structure(scene, data)
        raise ValueError('unknown type `{}` for {}'.format(tag, cls.__name__))

    def destructure(self, scene):
        if not self.type:
            raise RuntimeError('tried to destructure a base class')
        d = {'type': self.type}
        d.update(super().destructure(scene))
        return d


class Enum(Serializable, enum.Enum):
    @classmethod
    def structure(cls, scene, data):
        if isinstance(data, str):
            data = data.upper()
        if data not in cls.__members__:
            raise ValueError('bad value `{!r}` for {}'
                             .format(data, cls.__name__))
        return cls.__members__[data]

    def destructure(self, scene):
        return self.name.lower()

    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self.name)


class DataMeta(type):
    def __new__(cls, name, bases, members):
        self = super().__new__(cls, name, bases, members)
        return dataclasses.dataclass(self)


class DataBase(metaclass=DataMeta):
    @classmethod
    def field(cls, **kwargs):
        return dataclasses.field(**kwargs)

    def modify(self, *args, **kwargs):
        kwargs = kwargs.copy()
        fields = dataclasses.fields(self)
        for i, arg in enumerate(args):
            f = fields[i]
            setattr(self, f.name, arg)
        for f in fields:
            if f.name in kwargs:
                setattr(self, f.name, kwargs[f.name])
                del kwargs[f.name]
        if kwargs:
            k = next(iter(kwargs.keys()))
            raise KeyError('field `{}` does not exist on {}'
                           .format(k, self.__class__.__name__))


class Data(Serializable, DataBase):
    @classmethod
    def structure(cls, scene, data):
        if not isinstance(data, dict):
            raise ValueError('bad value {!r} for {}'
                             .format(data, cls.__name__))
        kwargs = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                if f.default is dataclasses.MISSING and \
                   f.default_factory is dataclasses.MISSING:
                    raise ValueError('required field `{}` missing in {}'
                                     .format(f.name, cls.__name__))
                continue
            kwargs[f.name] = structure(scene, f.type, data[f.name])
            del data[f.name]
        if data:
            n = next(iter(data.keys()))
            raise ValueError('unexpected field `{}` for {}'
                             .format(n, cls.__name__))
        return cls(**kwargs)

    def destructure(self, scene):
        ret = {}
        for f in dataclasses.fields(self):
            if f.default_factory is not dataclasses.MISSING and\
               f.default_factory() == getattr(self, f.name):
                continue
            if getattr(self, f.name) == f.default:
                continue
            ret[f.name] = destructure(scene, getattr(self, f.name))
        return ret


class Tuple(Serializable, DataBase):
    @classmethod
    def structure(cls, scene, data):
        if not isinstance(data, list):
            raise ValueError('bad value {!r} for {}'
                             .format(data, cls.__name__))
        args = []
        for f in dataclasses.fields(cls):
            if len(data) == 0:
                raise ValueError('field `{}` missing in {}'
                                 .format(f.name, cls.__name__))
                continue
            args.append(structure(scene, f.type, data.pop(0)))
        if data:
            n = next(iter(data.keys()))
            raise ValueError('unexpected extra fields for {}'
                             .format(n, cls.__name__))
        return cls(*args)

    def destructure(self, scene):
        ret = []
        for f in dataclasses.fields(self):
            ret.append(destructure(scene, getattr(self, f.name)))
        return ret


def structure(scene, typ, value):
    if issubclass(typ, Serializable):
        return typ.structure(scene, value)
    else:
        if not isinstance(value, typ):
            raise ValueError(
                'bad value {!r} for {}'.format(value, typ.__name__))
        return value


def destructure(scene, value):
    if isinstance(value, Serializable):
        return value.destructure(scene)
    else:
        return value

