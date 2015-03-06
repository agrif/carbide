import bpy

class MetaProperty:
    prefix = ''
    properties = {}

    def register_properties(self, props, prefix):
        self.prefix = prefix + '_'
        props[prefix] = self
        for k, v in self.properties.items():
            props[self.prefix + k] = v

def meta_propertize(cls):
    d = {}
    for k, v in vars(cls).items():
        if hasattr(v, 'register_properties'):
            v.register_properties(d, k)
    for k, v in d.items():
        setattr(cls, k, v)
    return cls

# this class was originally written to be used for a property
# on a material, referencing a texture.
# so: mat is the object owning the property
#     tex is the object the property points to
class FakeIDProperty(MetaProperty):
    ID_NAME = None
    HUMAN_NAME = None
    COLLECTION = None

    @property
    def attr_name(self):
        return self.prefix + self.ID_NAME

    def __init__(self, name, description):
        def update_id(mat, context):
            self.normalize(mat)

        self.properties = {
            self.attr_name: bpy.props.StringProperty(
                name=name + ' ' + self.HUMAN_NAME,
                description=description + ' ' + self.HUMAN_NAME,
                default='',
                update=update_id,
            ),
        }

    def normalize(self, mat):
        texname = getattr(mat, self.attr_name)
        if not texname:
            return None
        tex = getattr(bpy.data, self.COLLECTION).get(texname)
        if not tex:
            setattr(mat, self.attr_name, '')
            return None
        return tex

    def draw(self, lay, mat, **kwargs):
        self.normalize(mat)
        lay.prop_search(mat, self.attr_name, bpy.data, self.COLLECTION, **kwargs)

