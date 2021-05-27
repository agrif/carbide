# some reload machinery -- make sure to unload submodules
# so that importlib.reload(carbide) reloads *everything*
# this is entirely so that we can reload the plugin in blender during dev

import sys

for m in [m for m in sys.modules.keys() if m.startswith('carbide.')]:
    del sys.modules[m]

from carbide.blender import register, unregister
from carbide.tungsten import *

import carbide.mesh
import carbide.scene
