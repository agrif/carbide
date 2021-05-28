import bpy

from carbide.blender.register import add_class

@add_class
class TungstenPreferences(bpy.types.AddonPreferences):
    # careful -- this needs to match the root package name
    bl_idname = __package__.split('.')[0]

    tungsten_server_path: bpy.props.StringProperty(
        name="Tungsten Server Path",
        description="Tungsten Server Path",
        subtype='FILE_PATH',
        default='',
    )

    def draw(self, context):
        lay = self.layout

        lay.prop(self, 'tungsten_server_path')

def get():
    return bpy.context.preferences.addons[__package__.split('.')[0]] \
                                  .preferences
