from carbide.scene.json import Data, NamedSerializable, TypedSerializable


class Medium(NamedSerializable, TypedSerializable, Data):
    collection_name = 'media'
    name: str = ''
