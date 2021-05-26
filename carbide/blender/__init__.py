import collections
import importlib
import sys

# the top-level package name, used for module manipulation
PACKAGE_NAME = 'carbide'

# modules (relative to here!) to load
MODULES = [
    'test'
]

# the rest of this file is a set of mechanisms to ensure that reloading
# this addon actually reloads all of the code, to help development.
# However, there is a lot of module and import mucking about.
#
# HERE BE DRAGONS

# list of (name, register, deregister) tuples
REGISTER_HOOKS = collections.deque()
UNREGISTER_HOOKS = collections.deque()

def register():
    while REGISTER_HOOKS:
        n, r, u = REGISTER_HOOKS[0]
        print('registering', n)
        r()

        REGISTER_HOOKS.popleft()
        UNREGISTER_HOOKS.append((n, r, u))

def unregister():
    while UNREGISTER_HOOKS:
        n, r, u = UNREGISTER_HOOKS[-1]
        print('unregistering', n)
        try:
            u()
        except Exception:
            pass

        UNREGISTER_HOOKS.pop()
        REGISTER_HOOKS.appendleft((n, r, u))

    # unload any submodules of our package
    # this catches any recursive imports that do not use us to do the importing
    for m in list(sys.modules):
        if m.startswith(PACKAGE_NAME + '.'):
            del sys.modules[m]

def register_module(name):
    def import_module():
        importlib.import_module(name)
    def delete_module():
        if name in sys.modules:
            del sys.modules[name]
    REGISTER_HOOKS.append((name, import_module, delete_module))

def register_test(name):
    REGISTER_HOOKS.append((name, lambda: None, lambda: None))

for name in MODULES:
    register_module(PACKAGE_NAME + '.blender.' + name)
