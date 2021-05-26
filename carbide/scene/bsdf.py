from carbide.scene.json import Data, NamedSerializable, TypedSerializable
from carbide.scene.texture import Texture, ConstantTexture


class Bsdf(NamedSerializable, TypedSerializable, Data):
    collection_name = 'bsdfs'
    name: str = ''
    albedo: Texture = Data.field(default_factory=ConstantTexture.white)
    bump: Texture = None


class LambertBsdf(Bsdf):
    type = 'lambert'


class MirrorBsdf(Bsdf):
    type = 'mirror'
