import dataclasses
import struct

import numpy
import numpy.typing


Vertex = numpy.dtype([
    ('pos', numpy.float32, 3),
    ('normal', numpy.float32, 3),
    ('uv', numpy.float32, 2),
])


Triangle = numpy.dtype([
    ('vs', numpy.uint32, 3),
    ('material', numpy.int32),
])


LENFMT = struct.Struct('=Q')


@dataclasses.dataclass
class Mesh:
    # dtype = Vertex
    vertices: numpy.recarray
    # dtype = Triangle
    triangles: numpy.recarray

    def __post_init__(self):
        self.vertices = numpy.array(self.vertices, dtype=Vertex) \
                             .view(numpy.recarray)
        self.triangles = numpy.array(self.triangles, dtype=Triangle) \
                              .view(numpy.recarray)

    def dump(self, f):
        f.write(LENFMT.pack(len(self.vertices)))
        self.vertices.tofile(f)
        f.write(LENFMT.pack(len(self.triangles)))
        self.triangles.tofile(f)

    def dumpb(self):
        return b''.join([
            LENFMT.pack(len(self.vertices)),
            self.vertices.tobytes(),
            LENFMT.pack(len(self.triangles)),
            self.triangles.tobytes(),
        ])

    @classmethod
    def load(cls, f):
        nv = LENFMT.unpack(f.read(LENFMT.size))[0]
        vertices = numpy.fromfile(f, dtype=Vertex, count=nv)
        nt = LENFMT.unpack(f.read(LENFMT.size))[0]
        triangles = numpy.fromfile(f, dtype=Triangle, count=nt)
        return cls(vertices, triangles)

    @classmethod
    def loadb(cls, data):
        c = 0

        nv = LENFMT.unpack_from(data, offset=c)[0]
        c += LENFMT.size

        vertices = numpy.frombuffer(data, dtype=Vertex, count=nv, offset=c)
        c += Vertex.itemsize * nv

        nt = LENFMT.unpack_from(data, offset=c)[0]
        c += LENFMT.size

        triangles = numpy.frombuffer(data, dtype=Triangle, count=nt, offset=c)
        c += Triangle.itemsize * nt

        return cls(vertices, triangles)
