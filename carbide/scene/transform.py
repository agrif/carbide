import numpy

from carbide.scene.json import Serializable


class Transformable:
    def apply_transform(self, m):
        self.transform.apply_transform(m)

    def translate(self, x, y, z):
        self.apply_transform(Transform.translation(x, y, z))

    def scale(self, size):
        self.apply_transform(Transform.scaling(size))

    def scale_nonuniform(self, x, y, z):
        self.apply_transform(Transform.scaling_nonuniform(x, y, z))

    def rotate(self, axis, angle):
        self.apply_transform(Transform.rotation(axis, angle))


class Transform(Serializable, Transformable):
    def __init__(self, m=None):
        if m is None:
            m = numpy.identity(4)
        if isinstance(m, Transform):
            m = m.m
        self.m = numpy.array(m)

    def __repr__(self):
        return 'Transform({!r})'.format(self.m)

    def __eq__(self, other):
        return numpy.all(self.m == Transform(other).m)

    @classmethod
    def structure(cls, scene, data):
        # FIXME
        # there are... a lot of options here. Do the easy one now
        # JsonPtr.cpp L108
        if not isinstance(data, list):
            raise ValueError('bad value {!r} for {}'.format(data, cls.__name__))
        if len(data) != 16:
            raise ValueError('{} must be length 16'.format(cls.__name__))
        return cls(numpy.reshape(numpy.array(data), (4, 4), order='C'))

    def destructure(self, scene):
        return list(numpy.reshape(self.m, (16,), order='C'))

    def apply_transform(self, m):
        self.m = Transform(m).m @ self.m

    @classmethod
    def translation(cls, x, y, z):
        return cls([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ])

    @classmethod
    def scaling(cls, size):
        return cls.scaling_nonuniform(size, size, size)

    @classmethod
    def scaling_nonuniform(cls, x, y, z):
        return cls([
            [x, 0, 0, 0],
            [0, y, 0, 0],
            [0, 0, z, 0],
            [0, 0, 0, 1],
        ])

    @classmethod
    def rotation(self, axis, angle):
        sina = numpy.sin(numpy.radians(angle))
        cosa = numpy.cos(numpy.radians(angle))
        direction = numpy.asarray(axis) / (numpy.linalg.norm(axis))
        m3 = numpy.diag([cosa, cosa, cosa])
        m3 += numpy.outer(direction, direction) * (1.0 - cosa)
        direction *= sina
        m3 += numpy.array(
            [[0, -direction[2], direction[1]],
             [direction[2], 0, -direction[0]],
             [-direction[1], direction[0], 0]]
        )
        m = numpy.identity(4)
        m[:3, :3] = m3
        return Transform(m)
