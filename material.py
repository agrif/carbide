import bpy
import nodeitems_utils
from bl_ui import properties_material
from . import base

@base.register_class
class W_OT_use_material_nodes(bpy.types.Operator):
    """Enable nodes on a material"""
    bl_label = "Use Nodes"
    bl_idname = 'tungsten.use_material_nodes'

    @classmethod
    def poll(cls, context):
        return getattr(context, 'material', False)

    def execute(self, context):
        mat = context.material
        w = mat.tungsten
        
        if w.nodetree:
            return {'FINISHED'}
        
        nt = bpy.data.node_groups.new(mat.name, type='TungstenShaderTree')
        nt.use_fake_user = True
        w.nodetree = nt.name
        nt.nodes.new('TungstenOutputNode')
        
        return {'FINISHED'}

@base.register_class
class TungstenShaderTree(bpy.types.NodeTree):
    bl_idname = 'TungstenShaderTree'
    bl_label = 'Tungsten Shader Tree'
    bl_icon = 'TEXTURE_SHADED'

    node_categories = {}

    @classmethod
    def register_node(cls, category):
        def registrar(nodecls):
            base.register_class(nodecls)
            d = cls.node_categories.setdefault(category, [])
            d.append(nodecls)
            return nodecls
        return registrar

    @classmethod
    def register(cls):
        cats = []
        for c, l in cls.node_categories.items():
            cid = c.replace(' ', '').upper()
            items = [nodeitems_utils.NodeItem(nc.__name__) for nc in l]
            cats.append(TungstenNodeCategory(cid, c, items=items))

        nodeitems_utils.register_node_categories('TUNGSTEN_SHADER', cats)

    @classmethod
    def unregister(cls):
        nodeitems_utils.unregister_node_categories('TUNGSTEN_SHADER')

    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == 'TUNGSTEN'

    @classmethod
    def get_from_context(cls, context):
        ob = context.active_object
        if ob and ob.type not in {'LAMP', 'CAMERA'}:
            ma = ob.active_material
            if ma:
                ntname = ma.tungsten.nodetree
                if ntname:
                    return bpy.data.node_groups[ma.tungsten.nodetree], ma, ma
        return (None, None, None)

    @property
    def output(self):
        for n in self.nodes:
            if isinstance(n, TungstenOutputNode):
                return n
        return None

class TungstenNodeCategory(nodeitems_utils.NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'TungstenShaderTree'

class TungstenShaderNode(bpy.types.Node):
    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'TungstenShaderTree'

@base.register_class
class TungstenShaderSocket(bpy.types.NodeSocket):
    bl_idname = 'TungstenShaderSocket'
    bl_label = 'Tungsten Shader Socket'

    default_value = bpy.props.FloatVectorProperty(
        name='Albedo',
        description='Albedo',
        subtype='COLOR',
        min=0.0,
        max=1.0,
        default=(0.8, 0.8, 0.8),
    )

    def to_scene_data(self, scene):
        if not self.is_linked:
            return {
                'type': 'lambert',
                'albedo': list(self.default_value),
            }
        return self.links[0].from_node.to_scene_data(scene)
    
    def draw_value(self, context, layout, node):
        layout.label(self.name)

    def draw_color(self, context, node):
        return (0.1, 1.0, 0.2, 0.75)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

@base.register_class
class TungstenTextureSocket(bpy.types.NodeSocket):
    bl_idname = 'TungstenTextureSocket'
    bl_label = 'Tungsten Texture Socket'

    default_value = bpy.props.FloatVectorProperty(
        name='Color',
        description='Color',
        subtype='COLOR',
        min=0.0,
        max=1.0,
        default=(0.8, 0.8, 0.8),
    )

    def to_scene_data(self, scene):
        if not self.is_linked:
            return list(self.default_value)
        return self.links[0].from_node.to_scene_data(scene)
    
    def draw_value(self, context, layout, node):
        layout.label(self.name)

    def draw_color(self, context, node):
        return (1.0, 0.1, 0.2, 0.75)

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(self.name)
        else:
            layout.prop(self, 'default_value', text=self.name)

@TungstenShaderTree.register_node('Output')
class TungstenOutputNode(TungstenShaderNode):
    bl_label = 'Output'
    def init(self, context):
        self.inputs.new('TungstenShaderSocket', 'Material')

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
        'nodetree': bpy.props.StringProperty(
            name='Node Tree',
            description='Node Tree',
            default='',
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
        
        if w.nodetree:
            ntree = bpy.data.node_groups[w.nodetree]
            output = ntree.output
            if output:
                mat = output.inputs['Material'].to_scene_data(scene)
                mat['name'] = m.name
                obj['bsdf'] = m.name
            else:
                obj['bsdf'] = scene.default_mat
        else:
            mat = {
                'name': m.name,
                'type': 'lambert',
                'albedo': list(w.albedo),
                'emission': list(w.emission),
            }
            obj['bsdf'] = m.name
            
        if mat.get('emission') == [0.0, 0.0, 0.0]:
            del mat['emission']

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

            if not w.nodetree:
                layout.operator('tungsten.use_material_nodes', icon='NODETREE')
                layout.prop(w, 'albedo')
                layout.prop(w, 'emission')
            else:
                ntree = bpy.data.node_groups[w.nodetree]
                node = ntree.output
                if not node:
                    layout.label(text='No output node')
                else:
                    layout.template_node_view(ntree, node, node.inputs['Material'])

class TungstenBSDFNode(TungstenShaderNode):
    def init(self, context):
        self.outputs.new('TungstenShaderSocket', 'Material')

    def to_scene_data(self, scene):
        return {}

@TungstenShaderTree.register_node('Materials')
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

    def draw_buttons(self, context, layout):
        layout.prop(self, 'albedo')
