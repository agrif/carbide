import bpy
import struct

LENFMT = struct.Struct('=Q')
VERTFMT = struct.Struct('=ffffffff')
TRIFMT = struct.Struct('=IIIi')

def write_mesh(mesh, path):
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
        if not smooth:
            normal = f.normal[:]

        if has_uv:
            uv = active_uv_layer[i]
            uv = (uv.uv1, uv.uv2, uv.uv3, uv.uv4)

        oi = []
        for j, vidx in enumerate(f.vertices):
            v = verts[vidx]

            if smooth:
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
