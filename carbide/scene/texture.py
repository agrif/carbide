import math

from carbide.scene.json import Data, Tuple, TypedSerializable


class ColorMixin:
    @classmethod
    def color(cls, r, g, b):
        return cls(Color(r, g, b))

    @classmethod
    def grey(cls, value):
        return cls.color(value, value, value)

    @classmethod
    def white(cls):
        return cls.grey(1.0)

    @classmethod
    def black(cls):
        return cls.grey(0.0)


class Color(ColorMixin, Tuple):
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0

    @classmethod
    def color(cls, r, g, b):
        return cls(r, g, b)

    @classmethod
    def structure(cls, scene, data):
        if not isinstance(data, list):
            return super().structure(scene, [data, data, data])
        return super().structure(scene, data)

    def destructure(self, scene):
        if self.r == self.g and self.g == self.b and self.b == self.r:
            return self.r
        return super().destructure(scene)


class Texture(TypedSerializable, Data):
    @classmethod
    def structure(cls, scene, data):
        if isinstance(data, int) or isinstance(data, float) or \
           isinstance(data, list):
            return ConstantTexture.structure(scene, data)
        if isinstance(data, str):
            return BitmapTexture.structure(scene, data)
        return super().structure(scene, data)


class BitmapTexture(Texture):
    type = 'bitmap'
    file: str
    gamma_correct: bool = True
    interpolate: bool = True
    clamp: bool = False
    scale: float = 1.0

    @classmethod
    def structure(cls, scene, data):
        if isinstance(data, str):
            return cls(data)
        return super().structure(scene, data)

    def destructure(self, scene):
        d = super().destructure(self)
        if set(d.keys()) == {'type', 'file'}:
            return self.file
        return d


class ConstantTexture(ColorMixin, Texture):
    type = 'constant'
    value: Color = Data.field(default_factory=Color)

    @classmethod
    def structure(cls, scene, data):
        return cls(Color.structure(scene, data))

    def destructure(self, scene):
        return self.value.destructure(scene)


class CheckerTexture(Texture):
    type = 'checker'
    on_color: Color = Data.field(default_factory=lambda: Color.grey(0.8))
    off_color: Color = Data.field(default_factory=lambda: Color.grey(0.2))
    res_u: int = 20
    res_v: int = 20


class DiskTexture(ColorMixin, Texture):
    type = 'disk'
    value: Color = Data.field(default_factory=Color.white)


class BladeTexture(ColorMixin, Texture):
    type = 'blade'
    value: Color = Data.field(default_factory=Color.white)
    blades: int = 6
    angle: float = 0.5 * math.pi / 6


class IesTexture(Texture):
    type = 'ies'
    file: str
    resolution: int = 256
