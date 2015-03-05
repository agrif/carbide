import bpy
import tempfile
import shutil
import os.path
import json
import struct
from mathutils import Vector, Matrix

from .render import W_PT_renderer, W_PT_integrator
from .camera import W_PT_camera
from .world import W_PT_world

class TungstenScene:
    def __init__(self, clean_on_del=True, self_contained=False):
        self.dir = tempfile.mkdtemp(suffix='w')
        self.clean_on_del = clean_on_del
        self.self_contained = self_contained
        self.scene = {
            'media': [],
            'bsdfs': [
            ],
            'primitives': [],
            'camera': {},
            'integrator': {
            },
            'renderer': {
                'output_file': 'scene.png',
                'overwrite_output_files': True,
                'enable_resume_render': False,
                'checkpoint_interval': 0,
            },
        }
        self.mats = {}
        self.images = {}
        self.scenefile = self.path('scene.json')

        self.default_mat = '__default_mat'
        self.scene['bsdfs'].append({
            'name': self.default_mat,
            'type': 'lambert',
            'albedo': 0.8,
        })

    def __del__(self):
        if self.clean_on_del:
            shutil.rmtree(self.dir)

    @property
    def outputfile(self):
        return self.path(self.scene['renderer']['output_file'])

    @property
    def width(self):
        return self.scene['camera']['resolution'][0]

    @property
    def height(self):
        return self.scene['camera']['resolution'][1]

    def path(self, *args):
        return os.path.join(self.dir, *args)

    def save(self):
        with open(self.scenefile, 'w') as f:
            json.dump(self.scene, f, indent=4)

    def add_all(self, scene):
        d = W_PT_renderer.to_scene_data(self, scene)
        self.scene['renderer'].update(d)

        d = W_PT_integrator.to_scene_data(self, scene)
        self.scene['integrator'].update(d)

        self.add_world(scene.world)
        self.add_camera(scene, scene.camera)
        for o in scene.objects.values():
            self.add_object(scene, o)

    def add_world(self, world):
        p = W_PT_world.to_scene_data(self, world)
        self.scene['primitives'].append(p)

    def add_camera(self, scene, camera):
        # look_at and friends are right-handed, but tungsten at
        # large is left-handed, for... reasons...
        transform = camera.matrix_world * Matrix.Scale(-1, 4, Vector((0, 0, 1))) * Matrix.Scale(-1, 4, Vector((1, 0, 0)))

        scale = scene.render.resolution_percentage / 100
        # FIXME scene.render.pixel_aspect_x/y ?
        # FIXME border / crop
        width = int(scene.render.resolution_x * scale)
        height = int(scene.render.resolution_y * scale)

        self.scene['camera'] = {
            'transform': [],
            'resolution': [width, height],
        }

        for v in transform:
            self.scene['camera']['transform'] += list(v)

        d = W_PT_camera.to_scene_data(self, camera.data)
        self.scene['camera'].update(d)

    def _save_image_as(self, im, dest, fmt):
        # FIXME ewww
        if im.source == 'FILE' and im.file_format == fmt:
            # abuse image properties for saving
            oldfp = im.filepath_raw
            try:
                im.filepath_raw = dest
                im.save()
            finally:
                im.filepath_raw = oldfp
        else:
            # abuse render settings for conversion
            s = bpy.context.scene
            oldff = s.render.image_settings.file_format
            try:
                s.render.image_settings.file_format = fmt
                im.save_render(dest, s)
            finally:
                s.render.image_settings.file_format = oldff

    def add_image(self, im):
        if im.name in self.images:
            return self.images[im.name]

        IMAGE_FORMATS = {
            'BMP': '.bmp',
            'PNG': '.png',
            'JPEG': '.jpg',
            'TARGA': '.tga',
            'TARGA_RAW': '.tga',
            'HDR': '.hdr',
        }

        if im.file_format in IMAGE_FORMATS:
            ext = IMAGE_FORMATS[im.file_format]
            
            # use native format
            path = bpy.path.abspath(im.filepath)
            if im.library:
                path = bpy.path.abspath(im.filepath, library=im.library)
            
            if path and os.path.exists(path) and not self.self_contained:
                # use existing file
                self.images[im.name] = path
                return path
            else:
                # save file
                path = self.path(im.name + ext)
                self._save_image_as(im, path, im.file_format)
                self.images[im.name] = path
                return path
        else:
            # save as png
            path = self.path(im.name + '.png')
            self._save_image_as(im, path, 'PNG')
            self.images[im.name] = path
            return path

    def add_material(self, m):
        if m.name in self.mats:
            return self.mats[m.name]

        # FIXME material
        #obj, mat = PANEL_CLASSES['material'].to_scene_data(self, m)
        #self.scene['bsdfs'].append(mat)
        #self.mats[m.name] = obj
        return {'bsdf': self.default_mat}
        #return obj

    def add_mesh(self, m, name=None):
        if name is None:
            name = m.name
        
        # FIXME will break if using linked, deformed meshes...
        outname = name + '.wo3'

        num_vertices = 0
        vertices = b''
        num_triangles = 0
        triangles = b''

        # FIXME don't dupe verts
        def emit_vertex(v, uv, normal=None):
            nonlocal vertices, num_vertices
            x, y, z = v.co
            nx, ny, nz = v.normal
            if normal:
                nx, ny, nz = normal
            u, v = uv

            vertices += struct.pack('=ffffffff', x, y, z, nx, ny, nz, u, v)
            num_vertices += 1
            return num_vertices - 1
        def emit_triangle(i0, i1, i2, u0, u1, u2, mat, normal=None):
            nonlocal triangles, num_triangles
            i0 = emit_vertex(m.vertices[i0], u0, normal=normal)
            i1 = emit_vertex(m.vertices[i1], u1, normal=normal)
            i2 = emit_vertex(m.vertices[i2], u2, normal=normal)
            
            triangles += struct.pack('=IIIi', i0, i1, i2, mat)
            num_triangles += 1

        uvdata = None
        if len(m.tessface_uv_textures) >= 1:
            uvdata = m.tessface_uv_textures[0].data # FIXME many uv maps
        
        for n, f in enumerate(m.tessfaces):
            uv = [(0.0, 0.0)] * 4
            if uvdata:
                uv = uvdata[n]
                uv = [uv.uv1, uv.uv2, uv.uv3, uv.uv4]

            normal = None
            if not f.use_smooth:
                normal = f.normal
            
            i = f.vertices
            if len(i) == 3:
                emit_triangle(i[0], i[1], i[2], uv[0], uv[1], uv[2], f.material_index, normal=normal)
            else:
                i1 = i[0]
                u1 = uv[0]
                a = i[1:]
                ua = uv[1:]
                b = i[2:]
                ub = uv[2:]
                for (i2, i3, u2, u3) in zip(a, b, ua, ub):
                    emit_triangle(i1, i2, i3, u1, u2, u3, f.material_index, normal=normal)

        with open(self.path(outname), 'wb') as f:
            f.write(struct.pack('Q', num_vertices))
            f.write(vertices)
            f.write(struct.pack('Q', num_triangles))
            f.write(triangles)
        
        return outname

    def add_object(self, scene, o):
        if o.type != 'MESH':
            return

        dat = {
            'name': o.name,
            'type': 'mesh',
            'smooth': True,
        }

        mesh = o.to_mesh(scene, True, 'RENDER', True)
        dat['file'] = self.add_mesh(mesh, name=o.name)
        bpy.data.meshes.remove(mesh)

        dat['transform'] = []
        for v in o.matrix_world:
            dat['transform'] += list(v)

        if len(o.material_slots) > 0 and o.material_slots[0].material: # FIXME matid
            obj = self.add_material(o.material_slots[0].material)
            dat.update(obj)
        else:
            dat['bsdf'] = self.default_mat

        self.scene['primitives'].append(dat)