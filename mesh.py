import bpy
import os.path
import struct
import time
from bpy_extras.io_utils import ExportHelper

from . import base

LENFMT = struct.Struct('=Q')
VERTFMT = struct.Struct('=ffffffff')
TRIFMT = struct.Struct('=IIIi')

def write_object_mesh(scene, obj, path, apply_modifiers=True, **kwargs):
    if obj.type != 'MESH' or (apply_modifiers and obj.is_modified(scene, 'RENDER')):
        try:
            mesh = obj.to_mesh(scene, True, 'RENDER')
            verts, tris = write_mesh(mesh, path, **kwargs)
        finally:
            bpy.data.meshes.remove(mesh)
    else:
        verts, tris = write_mesh(obj.data, path, **kwargs)
    return (verts, tris)

def write_mesh(mesh, path, use_normals=True):
    mesh.calc_normals()
    if not mesh.tessfaces and mesh.polygons:
        mesh.calc_tessface()

    has_uv = bool(mesh.tessface_uv_textures)

    if has_uv:
        active_uv_layer = mesh.tessface_uv_textures.active
        if not active_uv_layer:
            has_uv = False
        else:
            active_uv_layer = active_uv_layer.data

    verts = mesh.vertices
    wo3_verts = bytearray()
    verti = 0
    wo3_indices = [{} for _ in range(len(verts))]
    wo3_tris = bytearray()
    trii = 0

    uvcoord = (0.0, 0.0)
    for i, f in enumerate(mesh.tessfaces):
        smooth = f.use_smooth
        if use_normals and not smooth:
            normal = f.normal[:]

        if has_uv:
            uv = active_uv_layer[i]
            uv = (uv.uv1, uv.uv2, uv.uv3, uv.uv4)

        oi = []
        for j, vidx in enumerate(f.vertices):
            v = verts[vidx]

            if not use_normals or smooth:
                normal = v.normal[:]

            if has_uv:
                uvcoord = (uv[j][0], uv[j][1])

            key = (normal, uvcoord)
            out_idx = wo3_indices[vidx].get(key)
            if out_idx is None:
                out_idx = verti
                wo3_indices[vidx][key] = out_idx
                wo3_verts += VERTFMT.pack(v.co[0], v.co[1], v.co[2], normal[0], normal[1], normal[2], uvcoord[0], uvcoord[1])
                verti += 1

            oi.append(out_idx)

        matid = f.material_index
        if len(oi) == 3:
            # triangle
            wo3_tris += TRIFMT.pack(oi[0], oi[1], oi[2], matid)
            trii += 1
        else:
            # quad
            wo3_tris += TRIFMT.pack(oi[0], oi[1], oi[2], matid)
            wo3_tris += TRIFMT.pack(oi[0], oi[2], oi[3], matid)
            trii += 2

    with open(path, 'wb') as f:
        f.write(LENFMT.pack(verti))
        f.write(wo3_verts)
        f.write(LENFMT.pack(trii))
        f.write(wo3_tris)

    return (verti, trii)

@base.register_menu_item(bpy.types.INFO_MT_file_export)
class W_OT_wo3_export(bpy.types.Operator, ExportHelper):
    """Export the selected object as a .wo3 mesh."""
    bl_label = "Tungsten Mesh (.wo3)"
    bl_idname = 'tungsten.export_wo3'

    filename_ext = '.wo3'
    filter_glob = bpy.props.StringProperty(default='*.wo3', options={'HIDDEN'})

    apply_modifiers = bpy.props.BoolProperty(
        name='Apply Modifiers',
        description='Apply modifiers to the exported mesh',
        default=True,
    )

    use_normals = bpy.props.BoolProperty(
        name='Use Normals',
        description='Use Smooth and Flat shading (duplicate for flat)',
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        path = self.filepath
        path = bpy.path.ensure_ext(path, self.filename_ext)

        start = time.time()
        scene = context.scene
        obj = context.active_object
        verts, tris = write_object_mesh(scene, obj, path, apply_modifiers=self.apply_modifiers, use_normals=self.use_normals)
        end = time.time()
        print('wrote', os.path.split(path)[1], 'in', end - start, 's -', verts, 'verts,', tris, 'tris')
        return {'FINISHED'}
