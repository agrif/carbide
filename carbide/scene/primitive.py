from carbide.scene.bsdf import Bsdf, LambertBsdf
from carbide.scene.json import Data, Enum, NamedSerializable, TypedSerializable
from carbide.scene.medium import Medium
from carbide.scene.texture import Texture, ConstantTexture
from carbide.scene.transform import Transform, Transformable


class Primitive(NamedSerializable, TypedSerializable, Transformable, Data):
    collection_name = 'primitives'
    name: str = ''
    transform: Transform = Data.field(default_factory=Transform)
    emission: Texture = None
    power: Texture = None
    int_medium: Medium = None
    ext_medium: Medium = None


class Mesh(Primitive):
    type = 'mesh'
    file: str = ''
    smooth: bool = False
    backface_culling: bool = False
    recompute_normals: bool = False
    # FIXME this can be a list or 1 bsdf
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


class Cube(Primitive):
    type = 'cube'
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


class Sphere(Primitive):
    type = 'sphere'
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


class Quad(Primitive):
    type = 'quad'
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


class Disk(Primitive):
    type = 'disk'
    cone_angle: float = 90.0
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


class CurveMode(Enum):
    CYLINDER = Enum.auto()
    HALF_CYLINDER = Enum.auto()
    BCSDF_CYLINDER = Enum.auto()
    RIBBON = Enum.auto()


class Curves(Primitive):
    type = 'curves'
    file: str = ''
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)
    mode: CurveMode = CurveMode.HALF_CYLINDER
    curve_taper: bool = False
    subsample: float = 0.0
    curve_thickness: bool = False


class Point(Primitive):
    type = 'point'


class Skydome(Primitive):
    type = 'skydome'
    temperature: float = 5777.0
    gamma_scale: float = 1.0
    turbidity: float = 3.0
    intensity: float = 2.0
    sample: bool = True


class Cylinder(Primitive):
    type = 'cylinder'
    capped: bool = True
    bsdf: Bsdf = Data.field(default_factory=LambertBsdf)


# FIXME instances


class InfiniteSphere(Primitive):
    type = 'infinite_sphere'
    sample: bool = True


class InfiniteSphereCap(Primitive):
    type = 'infinite_sphere_cap'
    sample: bool = True
    skydome: str = ''
    cap_angle: float = 10.0


# FIXME minecraft_map
