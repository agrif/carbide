import bpy
from mathutils import Matrix
from bl_ui import properties_data_lamp

from . import base

base.compatify_class(properties_data_lamp.DATA_PT_context_lamp)
base.compatify_class(properties_data_lamp.DATA_PT_custom_props_lamp)

@base.register_root_panel
class W_PT_lamp(properties_data_lamp.DataButtonsPanel, base.RootPanel):
    bl_label = "Tungsten Lamp"
    prop_class = bpy.types.Lamp

    @classmethod
    def get_object(cls, context):
        return context.lamp

    @classmethod
    def get_object_type(cls, obj):
        return obj.type

    PROPERTIES = {
        'emission': bpy.props.FloatVectorProperty(
            name='Emission',
            description='Emission',
            subtype='COLOR',
            min=0.0,
            soft_max=1.0,
            default=(10, 10, 10),
        ),

        # used in a few specialties
        'radius': bpy.props.FloatProperty(
            name='Radius',
            description='Radius',
            min=0,
            default=1,
            subtype='DISTANCE',
            unit='LENGTH',
        ),
    }

    @classmethod
    def to_scene_data(self, scene, lamp):
        w = lamp.tungsten
        d = {
            'bsdf': {'type': 'null'},
            'emission': list(w.emission),
        }
        d.update(super().to_scene_data(scene, lamp))
        return d

    def draw_for_object(self, lamp):
        layout = self.layout
        w = lamp.tungsten

        layout.prop(lamp, 'type')
        layout.prop(w, 'emission')

@base.register_sub_panel
class W_PT_lamp_point(W_PT_lamp.SubPanel):
    bl_label = "Point"
    w_type = 'POINT'

    @classmethod
    def to_scene_data(self, scene, lamp):
        w = lamp.tungsten
        return {
            'type': 'sphere',
            'transform': Matrix.Scale(w.radius, 4),
        }

    def draw_for_object(self, lamp):
        layout = self.layout
        w = lamp.tungsten

        layout.prop(w, 'radius')
