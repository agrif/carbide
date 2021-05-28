import collections

import bpy

# set to True to get registration traces printed to stdout
VERBOSE = False

# list of (name, register, deregister) tuples
REGISTER_HOOKS = collections.deque()
UNREGISTER_HOOKS = collections.deque()


def register():
    while REGISTER_HOOKS:
        n, r, u = REGISTER_HOOKS[0]
        if VERBOSE:
            print('{}: registering {}'.format(__package__, n))
        r()

        REGISTER_HOOKS.popleft()
        UNREGISTER_HOOKS.append((n, r, u))


def unregister():
    while UNREGISTER_HOOKS:
        n, r, u = UNREGISTER_HOOKS[-1]
        if VERBOSE:
            print('{}: unregistering {}'.format(__package__, n))
        try:
            u()
        except Exception:
            pass

        UNREGISTER_HOOKS.pop()
        REGISTER_HOOKS.appendleft((n, r, u))


def add_registration(name, register, unregister):
    REGISTER_HOOKS.append((name, register, unregister))


def add_class(cls):
    add_registration(cls.__qualname__,
                     lambda: bpy.utils.register_class(cls),
                     lambda: bpy.utils.unregister_class(cls))
