"""Uma mão humana articulada para o plano da vila.

Malha de base CC0, Posable anatomical right hand, Innerscene (MakeHuman/MPFB).
https://www.innerscene.com/tools/library/3d-parts/posable-anatomical-right-hand-f6098b4f
A malha acompanha a skill em assets/mao-anatomica-cc0.glb. O antebraço, as
unhas adaptadas, a pele procedural e os gestos são construídos localmente.
"""

from math import atan2, cos, radians, sin
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


FINGERS = ("index", "middle", "ring", "pinky", "thumb")
FLEXION = {
    "index": (20, 28, 12),
    "middle": (26, 35, 17),
    "ring": (33, 41, 20),
    "pinky": (37, 46, 24),
    "thumb": (11, 14, 17),
}


def _skin():
    mat = bpy.data.materials.new("Mão • pele ao sol")
    mat.diffuse_color = (0.58, 0.30, 0.19, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    link = mat.node_tree.links.new
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.44
    shader.inputs["Subsurface Weight"].default_value = 0.085
    shader.inputs["Subsurface Radius"].default_value = (1.0, 0.47, 0.26)
    shader.inputs["Subsurface Scale"].default_value = 0.033
    tex = nodes.new("ShaderNodeTexCoord")
    macro = nodes.new("ShaderNodeTexNoise")
    macro.inputs["Scale"].default_value = 6.5
    macro.inputs["Detail"].default_value = 3.0
    link(tex.outputs["Generated"], macro.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.39, 0.157, 0.082, 1)
    ramp.color_ramp.elements[1].color = (0.69, 0.387, 0.247, 1)
    link(macro.outputs["Fac"], ramp.inputs["Fac"])
    link(ramp.outputs["Color"], shader.inputs["Base Color"])
    pores = nodes.new("ShaderNodeTexNoise")
    pores.inputs["Scale"].default_value = 235
    pores.inputs["Detail"].default_value = 1.4
    link(tex.outputs["Generated"], pores.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.002
    bump.inputs["Strength"].default_value = 0.13
    link(pores.outputs["Fac"], bump.inputs["Height"])
    link(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def _nails(mesh, arm):
    """Pequenas lâminas adaptadas ao relevo da falange distal por projeção."""
    A = mesh.matrix_world.copy()
    inv = A.inverted()
    coords = [A @ v.co for v in mesh.data.vertices]
    tree = BVHTree.FromPolygons(coords, [p.vertices[:] for p in mesh.data.polygons])
    arm_world = arm.matrix_world.copy()
    nail = bpy.data.materials.new("Mão • leito ungueal")
    nail.diffuse_color = (0.66, 0.36, 0.28, 1)
    nail.use_nodes = True
    shader = nail.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = nail.diffuse_color
    shader.inputs["Roughness"].default_value = 0.34
    shader.inputs["Coat Weight"].default_value = 0.12
    edge = nail.copy()
    edge.name = "Mão • borda livre das unhas"
    edge.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.72, 0.49, 0.36, 1)
    for finger in FINGERS:
        name = finger + "_03_r"
        distal = arm_world @ arm.data.bones[name].head_local
        previous = arm_world @ arm.data.bones[finger + "_02_r"].head_local
        axis = (distal - previous).normalized()
        hint = Vector((0.86, -0.23, 0.46)) if finger == "thumb" else Vector((0, 0, 1))
        up = (hint - axis * hint.dot(axis)).normalized()
        side = axis.cross(up).normalized()
        group = mesh.vertex_groups[name].index
        vs = [
            coords[v.index]
            for v in mesh.data.vertices
            if any(w.group == group and w.weight > 0.75 for w in v.groups)
        ]
        length = max((v - distal).dot(axis) for v in vs)
        sections = [((q - distal).dot(axis), (q - distal).dot(side), (q - distal).dot(up)) for q in vs]
        verts, faces = [], []
        # Levemente quadrada perto da borda livre, arredondada junto à cutícula.
        for row, width in enumerate((0.45, 0.83, 1, 1, 0.97, 0.87, 0.46)):
            along = (0.25 + row / 6 * 0.58) * length
            nearby = sorted(sections, key=lambda q: abs(q[0] - along))[:32]
            lo, hi = min(q[1] for q in nearby), max(q[1] for q in nearby)
            side_mid = 0.5 * (lo + hi)
            half_width = (hi - lo) * 0.30
            for col in range(7):
                q = (col - 3) / 3
                point = distal + axis * along + side * (side_mid + half_width * width * q) + up * 0.028
                hit, normal, _, _ = tree.ray_cast(point, -up, 0.065)
                if hit is None:
                    break
                verts.append(inv @ (hit + normal * 0.00017))
            if len(verts) != 7 * (row + 1):
                break
        if len(verts) != 49:
            continue
        for i in range(6):
            for j in range(6):
                k = 7 * i + j
                faces.append((k, k + 7, k + 8, k + 1))
        data = bpy.data.meshes.new("Lâmina " + finger)
        data.from_pydata(verts, [], faces)
        data.materials.append(nail)
        data.materials.append(edge)
        for poly in data.polygons:
            poly.use_smooth = True
            if poly.index >= 30:
                poly.material_index = 1
        obj = bpy.data.objects.new("Unha • " + finger, data)
        bpy.context.collection.objects.link(obj)
        obj.parent = arm
        obj.matrix_world = A
        weights = obj.vertex_groups.new(name=name)
        weights.add(list(range(len(verts))), 1, "REPLACE")
        modifier = obj.modifiers.new("Falange distal", "ARMATURE")
        modifier.object = arm


def _forearm(mesh):
    """Prolongar a própria borda do punho, mantendo pele e normais contínuas."""
    A = mesh.matrix_world.copy()
    inv = A.inverted()
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000008)
    cut_y = 0.042
    forward = Vector((0, 1, 0))
    bmesh.ops.bisect_plane(
        bm,
        geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
        dist=0.000001,
        plane_co=inv @ Vector((0, cut_y, 0)),
        plane_no=(A.to_3x3().transposed() @ forward).normalized(),
        clear_inner=True,
    )
    edges = [
        ed
        for ed in bm.edges
        if ed.is_boundary and all(abs((A @ v.co).y - cut_y) < 0.000025 for v in ed.verts)
    ]
    adjacent = {}
    for ed in edges:
        a, b = ed.verts
        adjacent.setdefault(a, []).append(b)
        adjacent.setdefault(b, []).append(a)
    if len(adjacent) < 12 or any(len(j) != 2 for j in adjacent.values()):
        bm.free()
        raise ValueError("Não foi possível reconstruir a borda anatômica do punho.")
    first = next(iter(adjacent))
    ring = [first, adjacent[first][0]]
    while len(ring) < len(adjacent):
        prev, current = ring[-2:]
        nxt = next(v for v in adjacent[current] if v != prev)
        if nxt == first:
            break
        ring.append(nxt)
    vectors = [A @ v.co for v in ring]
    center = sum(vectors, Vector()) / len(vectors)
    deform = bm.verts.layers.deform.verify()
    group = mesh.vertex_groups["hand_r"].index
    radius_x = (max(v.x for v in vectors) - min(v.x for v in vectors)) * 0.5
    radius_z = (max(v.z for v in vectors) - min(v.z for v in vectors)) * 0.5
    prev_ring = ring
    # A seção oval gira e ganha massa progressivamente em direção ao antebraço.
    for extension, width, thickness, drift in (
        (0.009, 0.99, 1.015, 0.002),
        (0.020, 0.99, 1.07, 0.006),
        (0.038, 1.04, 1.16, 0.013),
        (0.070, 1.16, 1.30, 0.024),
        (0.118, 1.31, 1.49, 0.040),
        (0.175, 1.40, 1.62, 0.058),
        (0.240, 1.35, 1.60, 0.076),
    ):
        next_ring = []
        for original in vectors:
            q = original - center
            angle = atan2(q.z / radius_z, q.x / radius_x)
            # As saliências ósseas do punho cedem ao volume elíptico muscular.
            blend = min(1.0, extension / 0.055)
            x = q.x * (1.0 - blend) + radius_x * cos(angle) * blend
            z = q.z * (1.0 - blend) + radius_z * sin(angle) * blend
            co = center + Vector((x * width - drift, -extension, z * thickness + extension * 0.10))
            v = bm.verts.new(inv @ co)
            v[deform][group] = 1.0
            next_ring.append(v)
        for i in range(len(ring)):
            j = (i + 1) % len(ring)
            face = bm.faces.new((prev_ring[i], prev_ring[j], next_ring[j], next_ring[i]))
            face.smooth = True
        prev_ring = next_ring
    bm.faces.new(prev_ring)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()
    for p in mesh.data.polygons:
        p.use_smooth = True
    if mesh.data.has_custom_normals:
        mesh.data.normals_split_custom_set([(0.0, 0.0, 0.0)] * len(mesh.data.loops))
    return center


def build_hand():
    """Devolver root (origem = punho) e armature. Dedos abertos apontam para -Z."""
    path = Path(__file__).resolve().parents[1] / "assets" / "mao-anatomica-cc0.glb"
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), import_pack_images=True)
    imported = set(bpy.context.scene.objects) - before
    arm = next(o for o in imported if o.type == "ARMATURE")
    mesh = next(o for o in imported if o.type == "MESH" and o.parent == arm)
    # O importador cria ainda uma esfera auxiliar de visualização de ossos.
    for marker in imported:
        if marker.type == "MESH" and marker != mesh and not marker.parent:
            marker.hide_render = True
            marker.hide_set(True)
    original_matrix = arm.matrix_world.copy()
    _nails(mesh, arm)
    wrist = _forearm(mesh)
    mesh.data.materials.clear()
    mesh.data.materials.append(_skin())
    mesh.name = "Mão e antebraço • pele contínua"
    arm.name = "Mão • esqueleto de 16 ossos"
    arm.hide_render = True
    root = bpy.data.objects.new("Mão gigante • pulso", None)
    bpy.context.collection.objects.link(root)
    root.empty_display_type = "CIRCLE"
    root.empty_display_size = 0.45
    # Eixos da malha em repouso: +Y segue para as pontas, +Z sai do dorso.
    basis = Matrix(((-1, 0, 0, 0), (0, 0, -1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
    local = Matrix.Scale(23.8, 4) @ basis @ Matrix.Translation(-wrist)
    arm.parent = root
    arm.matrix_world = local @ original_matrix
    pose = {"root": root, "armature": arm, "mesh": mesh}
    pose_hand(pose, 0.0, None)
    return pose


def pose_hand(rig, fechamento, frame=None):
    """Flexionar as falanges em uma pinça relaxada. Valor normalizado de zero a um."""
    t = max(0.0, min(1.0, float(fechamento)))
    arm = rig["armature"]
    for finger in FINGERS:
        for index, bend in enumerate(FLEXION[finger], start=1):
            pb = arm.pose.bones[f"{finger}_{index:02d}_r"]
            pb.rotation_mode = "XYZ"
            spread = 0.0
            if index == 1:
                spread = {"index": -1, "middle": 1, "ring": 4, "pinky": 7, "thumb": 20}[finger] * t
            # O braço do modelo tem uma reflexão nos eixos de repouso. Uma
            # rotação negativa em Z flete as falanges na direção da palma.
            flex = 0.27 + 0.48 * t
            pb.rotation_euler = (radians(spread * 0.20), 0, radians(-bend * flex))
            if frame is not None:
                pb.keyframe_insert(data_path="rotation_euler", frame=frame, group="Pinça • " + finger)
