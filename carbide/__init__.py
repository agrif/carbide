# first, unload anything of ours that's loaded
# this makes "Reload Scripts" work in blender

import sys

# unload any submodules of our package
for m in list(sys.modules):
    if m.startswith(__package__ + '.'):
        del sys.modules[m]

# if we are running in blender, import blender stuff
try:
    import bpy
except ImportError:
    pass
else:
    from carbide.blender.register import register, unregister

# blender scans __init__.py for this without running, so this has to be here
bl_info = {
    'name': 'Carbide',
    'author': 'Aaron Griffith <aargri@gmail.com>',
    'description': 'Tungsten renderer integration',
    'category': 'Render',
    'blender': (2, 80, 0),
    'location': 'Properties Panel, Render Tab, Engine Dropdown',
}

# ok, now we can import things like normal

from carbide.tungsten import *

import carbide.mesh
import carbide.scene
