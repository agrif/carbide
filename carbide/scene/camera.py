from carbide.scene.json import Data, Enum, Tuple, TypedSerializable
from carbide.scene.medium import Medium
from carbide.scene.texture import Texture, DiskTexture
from carbide.scene.transform import Transform, Transformable


class Tonemap(Enum):
    LINEAR = Enum.auto()
    GAMMA = Enum.auto()
    REINHARD = Enum.auto()
    FILMIC = Enum.auto()
    PBRT = Enum.auto()


class Resolution(Tuple):
    width: int = 1000
    height: int = 563


class ReconstructionFilter(Enum):
    DIRAC = Enum.auto()
    BOX = Enum.auto()
    TENT = Enum.auto()
    GAUSSIAN = Enum.auto()
    MITCHELL_NETRAVALI = Enum.auto()
    CATMULL_ROM = Enum.auto()
    LANCZOS = Enum.auto()


class Camera(TypedSerializable, Transformable, Data):
    tonemap: Tonemap = Tonemap.GAMMA
    resolution: Resolution = Data.field(default_factory=Resolution)
    medium: Medium = None
    reconstruction_filter: ReconstructionFilter = ReconstructionFilter.DIRAC
    transform: Transform = Data.field(default_factory=Transform)


class PinholeCamera(Camera):
    type = 'pinhole'
    fov: float = 60.0


class ThinlensCamera(Camera):
    type = 'thinlens'
    fov: float = 60.0
    focus_distance: float = 1.0
    aperture_size: float = 0.001
    cateye: float = 0.0
    focus_pivot: str = ''
    aperture: Texture = Data.field(default_factory=DiskTexture)


class EquirectangularCamera(Camera):
    type = 'equirectangular'


class ProjectionMode(Enum):
    HORIZONTAL_CROSS = Enum.auto()
    VERTICAL_CROSS = Enum.auto()
    ROW = Enum.auto()
    COLUMN = Enum.auto()


class CubemapCamera(Camera):
    type = 'cubemap'
    mode: ProjectionMode = ProjectionMode.HORIZONTAL_CROSS
