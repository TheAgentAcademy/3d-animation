"""Construir um cenário editável a partir de JSON. Executar dentro do Blender 4.3+."""
import argparse
import json
import math
import struct
from pathlib import Path
import sys

import bpy
from mathutils import Vector

LIB = {}
R = math.radians
PALETTE = {
    "ivory": "#FAEDDB", "stone": "#DBBD9B", "tile": "#E6AB8D", "line": "#CE9980",
    "navy": "#183B49", "teal": "#267A79", "mint": "#9BD5BB", "blue": "#3D6FAE",
    "coral": "#DF6348", "gold": "#E9A643", "cocoa": "#493936", "green": "#45725D",
    "slate": "#536879", "denim": "#364B62", "ink": "#22323D", "white": "#FFF4DE",
    "skin1": "#E4A27E", "skin2": "#B97850", "skin3": "#80513C", "skin4": "#F0C9A4",
}


def material(value):
    color = PALETTE.get(value, value)
    if color in LIB:
        return LIB[color]
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = tuple(c / 12.92 if c <= 0.04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb)
    mat = bpy.data.materials.new(value)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*rgb, 1)
    shader.inputs["Roughness"].default_value = .78
    LIB[color] = mat
    return mat


def finish(obj, name, parent=None, color=None):
    obj.name = name
    if parent:
        obj.parent = parent
    if color:
        obj.data.materials.append(material(color))
    return obj


def empty(name, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    obj.empty_display_size = .15
    return finish(obj, name, parent)


def box(name, loc, size, color, parent=None, bevel=.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    for v in obj.data.vertices:
        for axis in range(3):
            v.co[axis] *= size[axis]
    if bevel:
        mod = obj.modifiers.new("Bordas moldadas", "BEVEL")
        mod.width = min(bevel, min(size) / 3)
        mod.segments = 2
        mod = obj.modifiers.new("Normais das faces", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
    return finish(obj, name, parent, color)


def ell(name, loc, size, color, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=loc)
    obj = bpy.context.object
    obj.scale = size
    return finish(obj, name, parent, color)


def cone(name, loc, bottom, top, depth, color, parent=None, sides=14):
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=bottom, radius2=top, depth=depth, location=loc)
    return finish(bpy.context.object, name, parent, color)


def tube(name, start, end, radius, color, parent=None):
    a, b = Vector(start), Vector(end)
    obj = cone(name, (a + b) / 2, radius, radius, (b - a).length, color, parent, 12)
    obj.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return obj


def label(name, loc, body, size, color, parent=None):
    data = bpy.data.curves.new(name, "FONT")
    data.body, data.align_x, data.align_y = body, 'CENTER', 'CENTER'
    data.size, data.extrude, data.resolution_u = size, .003, 4
    ob = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler.x = R(90)
    return finish(ob, name, parent, color)


def character(node, cfg):
    shirt = cfg.get("color", "teal")
    pants = cfg.get("pants", "denim")
    skin = cfg.get("skin", "skin2")
    hair = cfg.get("hair", "cocoa")
    accent = cfg.get("accent", "ivory")
    style = cfg.get("style", "crop")
    rig = {"legs": [], "arms": []}
    body = empty("Tronco / respiração", (0, 0, .67), node)
    rig["body"] = body
    coat = cone("Casaco", (0, 0, .29), .314, .255, .55, shirt, body, 12)
    coat.scale.y = .72
    collar = cone("Gola", (0, 0, .576), .135, .12, .072, accent, body)
    collar.scale.y = .84
    cone("Pescoço", (0, 0, .61), .092, .09, .13, skin, body)
    head = empty("Cabeça", (0, 0, .79), body)
    ell("Rosto", (0, -.008, .018), (.206, .186, .224), skin, head)
    ell("Nariz", (0, -.19, -.004), (.046, .077, .044), skin, head)
    ell("Cabelo", (0, .045, .135), (.218, .192, .157), hair, head)
    for side in (-1, 1):
        ell("Orelha", (side * .197, 0, .018), (.04, .052, .055), skin, head)
        ell("Olho", (side * .076, -.166, .050), (.021, .019, .025), "ink", head)
        brow = box("Sobrancelha", (side * .081, -.165, .091), (.060, .025, .015), hair, head, .006)
        brow.rotation_euler.y = side * R(5)
        leg = empty("Quadril", (side * .132, 0, .68), node)
        rig["legs"].append(leg)
        tube("Calça", (0, 0, -.036), (side * .013, .003, -.528), .104, pants, leg)
        box("Sapato", (side * .013, -.046, -.593), (.205, .306, .13), "ink", leg, .049)
        box("Sola", (side * .013, -.052, -.654), (.215, .308, .039), accent, leg, .015)
        arm = empty("Ombro", (side * .235, 0, .481), body)
        rig["arms"].append(arm)
        tube("Manga", (0, 0, 0), (side * .085, -.014, -.249), .099, shirt, arm)
        tube("Antebraço", (side * .087, -.014, -.249), (side * .095, -.060, -.395), .067, skin, arm)
        ell("Mão", (side * .095, -.065, -.401), (.076, .080, .089), skin, arm)
    if style == "bun":
        ell("Coque", (0, .176, .197), (.126, .11, .118), hair, head)
    elif style == "cap":
        ell("Boné", (0, .015, .152), (.224, .199, .125), accent, head)
        brim = ell("Aba", (0, -.151, .137), (.19, .145, .028), accent, head)
        brim.rotation_euler.x = R(-5)
    elif style == "curls":
        for a in range(9):
            a = 2 * math.pi * a / 9
            ell("Cacho", (.162 * math.cos(a), .13 * math.sin(a), .116), (.087, .084, .092), hair, head)
    if cfg.get("bag"):
        box("Mochila", (0, .172, .27), (.34, .15, .37), accent, body, .074)
        box("Bolso", (0, .251, .20), (.25, .05, .13), shirt, body, .038)
        for s in (-1, 1):
            tube("Alça", (s * .13, -.125, .10), (s * .15, -.118, .532), .026, accent, body)
    return rig


def counter(node, cfg):
    tone = cfg.get("color", "teal")
    box("Rodapé", (0, 0, .09), (2.03, .96, .17), "navy", node, .07)
    box("Bancada", (0, 0, .56), (2.02, .92, .91), tone, node, .085)
    for i in range(15):
        box("Ripa", ((i - 7) * .122, -.464, .54), (.041, .048, .74), tone, node, .016)
    box("Tampo", (0, 0, 1.065), (2.16, 1.03, .125), "ivory", node, .049)
    plaque = box("Placa", (0, -.503, .56), (.53, .09, .47), "navy", node, .047)
    label("Letra", (0, -.554, .57), cfg.get("label", "A"), .37, "white", node)
    box("Pé do terminal", (.52, -.02, 1.144), (.32, .23, .04), "navy", node)
    tube("Haste", (.52, -.02, 1.15), (.52, -.02, 1.40), .038, "navy", node)
    box("Terminal", (.52, -.03, 1.401), (.47, .095, .29), "denim", node, .035)
    box("Marca do terminal", (.52, -.082, 1.40), (.081, .012, .039), "ivory", node)
    cone("Campainha", (-.67, -.19, 1.15), .098, .079, .07, "gold", node)
    for dx in (-.77, .77):
        tube("Coluna", (dx, .36, 1.11), (dx, .36, 2.39), .036, "navy", node)
    box("Testeira", (0, .36, 2.37), (1.76, .16, .38), tone, node, .075)
    label("Guichê", (0, .269, 2.373), cfg.get("sign", "GUICHÊ " + cfg.get("label", "A")), .205, "white", node)


def plant(node):
    cone("Vaso", (0, 0, .32), .27, .36, .63, "coral", node, 15)
    cone("Terra", (0, 0, .636), .315, .315, .035, "cocoa", node, 15)
    for i in range(9):
        phi = i * 2.40
        height = .76 + .22 * (i % 3)
        d = .19 + .04 * (i % 2)
        end = (d * math.cos(phi), d * math.sin(phi), height + .3)
        tube("Haste", (0, 0, .62), end, .019, "green", node)
        leaf = ell("Folha", end, (.12, .049, .282), ("green", "mint", "teal")[i % 3], node)
        leaf.rotation_euler = (R(31), R(13), phi)


def room():
    box("Piso", (0, 0, -.155), (35, 30, .30), "tile", bevel=0)
    for j in range(-9, 10):
        box("Junta horizontal", (0, j * 1.38, -.001), (25, .014, .009), "line", bevel=0)
        box("Junta vertical", (j * 1.38, 0, -.001), (.014, 24, .009), "line", bevel=0)
    box("Parede", (0, 4.38, 3.45), (35, .47, 7), "ivory")
    box("Friso de madeira", (0, 4.08, 1.10), (35, .14, .093), "stone")
    box("Lambril", (0, 4.15, .54), (35, .15, 1.10), "stone")
    for x in (-6.48, -3.24, 0, 3.24, 6.48):
        box("Moldura", (x, 4.09, 3.78), (2.74, .25, 3.91), "stone", bevel=.12)
        box("Janela", (x, 3.94, 3.77), (2.53, .07, 3.65), "mint", bevel=.10)
        for dx in (-.42, .43):
            box("Caixilho", (x + dx, 3.884, 3.77), (.050, .058, 3.62), "ivory")
        box("Travessa", (x, 3.876, 3.73), (2.53, .057, .054), "ivory")
        box("Peitoril", (x, 3.89, 1.92), (2.86, .34, .104), "white")


def local_glb(asset_dir, filename):
    relative = Path(filename)
    path = (asset_dir / relative).resolve()
    if relative.is_absolute() or path.suffix.lower() != ".glb" or not path.is_file():
        raise ValueError("Indique um arquivo GLB relativo ao JSON: " + filename)
    with path.open("rb") as handle:
        header = handle.read(20)
        if len(header) != 20:
            raise ValueError("GLB incompleto: " + filename)
        signature, version, total, length, chunk = struct.unpack("<4sIII4s", header)
        if signature != b"glTF" or version != 2 or chunk != b"JSON" or total != path.stat().st_size or length > total - 20:
            raise ValueError("Cabeçalho GLB 2.0 inválido: " + filename)
        manifest = json.loads(handle.read(length))
    for entry in manifest.get("buffers", []) + manifest.get("images", []):
        if entry.get("uri") and not entry["uri"].startswith("data:"):
            raise ValueError("Incorpore os buffers e as texturas dentro do GLB: " + filename)
    return path


def build_entity(cfg, asset_dir):
    item = empty(cfg["id"])
    kind = cfg["type"]
    rig = None
    if kind == "person":
        rig = character(item, cfg)
    elif kind == "counter":
        counter(item, cfg)
    elif kind == "glb":
        path = local_glb(asset_dir, cfg["file"])
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(path), import_pack_images=True)
        imported = set(bpy.data.objects) - before
        if not imported:
            raise ValueError("Modelo sem objetos: " + str(path))
        for obj in imported:
            if obj.parent is None:
                obj.parent = item
    elif kind == "plant":
        plant(item)
    elif kind in {"box", "bar"}:
        dims = cfg.get("dimensions", [1, 1, 1])
        box("Volume", (0, 0, dims[2] / 2), dims, cfg.get("color", "teal"), item)
    elif kind == "sphere":
        dims = cfg.get("dimensions", [1, 1, 1])
        ell("Elipsoide", (0, 0, 0), tuple(d / 2 for d in dims), cfg.get("color", "teal"), item)
    elif kind == "disc":
        cone("Sinal", (0, 0, .012), cfg.get("radius", .26), cfg.get("radius", .26), .025, cfg.get("color", "ivory"), item, 32)
    elif kind == "label":
        label("Texto", (0, 0, 0), cfg["text"], cfg.get("text_size", .42), cfg.get("color", "navy"), item)
    elif kind == "route":
        points = cfg["points"]
        for start, end in zip(points, points[1:]):
            tube("Segmento", start, end, cfg.get("radius", .025), cfg.get("color", "gold"), item)
    else:
        raise ValueError("Tipo de objeto desconhecido: " + kind)
    return item, rig


def key(obj, prop, t, fps):
    obj.keyframe_insert(data_path=prop, frame=1 + round(t * fps))


def animate(node, rig, cfg, fps):
    keys = [{
        "at": 0, "xyz": cfg.get("xyz", [0, 0, 0]), "yaw": cfg.get("yaw", 0),
        "pitch": cfg.get("pitch", 0), "roll": cfg.get("roll", 0), "scale": cfg.get("scale", 1)
    }] + cfg.get("keys", [])
    previous = -1
    for pose in keys:
        t = pose["at"]
        if t < previous:
            raise ValueError("Chaves fora de ordem em " + cfg["id"])
        previous = t
        if "xyz" in pose:
            node.location = pose["xyz"]
            key(node, "location", t, fps)
        for axis, angle in enumerate(("roll", "pitch", "yaw")):
            if angle in pose:
                node.rotation_euler[axis] = R(pose[angle])
                node.keyframe_insert(data_path="rotation_euler", index=axis,
                                     frame=1 + round(t * fps))
        if "scale" in pose:
            v = pose["scale"]
            node.scale = (v, v, v) if isinstance(v, (int, float)) else v
            key(node, "scale", t, fps)
    if not rig:
        return
    for a, b in cfg.get("walk", []):
        if not a < b:
            raise ValueError("Intervalo de caminhada inválido em " + cfg["id"])
        count = max(4, round((b - a) * 4))
        for j in range(count + 1):
            t = a + (b - a) * j / count
            swing = 0 if j in (0, count) else (-1) ** j * .38
            for side, (leg, arm) in enumerate(zip(rig["legs"], rig["arms"])):
                leg.rotation_euler.x = (1 - 2 * side) * swing
                arm.rotation_euler.x = (2 * side - 1) * swing
                key(leg, "rotation_euler", t, fps)
                key(arm, "rotation_euler", t, fps)
    for t, deg in cfg.get("gesture", []):
        arm = rig["arms"][1]
        arm.rotation_euler.x = R(deg)
        key(arm, "rotation_euler", t, fps)
    for t, angle in cfg.get("lean", []):
        rig["body"].rotation_euler.x = R(angle)
        key(rig["body"], "rotation_euler", t, fps)


def light(name, point, target, watts, diameter, tint):
    bpy.ops.object.light_add(type='AREA', location=point)
    ob = bpy.context.object
    ob.name, ob.data.energy, ob.data.shape, ob.data.size = name, watts, 'DISK', diameter
    ob.data.color = tint
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def cameras(scene, shots, fps, projection="orthographic"):
    if not shots or shots[0]['at'] != 0:
        raise ValueError("A primeira câmera precisa começar em 0.")
    previous = -1
    for i, shot in enumerate(shots):
        if shot['at'] <= previous:
            raise ValueError("Inícios de planos devem ser estritamente crescentes.")
        previous = shot['at']
        cam = bpy.data.cameras.new("Objetiva")
        ob = bpy.data.objects.new("Câmera %02d" % (i + 1), cam)
        bpy.context.collection.objects.link(ob)
        camera_type = shot.get("projection", projection)
        if camera_type not in {"perspective", "orthographic"}:
            raise ValueError("projection deve ser perspective ou orthographic.")
        cam.type = 'PERSP' if camera_type == "perspective" else 'ORTHO'
        lens = float(shot.get("lens_mm", 35))
        for pose in (shot, *shot.get("keys", [])):
            at = pose["at"]
            ob.location = pose["eye"]
            direction = Vector(pose["target"]) - ob.location
            ob.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            if cam.type == 'PERSP':
                lens = float(pose.get("lens_mm", lens))
                if lens < 1:
                    raise ValueError("lens_mm precisa ser pelo menos 1 mm.")
                cam.lens = lens
                key(cam, "lens", at, fps)
            else:
                cam.ortho_scale = pose["scale"]
                key(cam, "ortho_scale", at, fps)
            for attr in ("location", "rotation_euler"):
                key(ob, attr, at, fps)
        marker = scene.timeline_markers.new(shot.get("name", ob.name), frame=1 + round(shot["at"] * fps))
        marker.camera = ob
        if i == 0:
            scene.camera = ob


def filter_noise(scene):
    # Os binários oficiais incluem o denoiser de CPU do próprio Cycles.
    try:
        import _cycles
        has_oidn = getattr(_cycles, "with_openimagedenoise", False)
    except ImportError:
        has_oidn = False
    if has_oidn:
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        scene.cycles.use_denoising = True
        return
    # Em builds de sistema sem OIDN, o compositor 4.x oferece uma alternativa.
    # O Blender 5 redesenhou a API do compositor; o render Cycles continua válido.
    if bpy.app.version >= (5, 0, 0):
        print("Cycles sem OpenImageDenoise. Para reduzir o ruído, aumente --samples.")
        return
    # Filtra o ruído dentro das superfícies pelo albedo e pelas normais.
    # Funciona também em compilações do Blender sem OpenImageDenoise.
    scene.use_nodes = True
    layer = scene.view_layers[0]
    layer.use_pass_diffuse_color = True
    layer.use_pass_normal = True
    tree = scene.node_tree
    source = tree.nodes.get("Render Layers")
    guide = tree.nodes.new("CompositorNodeMixRGB")
    guide.blend_type = 'ADD'
    guide.inputs[0].default_value = .27
    tree.links.new(source.outputs["DiffCol"], guide.inputs[1])
    tree.links.new(source.outputs["Normal"], guide.inputs[2])
    blur = tree.nodes.new("CompositorNodeBilateralblur")
    blur.sigma_space, blur.sigma_color, blur.iterations = 2.25, .047, 1
    tree.links.new(source.outputs["Image"], blur.inputs[0])
    tree.links.new(guide.outputs[0], blur.inputs[1])
    mix = tree.nodes.new("CompositorNodeMixRGB")
    mix.inputs[0].default_value = .93
    tree.links.new(source.outputs["Image"], mix.inputs[1])
    tree.links.new(blur.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], tree.nodes.get("Composite").inputs[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--render", action='store_true', help="Grava também a sequência PNG.")
    parser.add_argument("--still", type=int, help="Renderiza somente o quadro informado.")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--samples", type=int)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    cfg = json.loads(args.scene.read_text(encoding='utf-8'))
    fps = args.fps if args.fps is not None else cfg.get("fps", 24)
    width = args.width if args.width is not None else cfg.get("width", 1080)
    height = args.height if args.height is not None else cfg.get("height", 1920)
    if min(fps, width, height) <= 0 or cfg["duration"] <= 0:
        raise ValueError("Duração, resolução e fps devem ser positivos.")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new("Luz ambiente")
    scene.world.use_nodes = True
    sky = scene.world.node_tree.nodes.get("Background")
    sky.inputs['Color'].default_value = (.82, .85, .90, 1)
    sky.inputs['Strength'].default_value = .38
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples or cfg.get("samples", 8)
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 3
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 1
    scene.render.fps = fps
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = width, height, 100
    scene.frame_start, scene.frame_end = 1, round(cfg['duration'] * fps)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 35
    scene.view_settings.view_transform = 'AgX'
    filter_noise(scene)
    # Guardar a referência de materiais da cena atual, inclusive após execuções na interface.
    LIB.clear()
    PALETTE.update(cfg.get("palette", {}))
    if cfg.get("stage", "plain") == "hall":
        room()
    else:
        box("Chão", (0, 0, -.10), (100, 100, .20), cfg.get("floor", "ivory"), bevel=0)
    ids = set()
    for item in cfg["entities"]:
        if item["id"] in ids:
            raise ValueError("ID duplicado: " + item["id"])
        ids.add(item["id"])
        obj, rig = build_entity(item, args.scene.resolve().parent)
        animate(obj, rig, item, fps)
    outdoor = cfg.get("look") == "exterior"
    if outdoor:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from vila_ceu import apply_sky
        apply_sky(scene)
        sun = cfg.get("sun", {})
        sun_position = Vector(sun.get("direction_from", [-7, -5, 8]))
        if sun_position.length == 0:
            raise ValueError("sun.direction_from precisa de uma direção diferente de zero.")
        bpy.ops.object.light_add(type='SUN', location=sun_position)
        lamp = bpy.context.object
        lamp.name = "Sol da rua"
        lamp.rotation_euler = (-sun_position).to_track_quat('-Z', 'Y').to_euler()
        lamp.data.energy = float(sun.get("strength", 3.0))
        lamp.data.angle = R(float(sun.get("angle", 2.1)))
        lamp.data.color = (1.0, .93, .82)
    else:
        light("Luz principal", (-5, -5, 9), (0, 1, .7), 1150, 6, (1, .88, .75))
        light("Preenchimento", (5, -1, 6), (0, 1, .7), 580, 5, (.75, .88, 1))
        light("Recorte", (-2, 3.5, 6), (0, 0, .7), 420, 4, (1, .92, .80))
    cameras(scene, cfg["shots"], fps, "perspective" if outdoor else "orthographic")
    scene.frame_set(1)
    scene.name = cfg.get("title", "Explainer 3D")
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                view = area.spaces.active
                view.region_3d.view_perspective = 'CAMERA'
                view.shading.color_type = 'MATERIAL'
                view.overlay.show_overlays = False
    args.out.mkdir(parents=True, exist_ok=True)
    frames = args.out / "frames"
    frames.mkdir(exist_ok=True)
    scene.render.filepath = "//frames/"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str((args.out / "cena.blend").resolve()), compress=True)
    if args.still is not None:
        if not scene.frame_start <= args.still <= scene.frame_end:
            raise ValueError("Quadro fora da duração.")
        scene.frame_set(args.still)
        scene.render.filepath = str((args.out / ("quadro-%04d.png" % args.still)).resolve())
        bpy.ops.render.render(write_still=True)
    if args.render:
        scene.render.filepath = str(frames.resolve()) + "/"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
