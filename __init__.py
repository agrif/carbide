import bpy

bl_info = {
    "name": "Tungsten",
    "author": "Aaron Griffith <aargri@gmail.com>",
    "description": "Tungsten renderer integration",
    "category": "Render",
    "blender": (2, 6, 7),
    "location": "Info Header (engine dropdown)",
}

MODULES = [
    'base',
    'props',
    
    'tungsten',
    'preferences',
    'scene',
    'engine',
    
    'render',
    'texture',
    'material',
    'camera',
    'world'
]

import importlib, imp
for mod in MODULES:
    if mod in locals():
        imp.reload(locals()[mod])
    else:
        locals()[mod] = importlib.import_module('.' + mod, __package__)

from bl_ui import properties_scene
base.compatify_all(properties_scene, 'SCENE_PT')

def register():
    base.register()

def unregister():
    base.unregister()

if __name__ == "__main__":
    register()