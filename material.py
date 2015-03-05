import bpy
from bl_ui import properties_material
from .complex_ior_data import data as ior_data
from .texture import ColorTextureProperty, FloatTextureProperty, TextureProperty
from . import props

class MaterialProperty(props.FakeIDProperty):
    ID_NAME = 'material'
    HUMAN_NAME = 'Material'
    SLOTS_NAME = 'material_slots'
    
    def to_scene_data(self, scene, mat):
        submat = self.normalize(mat)
        if submat:
            return W_PT_context_material.to_scene_data(scene, submat)
        return None

class MaterialExtra(properties_material.MaterialButtonsPanel, bpy.types.Panel):
    bl_label = ""
    w_type = ""

    @classmethod
    def poll(cls, context):
        if W_PT_context_material.poll(context):
            mat = properties_material.active_node_mat(context.material)
            if mat.w_type == cls.w_type:
                return True
        return False

    def draw(self, context):
        mat = properties_material.active_node_mat(context.material)
        self.draw_extra(self.layout, mat)

    @classmethod
    def to_scene_data(self, scene, mat):
        return {}

    def draw_extra(self, lay, mat):
        pass

def lookup_ior(name):
    _, eta, k = [i for i in ior_data if i[0] == name][0]
    return (eta, k)

def update_conductor_material(self, context):
    if self.w_conductor_material != 'CUSTOM':
        eta, k = lookup_ior(self.w_conductor_material)
        self.w_conductor_eta = eta
        self.w_conductor_k = k

class W_PT_conductor(MaterialExtra):
    bl_label = "Conductor"
    w_type = "conductor"

    REGISTER_PROPERTIES = {
        bpy.types.Material: {
            'w_conductor_material': bpy.props.EnumProperty(
                name='Material',
                description='Conductor Material',
                items=[
                    ('CUSTOM', 'Custom', ''),
                ] + [(n, n, '') for n, _, _ in ior_data],
                default='W',
                update=update_conductor_material,
            ),
            'w_conductor_eta': bpy.props.FloatVectorProperty(
                name='Eta',
                description='Conductor Eta',
                min=0,
                default=lookup_ior('W')[0],
            ),

            'w_conductor_k': bpy.props.FloatVectorProperty(
                name='K',
                description='Conductor K',
                min=0,
                default=lookup_ior('W')[1],
            ),
        },
    }

    @classmethod
    def to_scene_data(self, scene, mat):
        return {
            'eta': list(mat.w_conductor_eta),
            'k': list(mat.w_conductor_k),
        }

    def draw_extra(self, lay, mat):
        lay.prop(mat, 'w_conductor_material')

        col = lay.column()
        col.enabled = (mat.w_conductor_material == 'CUSTOM')
        row = col.row()
        row.prop(mat, 'w_conductor_eta')
        row = col.row()
        row.prop(mat, 'w_conductor_k')

class W_PT_dielectric(MaterialExtra):
    bl_label = "Dielectric"
    w_type = "dielectric"

    REGISTER_PROPERTIES = {
        bpy.types.Material: {
            'w_dielectric_ior': bpy.props.FloatProperty(
                name='IOR',
                description='Dielectric IOR',
                min=0,
                default=1.5,
            ),

            'w_dielectric_enable_refraction': bpy.props.BoolProperty(
                name='Refraction',
                description='Enable Refraction',
                default=True,
            ),
        },
    }

    @classmethod
    def to_scene_data(self, scene, mat):
        return {
            'ior': mat.w_dielectric_ior,
            'enable_refraction': mat.w_dielectric_enable_refraction,
        }

    def draw_extra(self, lay, mat):
        row = lay.row()
        row.prop(mat, 'w_dielectric_enable_refraction')
        row.prop(mat, 'w_dielectric_ior')

def get_material_object(mat):
    # FIXME
    for o in bpy.data.objects:
        for ms in o.material_slots:
            if ms.material == mat:
                return o
    return None

class W_PT_mixed(MaterialExtra):
    bl_label = "Mixed"
    w_type = "mixed"

    REGISTER_PROPERTIES = {
        bpy.types.Material: {
            'w_mixed0': MaterialProperty(
                name='First',
                description='First',
                get_obj=get_material_object,
            ),

            'w_mixed1': MaterialProperty(
                name='Second',
                description='Second',
                get_obj=get_material_object,
            ),

            'w_mixed_ratio': FloatTextureProperty(
                name='Ratio',
                description='Ratio',
                default=0.5,
            ),
        },
    }

    @classmethod
    def to_scene_data(self, scene, mat):
        d = {
            'ratio': mat.w_mixed_ratio.to_scene_data(scene, mat),
        }
        
        m0 = mat.w_mixed0.to_scene_data(scene, mat)
        m1 = mat.w_mixed1.to_scene_data(scene, mat)
        if m0:
            d['bsdf0'] = m0[1]
        if m1:
            d['bsdf1'] = m1[1]

        return d

    def draw_extra(self, lay, mat):
        mat.w_mixed0.draw(lay, mat)
        mat.w_mixed1.draw(lay, mat)
        mat.w_mixed_ratio.draw(lay, mat)

class W_PT_context_material(properties_material.MaterialButtonsPanel, bpy.types.Panel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}

    REGISTER_PROPERTIES = {
        bpy.types.Material: {
            'w_type': bpy.props.EnumProperty(
                name='Material Type',
                description='Material Type',
                items=[
                    ('forward', 'Forward', ''),
                    ('lambert', 'Lambert', ''),
                    ('mirror', 'Mirror', ''),
                    ('null', 'Null', ''),
                ] + [(c.w_type, c.bl_label, '') for c in MaterialExtra.__subclasses__()],
                default='lambert',
            ),

            'w_albedo': ColorTextureProperty(
                name='Albedo',
                description='Albedo',
                default=(0.8, 0.8, 0.8),
            ),

            'w_emission': ColorTextureProperty(
                name='Emission',
                description='Emission',
                default=(0.0, 0.0, 0.0),
            ),

            'w_bump': TextureProperty(
                name='Bump',
                description='Bump',
            ),

            'w_bump_strength': bpy.props.FloatProperty(
                name='Bump Strength',
                description='Bump Strength',
                min=0.0,
                soft_max=10.0,
                default=1.0,
            ),
        },
    }

    @classmethod
    def to_scene_data(self, scene, m):
        mat = {
            'type': m.w_type,
            'name': m.name,
            'albedo': m.w_albedo.to_scene_data(scene, m),
        }
        obj = {
            'bsdf': m.name,
        }

        emission = m.w_emission.to_scene_data(scene, m)
        if emission != [0.0, 0.0, 0.0]:
            obj['emission'] = emission

        t = m.w_bump.to_scene_data(scene, m)
        if t:
            obj['bump_strength'] = m.w_bump_strength
            obj['bump'] = t

        for c in MaterialExtra.__subclasses__():
            if c.w_type == m.w_type:
                mat.update(c.to_scene_data(scene, m))
        
        return (obj, mat)

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        lay = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        if ob:
            row = lay.row()
            if bpy.app.version < (2, 65, 3):
                row.template_list(ob, 'material_slots', ob, 'active_material_index', rows=2)
            else:
                row.template_list('MATERIAL_UL_matslots', '', ob, 'material_slots', ob, 'active_material_index', rows=2)

            col = row.column(align=True)
            col.operator('object.material_slot_add', icon='ZOOMIN', text='')
            col.operator('object.material_slot_remove', icon='ZOOMOUT', text='')

            if ob.mode == 'EDIT':
                row = lay.row(align=True)
                row.operator('object.material_slot_assign', text='Assign')
                row.operator('object.material_slot_select', text='Select')
                row.operator('object.material_slot_deselect', text='Deselect')

        split = lay.split(percentage=0.75)

        if ob:
            split.template_ID(ob, 'active_material', new='material.new')
            row = split.row()
            if slot:
                row.prop(slot, 'link', text='')
            else:
                row.label()
        elif mat:
            split.template_ID(space, 'pin_id')
            split.separator()

        if mat:
            lay.separator()
            lay.prop(mat, 'w_type', text='Type')
            mat.w_albedo.draw(lay, mat)
            mat.w_emission.draw(lay, mat)

            row = lay.row(align=True)
            row.prop(mat, 'w_bump_strength', text='Bump')
            mat.w_bump.draw(row, mat, text='')

PANEL_CLASSES = {
    'material': W_PT_context_material,
}

PANEL_CLASSES.update({c.w_type: c for c in MaterialExtra.__subclasses__()})

