import collections

from carbide.scene.json import NamedSerializable, Serializable


class NamedCollection(Serializable, collections.UserList):
    T = object

    @classmethod
    def __class_getitem__(cls, key):
        if not issubclass(key, NamedSerializable):
            raise RuntimeError(
                'NamedCollection can only be used with NamedSerializable')
        return type(cls.__name__, (cls,), {'T': key})

    @classmethod
    def structure(cls, scene, data):
        return cls().structure_in_place(scene, data)

    def structure_in_place(self, scene, data):
        if not isinstance(data, list):
            raise ValueError(
                'collection of {} not a list'.format(self.T.__name__))
        for v in data:
            self.data.append(self.T.structure_full(scene, v))
        return self

    def destructure(self, scene):
        return [v.destructure_full(scene) for v in self.data]

    def find(self, name):
        for v in self.data:
            vname = getattr(v, 'name', '')
            if vname and vname == name:
                return v
        raise KeyError(
            'could not find {} named `{}`'.format(self.T.__name__, name))
