import bpy

class MetaProperty:
    prefix = ''
    properties = {}

    def register_properties(self, props, prefix):
        self.prefix = prefix + '_'
        props[prefix] = self
        for k, v in self.properties.items():
            props[self.prefix + k] = v

# this class was originally written to be used for a property
# on a material, referencing a texture.
# so: mat is the object owning the property
#     tex is the object the property points to
# and obj is the object that owns texture_slots
class FakeIDProperty(MetaProperty):
    ID_NAME = None
    HUMAN_NAME = None
    SLOTS_NAME = None

    @property
    def attr_name(self):
        return self.prefix + self.ID_NAME

    @property
    def attr_slot(self):
        return self.prefix + self.ID_NAME + '_slot'

    def __init__(self, name, description, get_obj=lambda x: x):
        self.get_obj = get_obj
        
        def update_id(mat, context):
            tex = getattr(mat, self.attr_name)
            if not tex:
                setattr(mat, self.attr_slot, -1)
                return

            obj = self.get_obj(mat)
            if obj is None:
                return
            
            for i, t in enumerate(getattr(obj, self.SLOTS_NAME)):
                if tex == t.name:
                    setattr(mat, self.attr_slot, i)
                    return

            # invalid setting
            setattr(mat, self.attr_slot, -1)
            setattr(mat, self.attr_name, '')
        
        self.properties = {
            self.attr_slot: bpy.props.IntProperty(
                name=name + ' ' + self.HUMAN_NAME + ' Slot',
                default=-1,
            ),

            self.attr_name: bpy.props.StringProperty(
                name=name + ' ' + self.HUMAN_NAME,
                description=description + ' ' + self.HUMAN_NAME,
                default='',
                update=update_id,
            ),
        }

    def normalize(self, mat):
        obj = self.get_obj(mat)
        if obj is None:
            return

        slots = getattr(obj, self.SLOTS_NAME)
        oldslot = getattr(mat, self.attr_slot)
        slot = oldslot
        oldtex = getattr(mat, self.attr_name)
        tex = oldtex
        
        if oldslot < 0:
            tex = ''
            slot = -1
        else:
            if oldslot >= len(slots) or not slots[oldslot]:
                tex = ''
                slot = -1
            else:
                tex = slots[oldslot].name

        if slot != oldslot:
            setattr(mat, self.attr_slot, slot)
        if tex != oldtex:
            setattr(mat, self.attr_name, tex)

        if slot < 0:
            return None
        return getattr(slots[slot], self.ID_NAME)

    def draw(self, lay, mat, **kwargs):
        obj = self.get_obj(mat)
        if not obj:
            return
        
        self.normalize(mat)
        lay.prop_search(mat, self.attr_name, obj, self.SLOTS_NAME, **kwargs)

