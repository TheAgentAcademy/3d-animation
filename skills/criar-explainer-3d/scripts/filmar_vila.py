"""Animar uma vila ao ar livre, com perspectiva, mão articulada e três ondas de ação."""

import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Matrix, Vector

MODULES = Path(__file__).resolve().parent
if str(MODULES) not in sys.path:
    sys.path.insert(0, str(MODULES))

from vila_cenario import build_village
from vila_mao import build_hand, pose_hand

RAD = math.radians


def create_material(name, color, metallic=0, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


def mesh_object(name, vertices, faces, materials, slots=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    if slots is not None:
        for poly, slot in zip(mesh.polygons, slots):
            poly.material_index = slot
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def put_linked(name, mesh, location):
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def put_box(name, position, dimensions, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    ob = bpy.context.object
    ob.name = name
    for vert in ob.data.vertices:
        for axis in range(3):
            vert.co[axis] *= dimensions[axis]
    ob.data.materials.append(mat)
    if bevel:
        mod = ob.modifiers.new("Bordas", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        ob.modifiers.new("Normais", "WEIGHTED_NORMAL")
    return ob


def pipe_between(name, start, end, radius, mat, sides=16):
    a, b = Vector(start), Vector(end)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=sides, radius=radius, depth=(b - a).length, location=(a + b) / 2
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


def number_frame(time, fps):
    return 1 + round(time * fps)


def pose(obj, time, fps, position=None, angles=None, scale=None):
    frame = number_frame(time, fps)
    if position is not None:
        obj.location = position
        obj.keyframe_insert(data_path="location", frame=frame)
    if angles is not None:
        obj.rotation_euler = tuple(RAD(x) for x in angles)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = scale if isinstance(scale, (tuple, list)) else (scale,) * 3
        obj.keyframe_insert(data_path="scale", frame=frame)


def transient(obj, start, end, fps):
    for t, hidden in [(0, True), (start, False), (end, True)]:
        frame = number_frame(t, fps)
        obj.hide_render = hidden
        obj.hide_viewport = hidden
        obj.keyframe_insert(data_path="hide_render", frame=frame)
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)


def daylight(scene):
    def sun(name, direction, color, energy, angle, shadow):
        lamp = bpy.data.lights.new(name, "SUN")
        lamp.color, lamp.energy, lamp.angle = color, energy, RAD(angle)
        lamp.use_shadow = shadow
        obj = bpy.data.objects.new(name, lamp)
        bpy.context.collection.objects.link(obj)
        obj.rotation_euler = Vector(direction).to_track_quat("-Z", "Y").to_euler()

    sun("Sol da manhã / sombra para a direita", (4.7, 3.6, -7.0), (1.0, 0.88, 0.71), 3.3, 2.3, True)
    sun("Céu aberto / luz difusa", (-2.5, 3.3, -5), (0.63, 0.79, 1.0), 0.68, 24, False)
    sun("Luz nas bordas / fundo", (-1.8, -3.1, -3.5), (0.83, 0.90, 1.0), 0.80, 16, False)
    scene.view_settings.view_transform = "Khronos PBR Neutral"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.06


def camera_path(scene, cfg, fps):
    lens = bpy.data.cameras.new("Lente da praça")
    lens.type = "PERSP"
    lens.sensor_fit = "VERTICAL"
    lens.sensor_height = 36
    lens.clip_end = 600
    cam = bpy.data.objects.new("Travelling / rua", lens)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    for point in cfg:
        cam.location = point["eye"]
        cam.rotation_euler = (Vector(point["target"]) - cam.location).to_track_quat("-Z", "Y").to_euler()
        lens.lens = point["mm"]
        frame = number_frame(point["s"], fps)
        cam.keyframe_insert(data_path="location", frame=frame)
        cam.keyframe_insert(data_path="rotation_euler", frame=frame)
        lens.keyframe_insert(data_path="lens", frame=frame)
    return cam


def make_coin():
    bright = create_material("Ouro cunhado", (0.96, 0.575, 0.075), 0.62, 0.27)
    rim = create_material("Aresta polida", (1, 0.78, 0.19), 0.53, 0.23)
    dark = create_material("Sulcos do metal", (0.50, 0.237, 0.026), 0.58, 0.32)
    vertices, faces, slots = [], [], []
    # Perfil torneado com bordo alto e campo central rebaixado, em ambas as faces.
    rings = [
        (0.216, -0.041),
        (0.236, -0.040),
        (0.252, -0.027),
        (0.252, 0.025),
        (0.237, 0.040),
        (0.218, 0.041),
        (0.204, 0.025),
    ]
    sides = 32
    for rad, z in rings:
        vertices.extend(
            (rad * math.cos(i * math.tau / sides), rad * math.sin(i * math.tau / sides), z)
            for i in range(sides)
        )
    faces.append(tuple(reversed(range(sides))))
    slots.append(0)
    for j in range(len(rings) - 1):
        for k in range(sides):
            a = j * sides + k
            b = j * sides + (k + 1) % sides
            faces.append((a, b, b + sides, a + sides))
            slots.append((1, 0, 2 if k % 2 else 1, 0, 1, 1)[j])
    faces.append(tuple(range((len(rings) - 1) * sides, len(rings) * sides)))
    slots.append(0)
    # Estrela de oito pontas, estampada no topo da moeda.
    base = len(vertices)
    vertices.append((0, 0, 0.053))
    for k in range(16):
        a = k * math.tau / 16
        rad = (0.151 if k % 4 == 0 else 0.114) if k % 2 == 0 else 0.062
        vertices.append((rad * math.cos(a), rad * math.sin(a), 0.035))
    for k in range(16):
        faces.append((base, base + 1 + k, base + 1 + (k + 1) % 16))
        slots.append(1)
    return mesh_object("Moeda / matriz", vertices, faces, [bright, rim, dark], slots)


def spiral_coins(t0, fps, rng):
    source = make_coin()
    mesh = source.data
    center = Vector((0.68, -2.28, 0.08))
    stacks = [
        (-0.45, -0.30, 7),
        (-0.08, -0.44, 5),
        (0.40, -0.25, 7),
        (0.59, 0.12, 5),
        (0.16, 0.20, 9),
        (-0.32, 0.17, 6),
        (-0.69, 0.12, 3),
    ]
    count = 0
    for dx, dy, height in stacks:
        for j in range(height):
            start = center + Vector(
                (dx + rng.uniform(-0.014, 0.014), dy + rng.uniform(-0.014, 0.014), j * 0.078)
            )
            ob = source if count == 0 else put_linked("Moeda %02d" % count, mesh, start)
            a = rng.uniform(-180, 180)
            t = t0 + (height - 1 - j) * 0.046 + rng.uniform(0, 0.12)
            spiral = rng.uniform(0, math.tau)
            mag = rng.uniform(0.50, 1.17)
            pose(ob, 0, fps, start, (0, 0, a), 1)
            pose(ob, t, fps, start, (0, 0, a), 1)
            pose(
                ob,
                t + 0.22,
                fps,
                (start.x + math.cos(spiral) * mag, start.y + math.sin(spiral) * 0.38, start.z + 0.46),
                (48, -20, a + 30),
                1,
            )
            pose(
                ob,
                t + 0.51,
                fps,
                (
                    0.48 + math.cos(spiral + 1.4) * mag,
                    -1.65 + math.sin(spiral + 1.4) * 0.38,
                    2.32 + rng.random() * 0.4,
                ),
                (155, 64, a + 125),
                0.92,
            )
            pose(
                ob,
                t + 0.91,
                fps,
                (0.55 + rng.uniform(-0.23, 0.23), -0.72, 5.38 + rng.uniform(-0.1, 0.17)),
                (245, 88, a + 280),
                0.045,
            )
            for key, hidden in [(0, False), (t + 0.91, True)]:
                frame = number_frame(key, fps)
                ob.hide_render = hidden
                ob.hide_viewport = hidden
                ob.keyframe_insert(data_path="hide_render", frame=frame)
                ob.keyframe_insert(data_path="hide_viewport", frame=frame)
            count += 1


def sign_and_pipes(label, reveal, fps):
    iron = create_material("Ferro esmaltado", (0.021, 0.086, 0.107), 0.46, 0.42)
    cream = create_material("Esmalte marfim", (0.85, 0.78, 0.57), 0.12, 0.43)
    turquoise = create_material("Esmalte azul-petróleo", (0.018, 0.20, 0.23), 0.28, 0.36)
    clay = create_material("Cerâmica ocre", (0.29, 0.109, 0.044), 0.22, 0.68)
    oxide = create_material("Anel da tubulação", (0.12, 0.18, 0.17), 0.48, 0.56)
    x, y = 1.20, -1.71
    pipe_between("Poste da rua", (x, y, 0.04), (x, y, 1.94), 0.047, iron)
    put_box("Placa / moldura", (x, y, 1.80), (0.98, 0.085, 0.32), cream, 0.04)
    put_box("Placa / esmalte", (x, y - 0.046, 1.80), (0.924, 0.025, 0.265), turquoise, 0.024)
    for dx in [-0.38, 0.38]:
        for dz in [-0.079, 0.079]:
            pipe_between(
                "Parafuso da placa",
                (x + dx, y - 0.065, 1.80 + dz),
                (x + dx, y - 0.078, 1.80 + dz),
                0.012,
                cream,
                8,
            )
    curve = bpy.data.curves.new("Nome da rua", "FONT")
    curve.body = label
    curve.size = min(0.130, 1.04 / max(8, len(label)))
    curve.extrude = 0.0016
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    ob = bpy.data.objects.new("Placa / " + label, curve)
    bpy.context.collection.objects.link(ob)
    ob.location = (x, y - 0.068, 1.80)
    ob.rotation_euler.x = RAD(90)
    curve.materials.append(cream)
    pipes = []
    nodes = [
        (-9.4, 1.12, 0.075),
        (-4.8, 1.12, 0.075),
        (-4.28, 1.46, 0.075),
        (-0.46, 1.46, 0.075),
        (0.06, 1.82, 0.075),
        (5.28, 1.82, 0.075),
        (8.35, 2.11, 0.075),
    ]
    for a, b in zip(nodes, nodes[1:]):
        pipes.append(pipe_between("Rede enterrada / tubulação", a, b, 0.094, clay))
        pa, pb = Vector(a), Vector(b)
        d = (pb - pa).normalized()
        for factor in (0.14, 0.67):
            mid = pa.lerp(pb, factor)
            pipes.append(
                pipe_between("Abraçadeira metálica", mid - 0.065 * d, mid + 0.065 * d, 0.115, oxide)
            )
    for ob in pipes:
        for t, hidden in [(0, True), (reveal, False)]:
            frame = number_frame(t, fps)
            ob.hide_render = hidden
            ob.hide_viewport = hidden
            ob.keyframe_insert(data_path="hide_render", frame=frame)
            ob.keyframe_insert(data_path="hide_viewport", frame=frame)


def move_hand(rig, events, fps):
    root = rig["root"]
    enter = events["entrada_mao"]
    houses = events["casas"]
    ground = events["calcada"]
    for t, xyz, rot, scale in [
        (0, (-2.08, -0.85, 19.3), (-13, -29, 6), 1.24),
        (enter - 0.14, (-2.04, -0.85, 17.9), (-13, -29, 6), 1.24),
        (enter + 0.11, (-1.92, -0.88, 14.8), (-14, -29, 6), 1.24),
        (enter + 0.56, (-1.45, -0.98, 9.45), (-14, -25, 8), 1.24),
        (enter + 0.99, (-1.21, -0.80, 8.59), (-12, -23, 11), 1.24),
        (events["moedas"] + 0.24, (-1.09, -0.75, 8.62), (-14, -22, 12), 1.24),
        (houses - 0.08, (-0.82, -0.69, 8.7), (-16, -19, 13), 1.24),
        (houses + 0.63, (-0.59, -0.59, 8.76), (-16, -17, 16), 1.24),
        (houses + 1.60, (-0.88, -0.42, 9.45), (-18, -22, 21), 1.24),
        (ground + 0.08, (-1.13, -0.26, 10.00), (-17, -24, 19), 1.24),
        (events["revelacao"] + 0.05, (-2.65, 0.37, 17.8), (-14, -30, 12), 1.24),
        (events["revelacao"] + 0.45, (-2.82, 0.67, 20.1), (-14, -31, 12), 1.24),
    ]:
        # Girar a mão para o perfil primeiro; inclinar o punho no plano da imagem depois.
        angle = (
            Matrix.Rotation(RAD(rot[0] + 9), 4, "X")
            @ Matrix.Rotation(RAD(rot[1] - 11), 4, "Y")
            @ Matrix.Rotation(RAD(104 + (rot[2] - 12) * 0.42), 4, "Z")
        ).to_euler()
        pose(
            root,
            t,
            fps,
            (xyz[0] - 0.43, xyz[1], xyz[2] - 0.40),
            tuple(math.degrees(a) for a in angle),
            scale,
        )
    for t, value in [
        (0, 0.22),
        (enter + 0.19, 0.20),
        (enter + 0.99, 0.025),
        (events["moedas"] - 0.18, 0.02),
        (events["moedas"] + 0.71, 0.34),
        (houses + 0.04, 0.20),
        (houses + 0.73, 0.58),
        (ground + 0.10, 0.72),
        (events["revelacao"] + 0.35, 0.94),
    ]:
        pose_hand(rig, value, number_frame(t, fps))


def lifting_wave(objects, times, fps, rng, kind):
    for i, (obj, start) in enumerate(zip(objects, times)):
        location = obj.location.copy()
        original_angles = tuple(math.degrees(r) for r in obj.rotation_euler)
        scale = tuple(obj.scale)
        side = -1 if location.x < 0 else 1
        twist = side * rng.uniform(6, 15)
        if kind == "casa":
            route = [
                (0.15, 0.12, -0.02, -0.05, (1, -twist * 0.25, -2), 1),
                (0.48, 0.88, -0.04, -0.07, (-5, twist, 4), 1),
                (0.84, 2.86, 0.16, -0.34, (-9, twist * 1.9, 10), 0.90),
                (1.16, 5.15, 0.53, -0.59, (-18, twist * 2.7, -9), 0.57),
                (1.48, 7.30, 0.89, -0.57, (-29, twist * 3.8, -16), 0.19),
                (1.66, 8.25, 1, -0.52, (-34, twist * 4.1, -26), 0.018),
            ]
        elif kind == "árvore":
            route = [
                (0.19, 0.27, -0.04, 0, (0, twist * 0.5, 1), 1),
                (0.46, 2.02, 0.11, -0.12, (8, twist * 2, 10), 1),
                (0.82, 5.63, 0.50, -0.28, (24, twist * 3, 20), 0.62),
                (1.19, 8.19, 1, -0.45, (38, twist * 4, 45), 0.025),
            ]
        else:
            route = [
                (0.14, 0.21, 0.01, 0.10, (-3, twist * 0.3, 2), 1),
                (0.33, 1.24, 0.04, 0.42, (-12, twist * 0.92, 6), 0.99),
                (0.55, 3.59, 0.21, 0.94, (-23, twist * 1.72, 16), 0.73),
                (0.84, 7.32, 0.75, 0.13, (-41, twist * 2.3, 30), 0.20),
                (1.04, 10.21, 1, -0.22, (-65, twist * 3.1, 50), 0.018),
            ]
        pose(obj, 0, fps, location, original_angles, scale)
        pose(obj, start, fps, location, original_angles, scale)
        destination = 0.48 + side * 0.18
        for dt, dz, progress, dy, delta, shrink in route:
            xyz = (location.x + (destination - location.x) * progress, location.y + dy, location.z + dz)
            rot = tuple(original + change for original, change in zip(original_angles, delta))
            pose(obj, start + dt, fps, xyz, rot, tuple(v * shrink for v in scale))


def dust(village, times, fps, rng):
    mats = [
        create_material("Poeira / areia", (0.60, 0.365, 0.164), 0, 0.91),
        create_material("Poeira / cal", (0.72, 0.52, 0.31), 0, 0.90),
    ]
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
    template = bpy.context.object
    meshes = []
    for mat in mats:
        mesh = template.data.copy()
        mesh.materials.append(mat)
        meshes.append(mesh)
    bpy.data.objects.remove(template, do_unlink=True)
    for house, start in zip(village["houses"], times):
        center = house.location.copy()
        for i in range(12):
            ob = put_linked("Poeira na fundação", meshes[i % 2], center)
            a = rng.uniform(-math.pi, math.pi)
            x = center.x + math.cos(a) * rng.uniform(0.5, 1.08)
            y = center.y + math.sin(a) * 0.75
            interval = start + 0.12 + rng.uniform(0, 0.17)
            size = rng.uniform(0.017, 0.075)
            pose(ob, interval, fps, (x, y, 0.04), scale=size * 0.2)
            pose(
                ob,
                interval + 0.24,
                fps,
                (x + math.cos(a) * 0.35, y + math.sin(a) * 0.38, rng.uniform(0.18, 0.59)),
                scale=size,
            )
            pose(
                ob,
                interval + 0.57,
                fps,
                (x + math.cos(a) * 0.77, y + math.sin(a) * 0.65, 0.045),
                scale=0.001,
            )
            transient(ob, interval, interval + 0.60, fps)


def configure_output(scene, width, height, fps, samples, duration, engine):
    if engine == "CYCLES":
        from cena_3d import filter_noise

        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 3
        scene.cycles.diffuse_bounces = 2
        scene.cycles.glossy_bounces = 1
        filter_noise(scene)
    elif engine == "EEVEE":
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = samples
        scene.eevee.use_raytracing = False
    else:
        raise ValueError("engine deve ser EEVEE ou CYCLES.")
    scene.render.use_motion_blur = False
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = 1, round(duration * fps)
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 24
    scene.render.film_transparent = False


def build(cfg, args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = cfg["title"]
    fps = args.fps or cfg["fps"]
    configure_output(
        scene,
        args.width or cfg["width"],
        args.height or cfg["height"],
        fps,
        args.samples or cfg["samples"],
        cfg["duration"],
        cfg.get("engine", "EEVEE").upper(),
    )
    rng = random.Random(cfg.get("seed", 27))
    village = build_village()
    daylight(scene)
    e = cfg["eventos"]
    rig = build_hand()
    move_hand(rig, e, fps)
    house_times = [e["casas"] + d for d in (0.39, 0.19, 0.00, 0.30, 0.48)]
    lifting_wave(village["houses"], house_times, fps, rng, "casa")
    tree_times = [e["arvores"] + (i % 5) * 0.075 for i in range(len(village["trees"]))]
    lifting_wave(village["trees"], tree_times, fps, rng, "árvore")
    plot_times = [e["calcada"] + d for d in (0.22, 0.10, 0.01, 0.15, 0.29)]
    lifting_wave(village["plots"], plot_times, fps, rng, "piso")
    dust(village, house_times, fps, rng)
    spiral_coins(e["moedas"], fps, rng)
    sign_and_pipes(cfg.get("placa", "RUA DO SOL"), e["calcada"] + 0.30, fps)
    witness = village.get("witness")
    if witness:
        xyz = witness.location.copy() + Vector((-0.09, -1.12, 0))
        witness.scale *= 0.88
        angs = [math.degrees(r) for r in witness.rotation_euler]
        for t, dx, dy, yaw in [
            (0, 0, 0, 0),
            (2.0, 0, 0, 0),
            (2.4, -0.10, -0.09, -15),
            (4.03, -0.10, -0.09, -15),
            (4.77, -0.20, -0.29, -33),
            (7.91, -0.20, -0.29, -33),
            (9.0, -0.16, -0.32, -12),
        ]:
            pose(witness, t, fps, (xyz.x + dx, xyz.y + dy, xyz.z), (angs[0], angs[1], angs[2] + yaw))
    for lot, start in zip(village["plots"], plot_times):
        for j, fragment in enumerate(sorted(lot.children, key=lambda child: child.location.y)):
            base = fragment.location.copy()
            direction = -1 if j % 2 else 1
            pose(fragment, 0, fps, base, (0, 0, 0))
            pose(fragment, start + 0.09, fps, base, (0, 0, 0))
            pose(
                fragment,
                start + 0.44,
                fps,
                (base.x + direction * 0.24, base.y + (j - 1.5) * 0.34, base.z + 0.12 * j),
                ((j - 1) * 9, direction * (11 + 1.2 * j), direction * 5.5),
            )
            pose(
                fragment,
                start + 0.82,
                fps,
                (base.x + direction * 0.88, base.y + (j - 1.5) * 1.05, base.z + 0.59 * j),
                ((j - 1) * 34, direction * (38 + 2 * j), direction * 18),
            )
    camera_path(scene, cfg["camera"], fps)
    for key, label in [
        ("entrada_mao", "Mão no céu"),
        ("moedas", "Moedas"),
        ("casas", "Casas"),
        ("calcada", "Calçada"),
        ("revelacao", "Rua vazia"),
    ]:
        scene.timeline_markers.new(label, frame=number_frame(e[key], fps))
    scene.frame_set(1)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = None
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.color_type = "MATERIAL"
                area.spaces.active.overlay.show_overlays = False
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", "--config", type=Path, default=MODULES.parent / "assets" / "vila.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--still", type=int)
    for flag in ("width", "height", "fps", "samples"):
        parser.add_argument("--" + flag, type=int)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    cfg = json.loads(args.scene.read_text(encoding="utf-8-sig"))
    if cfg.get("modelo") != "vila":
        raise ValueError("Escolha um arquivo de cena com modelo vila.")
    for flag in ("width", "height", "fps", "samples"):
        if (getattr(args, flag) or cfg[flag]) < 1:
            raise ValueError(flag + " precisa ser positivo.")
    scene = build(cfg, args)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    frames = output / "frames"
    frames.mkdir(exist_ok=True)
    scene.render.filepath = "//frames/"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "cena.blend"), compress=True)
    if args.still is not None:
        if not 1 <= args.still <= scene.frame_end:
            raise ValueError("Quadro de teste fora da duração.")
        scene.frame_set(args.still)
        scene.render.filepath = str(output / ("quadro-%04d.png" % args.still))
        bpy.ops.render.render(write_still=True)
    if args.render:
        scene.render.filepath = str(frames) + "/"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
