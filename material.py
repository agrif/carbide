import bpy
from bl_ui import properties_material
from . import base
from .node import TungstenNodeTree, TungstenNode, NodeTreeProperty

@base.register_root_panel
class W_PT_material(properties_material.MaterialButtonsPanel, base.RootPanel):
    bl_label = ""
    bl_options = {'HIDE_HEADER'}
    prop_class = bpy.types.Material

    @classmethod
    def get_object(cls, context):
        return context.material
    
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return (context.material or context.object) and (engine in cls.COMPAT_ENGINES)

    PROPERTIES = {
        'material': NodeTreeProperty(
            name='Material',
            description='Material',
        ),
        
        'albedo': bpy.props.FloatVectorProperty(
            name='Albedo',
            description='Albedo',
            subtype='COLOR',
            min=0.0,
            max=1.0,
            default=(0.8, 0.8, 0.8),
        ),

        'emission': bpy.props.FloatVectorProperty(
            name='Emission',
            description='Emission',
            subtype='COLOR',
            min=0.0,
            soft_max=1.0,
            default=(0.0, 0.0, 0.0),
        ),
    }

    @classmethod
    def to_scene_data(self, scene, m):
        w = m.tungsten
        obj = {}
        mat = {}

        ret = w.material.to_scene_data(scene, w)
        if ret:
            obj, mat = ret
        else:
            mat = {
                'type': 'lambert',
                'albedo': list(w.albedo),
                'emission': list(w.emission),
            }
            
        if mat.get('emission') == [0.0, 0.0, 0.0]:
            del mat['emission']

        mat['name'] = m.name
        obj['bsdf'] = m.name

        return obj, mat

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data

        if ob:
            row = layout.row()
            row.template_list('MATERIAL_UL_matslots', '', ob, 'material_slots', ob, 'active_material_index', rows=1)

            col = row.column(align=True)
            col.operator('object.material_slot_add', icon='ZOOMIN', text='')
            col.operator('object.material_slot_remove', icon='ZOOMOUT', text='')
            col.menu('MATERIAL_MT_specials', icon='DOWNARROW_HLT', text='')

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator('object.material_slot_assign', text='Assign')
                row.operator('object.material_slot_select', text='Select')
                row.operator('object.material_slot_deselect', text='Deselect')

        split = layout.split(percentage=0.65)

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
            layout.separator()
            w = mat.tungsten

            if not w.material.draw(layout, w):
                layout.prop(w, 'albedo')
                layout.prop(w, 'emission')

@TungstenNodeTree.register_node('Output')
class TungstenMaterialOutputNode(TungstenNode):
    bl_label = 'Material Output'
    w_output = True

    bump_strength = bpy.props.FloatProperty(
        name='Bump Strength',
        description='Bump Strength',
        min=0.0,
        soft_max=10.0,
        default=1.0,
    )

    def init(self, context):
        self.inputs.new('TungstenShaderSocket', 'Material')
        self.inputs.new('TungstenTextureSocket', 'Emission')
        self.inputs['Emission'].default_value = (0.0, 0.0, 0.0)
        self.inputs.new('TungstenTextureSocket', 'Bump')
        self.inputs['Bump'].show_color = False

    def to_scene_data(self, scene):
        mat = self.inputs['Material'].to_scene_data(scene)
        obj = {
            'emission': self.inputs['Emission'].to_scene_data(scene),
        }

        if self.inputs['Bump'].is_linked:
            obj['bump'] = self.inputs['Bump'].to_scene_data(scene)
            obj['bump_strength'] = self.bump_strength

        return obj, mat

    def draw_buttons(self, context, layout):
        if self.inputs['Bump'].is_linked:
            layout.prop(self, 'bump_strength')

class TungstenBSDFNode(TungstenNode):
    def init(self, context):
        self.outputs.new('TungstenShaderSocket', 'Material')

    def to_scene_data(self, scene):
        return {}

@TungstenNodeTree.register_node('Materials')
class TungstenLambertNode(TungstenBSDFNode):
    bl_label = 'Lambert'

    def init(self, context):
        super().init(context)
        self.inputs.new('TungstenTextureSocket', 'Albedo')

    def to_scene_data(self, scene):
        return {
            'type': 'lambert',
            'albedo': self.inputs['Albedo'].to_scene_data(scene),
        }
