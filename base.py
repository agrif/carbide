import bpy
import bpy_types

REGISTRARS = []

def registrar(register, unregister):
    global REGISTRARS
    REGISTRARS.append((register, unregister))

def register():
    for r, _ in REGISTRARS:
        r()

def unregister():
    for _, u in REGISTRARS:
        u()

def register_class(cls):
    registrar(lambda: bpy.utils.register_class(cls), lambda: bpy.utils.unregister_class(cls))
    return cls

def compatify_class(cls):
    def reg():
        if not 'COMPAT_ENGINES' in cls.COMPAT_ENGINES:
            cls.COMPAT_ENGINES = set()
        cls.COMPAT_ENGINES.add('TUNGSTEN')
    def unreg():
        cls.COMPAT_ENGINES.remove('TUNGSTEN')
    registrar(reg, unreg)
    return cls

def compatify_all(mod, start):
    for k, v in vars(mod).items():
        if k.startswith(start):
            compatify_class(v)

class Panel(bpy.types.Panel):
    COMPAT_ENGINES = {'TUNGSTEN'}

class ObjectPanel(Panel):
    @classmethod
    def get_object(self, context):
        return None

    def draw_for_object(self, object):
        pass

    def draw(self, context):
        self.draw_for_object(self.get_object(context))

def register_properties(props, cls):
    for k, v in getattr(cls, 'PROPERTIES', {}).items():
        if 'register_properties' in dir(v):
            v.register_properties(props, k)
        else:
            props[k] = v

def register_root_panel(k):
    class SubPanel(ObjectPanel):
        Parent = k
        w_type = None
        w_types = set()
        
        @classmethod
        def poll_for_object(cls, obj):
            w = getattr(obj, cls.Parent.prop_name)
            if w:
                typ = getattr(w, 'type', None)
                if typ == cls.w_type or typ in cls.w_types:
                    return True
            return False
            
        @classmethod
        def poll(cls, context):
            if not cls.Parent.poll(context):
                return False
            obj = cls.get_object(context)
            if not obj:
                return False
            return cls.poll_for_object(obj)
        
        @classmethod
        def to_scene_data(cls, scene, obj):
            return {}

        @classmethod
        def get_object(cls, context):
            return cls.Parent.get_object(context)
        
    k.SubPanel = SubPanel
    def copy_attr(n):
        if n in dir(k):
            setattr(k.SubPanel, n, getattr(k, n))
    copy_attr('bl_space_type')
    copy_attr('bl_region_type')
    copy_attr('bl_context')

    return register_class(k)

class RootPanel(ObjectPanel):
    prop_class = None
    prop_name = 'tungsten'

    @classmethod
    def get_subpanel_data(cls, scene, obj):
        for k in cls.SubPanel.__subclasses__():
            if k.poll_for_object(obj):
                yield k.to_scene_data(scene, obj)
    
    @classmethod
    def to_scene_data(cls, scene, obj):
        d = {}
        for sd in cls.get_subpanel_data(scene, obj):
            d.update(sd)
        return d

    @classmethod
    def register(cls):
        props = {}
        register_properties(props, cls)
        for k in cls.SubPanel.__subclasses__():
            register_properties(props, k)

        cls.PropertyGroup = type('PropertyGroup', (bpy.types.PropertyGroup,), props)
        bpy.utils.register_class(cls.PropertyGroup)
        setattr(cls.prop_class, cls.prop_name, bpy.props.PointerProperty(type=cls.PropertyGroup))

    @classmethod
    def unregister(cls):
        delattr(cls.prop_class, cls.prop_name)
        bpy.utils.unregister_class(cls.PropertyGroup)
        delattr(cls, 'PropertyGroup')