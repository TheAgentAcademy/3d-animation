"""Cenário original da vila. Importar com o Python do Blender e chamar build_village()."""

import math
import random

import bpy
from mathutils import Vector


def linear(hexcolor):
    rgb = tuple(int(hexcolor[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in rgb) + (1,)


def material(name, color, rough=0.75, metallic=0, variation=0.0, grain=3.0):
    title = "Vila • " + name
    old = bpy.data.materials.get(title)
    if old:
        return old
    mat = bpy.data.materials.new(title)
    value = linear(color)
    mat.diffuse_color = value
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = value
    shader.inputs["Roughness"].default_value = rough
    shader.inputs["Metallic"].default_value = metallic
    if variation:
        tx = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = grain
        noise.inputs["Detail"].default_value = 2.3
        mat.node_tree.links.new(tx.outputs["Object"], noise.inputs["Vector"])
        ramp = nodes.new("ShaderNodeValToRGB")
        for element, factor in zip(ramp.color_ramp.elements, (1 - variation, 1 + variation)):
            element.color = tuple(min(1.0, x * factor) for x in value[:3]) + (1,)
        mat.node_tree.links.new(noise.outputs["Fac"], ramp.inputs[0])
        mat.node_tree.links.new(ramp.outputs[0], shader.inputs["Base Color"])
    return mat


def clay_ground():
    mat = material("Argila, rachaduras de contração", "B99360")
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    if nodes.get("Malha de fissuras"):
        return mat
    coord = nodes.new("ShaderNodeTexCoord")
    dist = nodes.new("ShaderNodeTexNoise")
    dist.inputs["Scale"].default_value = 0.84
    dist.inputs["Detail"].default_value = 3
    links.new(coord.outputs["Object"], dist.inputs["Vector"])
    amp = nodes.new("ShaderNodeVectorMath")
    amp.operation = "SCALE"
    amp.inputs["Scale"].default_value = 0.18
    links.new(dist.outputs["Color"], amp.inputs[0])
    add = nodes.new("ShaderNodeVectorMath")
    add.operation = "ADD"
    links.new(coord.outputs["Object"], add.inputs[0])
    links.new(amp.outputs["Vector"], add.inputs[1])
    cells = nodes.new("ShaderNodeTexVoronoi")
    cells.name = "Malha de fissuras"
    cells.voronoi_dimensions = "2D"
    cells.feature = "DISTANCE_TO_EDGE"
    cells.inputs["Scale"].default_value = 1.7
    links.new(add.outputs[0], cells.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.001, linear("726042")
    e[1].position, e[1].color = 0.07, linear("CBAB79")
    m = e.new(0.017)
    m.color = linear("A58B62")
    links.new(cells.outputs["Distance"], ramp.inputs[0])
    links.new(ramp.outputs[0], nodes.get("Principled BSDF").inputs["Base Color"])
    return mat


def ico_template():
    t = (1 + math.sqrt(5)) / 2
    verts = [
        Vector(v).normalized()
        for v in [
            (-1, t, 0),
            (1, t, 0),
            (-1, -t, 0),
            (1, -t, 0),
            (0, -1, t),
            (0, 1, t),
            (0, -1, -t),
            (0, 1, -t),
            (t, 0, -1),
            (t, 0, 1),
            (-t, 0, -1),
            (-t, 0, 1),
        ]
    ]
    coarse = [
        (0, 11, 5),
        (0, 5, 1),
        (0, 1, 7),
        (0, 7, 10),
        (0, 10, 11),
        (1, 5, 9),
        (5, 11, 4),
        (11, 10, 2),
        (10, 7, 6),
        (7, 1, 8),
        (3, 9, 4),
        (3, 4, 2),
        (3, 2, 6),
        (3, 6, 8),
        (3, 8, 9),
        (4, 9, 5),
        (2, 4, 11),
        (6, 2, 10),
        (8, 6, 7),
        (9, 8, 1),
    ]
    fine, mid = [], {}

    def between(a, b):
        k = tuple(sorted((a, b)))
        if k not in mid:
            mid[k] = len(verts)
            verts.append((verts[a] + verts[b]).normalized())
        return mid[k]

    for a, b, c in coarse:
        d, f, g = between(a, b), between(b, c), between(c, a)
        fine += [(a, d, g), (d, b, f), (g, f, c), (d, f, g)]
    return verts, coarse, fine


ICO, COARSE, FINE = ico_template()


class Geometry:
    """Acumular peças com seus materiais em uma malha por objeto animável."""

    def __init__(self):
        self.v, self.f, self.matindices, self.slots = [], [], [], {}

    def mesh(self, vertices, faces, mat):
        i = len(self.v)
        self.v.extend(vertices)
        index = self.slots.setdefault(mat, len(self.slots))
        self.f.extend([tuple(i + j for j in f) for f in faces])
        self.matindices.extend([index] * len(faces))

    def box(self, p, dimensions, mat, axes=None):
        p = Vector(p)
        if axes is None:
            axes = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        dx, dy, dz = [Vector(axis) * (size / 2) for axis, size in zip(axes, dimensions)]
        poly = [
            p + x * dx + y * dy + z * dz
            for x, y, z in [
                (-1, -1, -1),
                (1, -1, -1),
                (1, 1, -1),
                (-1, 1, -1),
                (-1, -1, 1),
                (1, -1, 1),
                (1, 1, 1),
                (-1, 1, 1),
            ]
        ]
        self.mesh(
            poly, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat
        )

    def beam(self, a, b, w, d, mat):
        a, b = Vector(a), Vector(b)
        run = (b - a).normalized()
        anchor = Vector((0, 1, 0)) if abs(run.y) < 0.95 else Vector((1, 0, 0))
        side = anchor.cross(run).normalized()
        deep = run.cross(side).normalized()
        self.box((a + b) / 2, (w, d, (b - a).length), mat, (side, deep, run))

    def rod(self, a, b, r1, r2, mat, sides=9):
        a, b = Vector(a), Vector(b)
        v = (b - a).normalized()
        ref = Vector((0, 0, 1)) if abs(v.z) < 0.85 else Vector((0, 1, 0))
        u = v.cross(ref).normalized()
        w = v.cross(u)
        vertices = [
            p + r * (math.cos(i * 2 * math.pi / sides) * u + math.sin(i * 2 * math.pi / sides) * w)
            for p, r in ((a, r1), (b, r2))
            for i in range(sides)
        ]
        faces = [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))]
        faces.extend((j, (j + 1) % sides, (j + 1) % sides + sides, j + sides) for j in range(sides))
        self.mesh(vertices, faces, mat)

    def ball(self, p, r, mat, detailed=False):
        p = Vector(p)
        vertices = [
            p + Vector((q.x * r[0], q.y * r[1], q.z * r[2])) for q in (ICO if detailed else ICO[:12])
        ]
        self.mesh(vertices, FINE if detailed else COARSE, mat)

    def finish(self, title, parent=None, origin=(0, 0, 0)):
        data = bpy.data.meshes.new(title)
        data.from_pydata(self.v, [], self.f)
        for mat in self.slots:
            data.materials.append(mat)
        data.polygons.foreach_set("material_index", self.matindices)
        data.update()
        ob = bpy.data.objects.new(title, data)
        bpy.context.collection.objects.link(ob)
        ob.parent, ob.location = parent, origin
        return ob


def wall_outline(g, w, d, h, peak, mat):
    coords = [(-w, 0), (w, 0), (w, h), (0, peak), (-w, h)]
    v = [(x, y, z) for y in (-d, d) for x, z in coords]
    faces = [tuple(range(5)), tuple(reversed(range(5, 10)))]
    faces += [(i, (i + 1) % 5, (i + 1) % 5 + 5, i + 5)[::-1] for i in range(5)]
    g.mesh(v, faces, mat)


def window(g, x, y, z, w, h, p, shutters=False, flower=False):
    wood, edge = p["dark"], p["wood"]
    g.box((x, y - 0.018, z), (w + 0.11, 0.075, h + 0.12), wood)
    g.box((x, y - 0.067, z), (w - 0.04, 0.044, h - 0.04), p["glass"])
    for i in (-1, 1):
        for j in (-1, 1):
            # The sky-lit upper panes read even when a façade fills only 100 pixels.
            c = p["windowtop"] if j == 1 else p["windowbot"]
            g.box((x + i * w * 0.215, y - 0.095, z + j * h * 0.228), (w * 0.37, 0.024, h * 0.405), c)
    for dx in (-w / 2, 0, w / 2):
        g.box((x + dx, y - 0.12, z), (0.037, 0.06, h + 0.035), edge)
    for dz in (-h / 2, -h * 0.08, h / 2):
        g.box((x, y - 0.115, z + dz), (w + 0.04, 0.05, 0.043), edge)
    g.box((x, y - 0.1, z - h / 2 - 0.06), (w + 0.16, 0.19, 0.075), p["stone2"])
    if shutters:
        for s in (-1, 1):
            for k in range(2):
                g.box(
                    (x + s * (w / 2 + 0.085 + k * 0.107), y - 0.025, z),
                    (0.094, 0.045, h * 0.94),
                    p["shutter"],
                )
            for dz in (-h * 0.31, h * 0.31):
                g.box((x + s * (w / 2 + 0.14), y - 0.055, z + dz), (0.21, 0.025, 0.033), wood)
    if flower:
        g.box((x, y - 0.15, z - h / 2 - 0.005), (w + 0.075, 0.17, 0.13), p["wood"])
        for k in range(7):
            a = x + (k - 3) * w / 6.5
            g.ball((a, y - 0.18, z - h / 2 + 0.11 + 0.023 * (k % 3)), (0.10, 0.078, 0.07), p["leaf"])
            if k % 2 == 0:
                g.ball((a, y - 0.218, z - h / 2 + 0.158), (0.042, 0.035, 0.038), p["flor"])


def door(g, x, y, p):
    w, h = 0.60, 1.0
    g.box((x, y - 0.035, 0.66), (w + 0.16, 0.1, 1.12), p["dark"])
    g.box((x, y - 0.103, 0.62), (w, 0.06, h), p["shutter"])
    for j in range(6):
        g.box((x + (j - 2.5) * 0.10, y - 0.14, 0.62), (0.007, 0.015, 0.95), p["wood"])
    for z in (0.31, 0.89):
        g.box((x - 0.19, y - 0.145, z), (0.17, 0.03, 0.035), p["iron"])
    g.ball((x + 0.17, y - 0.19, 0.55), (0.042, 0.035, 0.041), p["gold"])
    # Stone lintel, jambs and two steps.
    for side in (-1, 1):
        for k in range(5):
            g.box(
                (x + side * (w / 2 + 0.078), y - 0.06, 0.19 + 0.202 * k), (0.125, 0.155, 0.18), p["stone2"]
            )
    g.box((x, y - 0.066, 1.14), (w + 0.32, 0.18, 0.13), p["stone2"])
    g.box((x, y - 0.21, 0.095), (0.90, 0.37, 0.12), p["stone"])
    g.box((x, y - 0.37, 0.038), (0.98, 0.33, 0.07), p["stone2"])


def roof(g, w, d, h, peak, p, rng):
    reach = w + 0.16
    eave = h - 0.11
    top = peak + 0.10
    depth = d + 0.22
    for side in (-1, 1):

        def tilepoint(t, y, over=0):
            return (side * reach * t, y, top + (eave - top) * t + over)

        pts = [tilepoint(t, y, 0) for t, y in [(0, -depth), (1, -depth), (1, depth), (0, depth)]]
        g.mesh(pts, [(0, 1, 2, 3) if side == 1 else (3, 2, 1, 0)], p["dark"])
        for row in range(8):
            t0 = row / 8
            t1 = (row + 1) / 8
            for col in range(-1, 9):
                y0 = max(-depth, -depth + (col + 0.5 * (row % 2)) * 2 * depth / 8)
                y1 = min(depth, -depth + (col + 1 + 0.5 * (row % 2)) * 2 * depth / 8)
                if y1 - y0 < 0.035:
                    continue
                y0 += 0.003
                y1 -= 0.003
                taper = min(0.034, (y1 - y0) * 0.13)
                corners = [
                    tilepoint(t0, y0, 0.025),
                    tilepoint(t1 - 0.013, y0, 0.048),
                    tilepoint(t1, y0 + taper, 0.048),
                    tilepoint(t1, y1 - taper, 0.048),
                    tilepoint(t1 - 0.013, y1, 0.048),
                    tilepoint(t0, y1, 0.025),
                ]
                g.mesh(
                    corners,
                    [tuple(range(6)) if side == 1 else tuple(reversed(range(6)))],
                    rng.choice(p["tiles"]),
                )
        # Dark exposed end-grain beneath the red verge.
        for y in (-depth, depth):
            g.beam((0, y, top - 0.018), (side * reach, y, eave - 0.018), 0.079, 0.12, p["wood"])
            g.beam(
                (0, y - 0.012, top + 0.038),
                (side * reach, y - 0.012, eave + 0.038),
                0.045,
                0.13,
                p["tiles"][0],
            )
    for k in range(9):
        a = -depth + k * 2 * depth / 9
        g.rod(
            (0, a, top + 0.025), (0, a + 2 * depth / 9 - 0.007, top + 0.025), 0.092, 0.084, p["tiles"][2], 8
        )


def house(index, x, p):
    g = Geometry()
    rng = random.Random(736 + index)
    w = [1.38, 1.34, 1.46, 1.37, 1.42][index]
    d = [1.06, 1.10, 1.12, 1.08, 1.09][index]
    h = [2.43, 2.54, 2.54, 2.48, 2.49][index]
    peak = h + [1.27, 1.34, 1.38, 1.25, 1.29][index]
    y = -d
    wall_outline(g, w, d, h, peak, p["plasters"][index])
    g.box((0, 0, 0.13), (w * 2 + 0.07, d * 2 + 0.075, 0.26), p["mortar"])
    for j in range(2):
        for k in range(-1, 9):
            left = max(-w, -w + (k + 0.5 * (j % 2)) * 2 * w / 8)
            right = min(w, -w + (k + 1 + 0.5 * (j % 2)) * 2 * w / 8)
            if right - left > 0.055:
                g.box(
                    ((left + right) / 2, y - 0.050, 0.069 + 0.123 * j),
                    (right - left - 0.021, 0.073, 0.105),
                    rng.choice(p["stones"]),
                )
    for yy in (-d, d):
        g.box((0, yy, 1.35), (w * 2 + 0.12, 0.15, 0.14), p["wood"])
        g.box((0, yy, 2.48), (w * 2 + 0.10, 0.14, 0.11), p["wood"])
        g.box((0, yy, 0.29), (w * 2 + 0.1, 0.10, 0.082), p["dark"])
        for xpost in (-w, -w * 0.35, w * 0.35, w):
            g.box((xpost, yy, 1.40), (0.112, 0.133, 2.25), p["wood"])
        for s in (-1, 1):
            g.beam(
                (s * (w - 0.07), yy - 0.03, 1.43),
                (s * (w - 0.43), yy - 0.03, 1.76),
                0.081,
                0.105,
                p["wood"],
            )
            g.beam((0, yy, peak - 0.02), (s * w, yy, h - 0.01), 0.115, 0.12, p["wood"])
            g.beam((s * 0.84, yy, 2.52), (s * 0.38, yy, 2.99), 0.081, 0.105, p["wood"])
        g.box((0, yy, (h + peak) / 2), (0.1, 0.12, peak - h), p["wood"])
    for s in (-1, 1):
        for z in (0.32, 1.35, 2.45):
            g.box((s * w, 0, z), (0.129, 2 * d + 0.073, 0.096), p["wood"])
        g.box((s * w, 0, 1.37), (0.13, 0.11, 2.3), p["wood"])
        g.box((s * (w + 0.018), -0.48, 1.9), (0.08, 0.54, 0.71), p["dark"])
        g.box((s * (w + 0.068), -0.48, 1.9), (0.055, 0.46, 0.62), p["windowtop"])
        for yy in (-0.71, -0.48, -0.25):
            g.box((s * (w + 0.105), yy, 1.9), (0.03, 0.03, 0.61), p["wood"])
        g.box((s * (w + 0.105), -0.48, 1.89), (0.03, 0.48, 0.035), p["wood"])
        g.beam((s * w, 0.1, 1.46), (s * w, d - 0.05, 2.34), 0.095, 0.086, p["wood"])
    for j, xx in enumerate((-w * 0.55, w * 0.55)):
        window(
            g,
            xx,
            y - 0.012,
            1.93,
            0.65,
            0.68,
            p,
            shutters=(index + j) % 2 == 0,
            flower=(index + j) % 2 == 1,
        )
    window(g, 0, y - 0.01, 2.91, 0.48, 0.53, p)
    dx = -0.62 if index in (0, 2, 4) else 0.67
    door(g, dx, y, p)
    window(g, -dx, y, 0.77, 0.70, 0.66, p, shutters=False, flower=index != 2)
    roof(g, w, d, h, peak, p, rng)
    chimney_x = -0.67 if index % 2 else 0.68
    chimney_z = peak - 0.29
    g.box((chimney_x, 0.40, chimney_z), (0.40, 0.44, 1.10), p["stone2"])
    for j in range(5):
        for k in range(2):
            g.box(
                (chimney_x + (k - 0.5) * 0.177, 0.166, chimney_z - 0.27 + j * 0.14),
                (0.155, 0.023, 0.107),
                rng.choice(p["chimney"]),
            )
    g.box((chimney_x, 0.4, chimney_z + 0.56), (0.49, 0.51, 0.12), p["dark"])
    g.box((chimney_x, 0.4, chimney_z + 0.636), (0.43, 0.46, 0.073), p["stone2"])
    if index in (1, 3):
        # Fabric over the shopfront; strips wrap over the scalloped valance.
        awning_x = -dx
        for k in range(7):
            xx = awning_x + (k - 3) * 0.156
            color = p["awning"] if k % 2 else p["stone2"]
            g.beam((xx, y - 0.08, 1.32), (xx, y - 0.54, 1.15), 0.157, 0.025, color)
            g.box((xx, y - 0.54, 1.083), (0.153, 0.025, 0.137), color)
    else:
        sx = dx - 0.48 if dx > 0 else dx + 0.51
        g.rod((sx, y, 1.35), (sx, y - 0.38, 1.35), 0.029, 0.026, p["iron"], 6)
        g.rod((sx, y - 0.34, 1.35), (sx, y - 0.34, 1.21), 0.014, 0.014, p["iron"], 6)
        g.ball((sx, y - 0.34, 1.113), (0.088, 0.081, 0.145), p["lamp"])
        g.ball((sx, y - 0.34, 1.22), (0.105, 0.095, 0.075), p["iron"])
        g.ball((sx, y - 0.34, 0.998), (0.074, 0.066, 0.045), p["iron"])
    return g.finish("Casa %02d • enxaimel e telhas" % (index + 1), origin=(x, 0, 0))


def tree(name, x, y, size, p, rng):
    g = Geometry()
    g.rod((0, 0, 0), (0.055, 0.03, 1.05), 0.13, 0.079, p["bark"], 7)
    for a, b in [
        ((0.0, 0.0, 0.53), (-0.34, -0.04, 1.22)),
        ((0.02, 0.01, 0.64), (0.39, 0.04, 1.3)),
        ((0.04, 0.02, 0.83), (-0.02, 0.23, 1.54)),
    ]:
        g.rod(a, b, 0.075, 0.026, p["bark"], 6)
    for c, rad in [
        ((-0.31, -0.07, 1.28), (0.53, 0.47, 0.53)),
        ((0.27, 0.08, 1.42), (0.55, 0.48, 0.64)),
        ((-0.07, 0.16, 1.72), (0.55, 0.51, 0.63)),
        ((0.02, -0.19, 1.52), (0.44, 0.42, 0.51)),
    ]:
        mat = rng.choice(p["leaves"])
        g.ball(c, rad, mat, False)
    o = g.finish(name, origin=(x, y, 0))
    o.scale = (size, size, size * (1 + rng.uniform(-0.09, 0.1)))
    o.rotation_euler.z = rng.uniform(-0.5, 0.5)
    return o


def person(name, origin, p, coat, angle=150):
    g = Geometry()
    skin = p["skin"]
    # Local front faces -Y. All clothes and face details travel together.
    for s in (-1, 1):
        g.rod(
            (s * 0.10, 0.015, 0.71),
            (s * 0.102, 0.025 if s > 0 else -0.04, 0.47),
            0.078,
            0.062,
            p["pants"],
            9,
        )
        g.rod(
            (s * 0.102, 0.025 if s > 0 else -0.04, 0.48),
            (s * 0.118, 0.020 if s > 0 else -0.078, 0.15),
            0.049,
            0.039,
            skin,
            8,
        )
        g.ball((s * 0.119, -0.024 if s > 0 else -0.118, 0.10), (0.076, 0.135, 0.083), p["boot"], True)
        g.rod(
            (s * 0.118, 0.018 if s > 0 else -0.083, 0.15),
            (s * 0.118, 0.018 if s > 0 else -0.083, 0.24),
            0.053,
            0.057,
            p["boot"],
            8,
        )
    g.rod((0, 0, 0.665), (0, 0, 0.767), 0.187, 0.155, p["pants"], 10)
    g.rod((0, 0, 0.704), (0, 0, 1.026), 0.176, 0.18, coat, 10)
    for s in (-1, 1):
        g.ball((s * 0.155, 0.004, 1.003), (0.084, 0.085, 0.096), coat)
        elbow = (s * 0.222, -0.025, 0.85)
        hand = (s * 0.228, -0.090 if s < 0 else 0.027, 0.724)
        g.rod((s * 0.16, 0, 1.007), elbow, 0.080, 0.057, coat, 7)
        g.rod(elbow, hand, 0.062, 0.046, coat, 7)
        g.ball(hand, (0.05, 0.055, 0.063), skin, True)
    g.rod((0, 0, 1.029), (0, 0, 1.14), 0.070, 0.064, skin, 10)
    g.ball((0, -0.005, 1.22), (0.131, 0.112, 0.161), skin, True)
    g.ball((0, 0.016, 1.32), (0.144, 0.123, 0.101), p["hair"], True)
    g.ball((0, 0.086, 1.245), (0.119, 0.087, 0.13), p["hair"], True)
    for s in (-1, 1):
        g.ball((s * 0.12, -0.006, 1.22), (0.030, 0.033, 0.042), skin, True)
        g.ball((s * 0.047, -0.105, 1.245), (0.012, 0.008, 0.014), p["dark"], True)
    g.ball((0, -0.115, 1.218), (0.024, 0.032, 0.027), skin, True)
    g.beam((-0.025, -0.105, 1.178), (0.026, -0.105, 1.177), 0.009, 0.009, p["lip"])
    g.rod((0, 0, 1.022), (0, 0, 1.075), 0.112, 0.097, p["scarf"], 9)
    g.beam((-0.045, -0.137, 1.03), (0.01, -0.165, 0.92), 0.055, 0.024, p["scarf"])
    g.beam((-0.123, -0.10, 1.029), (0.145, -0.125, 0.711), 0.025, 0.021, p["boot"])
    g.box((0.146, -0.068, 0.72), (0.132, 0.108, 0.12), p["leather"])
    actor = g.finish(name, origin=origin)
    actor.rotation_euler.z = math.radians(angle)
    return actor


def materials():
    palette = {
        "dark": ("Carvalho em sombra", "422B25"),
        "wood": ("Enxaimel oleado", "704735"),
        "mortar": ("Argamassa antiga", "968B78"),
        "stone": ("Arenito cinza", "B5AA91"),
        "stone2": ("Calcário lavrado", "E0D5B3"),
        "glass": ("Rebaixo da vidraça", "22373E"),
        "windowtop": ("Vidro azul celeste", "709CB0"),
        "windowbot": ("Vidro antigo na sombra", "3A5862"),
        "shutter": ("Madeira com tinta petróleo", "3B6869"),
        "awn": ("Tecido vermelho", "96474A"),
        "iron": ("Ferro forjado", "3C3738"),
        "lamp": ("Vidro mel", "F0B25E"),
        "gold": ("Latão", "C99A4E"),
        "leaf": ("Folhas de gerânio", "427432"),
        "flor": ("Gerânio coral", "D6544B"),
        "bark": ("Casca de árvore", "76513B"),
        "grass": ("Grama dos lotes", "76A64F"),
        "border": ("Areia das juntas", "B4AB91"),
        "skin": ("Pele", "C98D66"),
        "hair": ("Cabelo castanho", "432F25"),
        "pants": ("Short índigo", "354357"),
        "boot": ("Couro marrom", "533B30"),
        "leather": ("Bolsa", "9D6643"),
        "scarf": ("Lenço coral", "BF4D37"),
        "lip": ("Boca", "8D594A"),
        "coat": ("Casaco açafrão", "E4A51E"),
    }
    p = {
        key: material(
            title, col, variation=0.16 if key in ("wood", "stone", "grass", "bark") else 0, grain=5.5
        )
        for key, (title, col) in palette.items()
    }
    p["awning"] = p["awn"]

    def series(key, title, colors, rough=0.78, variation=0):
        p[key] = [
            material(title + " " + str(i + 1), c, rough, variation=variation, grain=4.0)
            for i, c in enumerate(colors.split())
        ]

    series("plasters", "Reboco de cal", "EFE0BB F8E2AD F8E8CC EDD9BC EFDAB4", variation=0.18)
    series("tiles", "Telha de terracota", "9C483A AA4A3D B85542 B85B49 C3634D AE503F", 0.68, variation=0.12)
    series("stones", "Pedra de embasamento", "A79983 C6B69A B3A086 D2C3A4 BAAC94")
    series("chimney", "Tijolo cozido", "A97158 C89676 B67958 C3886D")
    series("leaves", "Folhagem", "558447 648F50 78A15C 4C7C47 729952")
    series("pavers", "Lajes da praça", "E6DABC DFCEAE EADFBE E3D4B6 DFD3B5 E9DEC3", variation=0.11)
    series("hedges", "Hedge", "558639 639047 6F944D")
    series("hills", "Prados ao sol", "79A747 719F43 76A346 78A844 84AE50 70A03C")
    series(
        "strata", "Estratos de terra", "856245 92724F 73523C A4815C 9E7956 886647 70533E", variation=0.35
    )
    series("gravel", "Seixos na fratura", "B49C7E 9F8C76 C1AC89 756354 B39A71 8F7C66")
    series("far", "Cristas distantes", "92ABA0 9EB5AC A6BAB5 92A99C")
    series("pine", "Pinheiros", "55795D 608562 688966")
    return p


def earth_slab(g, y0, y1, p, rng):
    # A superfície assenta exatamente com a vizinha. Bordas inferiores irregulares
    # expõem três estratos distintos e uma seção quebrada, visíveis no arrancamento.
    lo, hi = -1.896, 1.896
    outline = []
    for a, b, n in [
        ((lo, y0), (hi, y0), 6),
        ((hi, y0), (hi, y1), 5),
        ((hi, y1), (lo, y1), 6),
        ((lo, y1), (lo, y0), 5),
    ]:
        for j in range(n):
            t = j / n
            outline.append((a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t))
    mid = (y0 + y1) / 2
    top = [(x, y, -0.009) for x, y in outline]
    grass_edge = [(x, y, -0.045 - rng.uniform(0.008, 0.035)) for x, y in outline]
    topsoil = [
        (x + rng.uniform(-0.035, 0.035), y + rng.uniform(-0.035, 0.035), -0.14 - rng.uniform(0.015, 0.072))
        for x, y in outline
    ]
    lower = [
        (
            x * 0.93 + rng.uniform(-0.073, 0.073),
            mid + (y - mid) * 0.925 + rng.uniform(-0.075, 0.075),
            -0.31 - rng.uniform(0, 0.15),
        )
        for x, y in outline
    ]
    inner = [
        (
            x * 0.55 + rng.uniform(-0.14, 0.14),
            mid + (y - mid) * 0.5 + rng.uniform(-0.12, 0.12),
            -0.40 - rng.uniform(0.035, 0.19),
        )
        for x, y in outline
    ]
    center = (rng.uniform(-0.15, 0.15), mid + rng.uniform(-0.12, 0.12), -0.59)
    g.mesh(top, [tuple(range(len(top)))], p["grass"])
    for i in range(len(top)):
        j = (i + 1) % len(top)
        for up, down, mat in (
            (top, grass_edge, p["grass"]),
            (grass_edge, topsoil, p["strata"][2]),
            (topsoil, lower, rng.choice(p["strata"])),
        ):
            g.mesh([up[i], down[i], down[j], up[j]], [(0, 1, 2, 3)], mat)
        c = rng.choice(p["strata"])
        g.mesh([lower[i], inner[i], inner[j], lower[j]], [(0, 1, 2), (0, 2, 3)], c)
        g.mesh([inner[i], center, inner[j]], [(0, 1, 2)], rng.choice(p["strata"]))
        if i % 3 == 0:
            x, y, z = lower[i]
            g.ball((x, y, z + 0.075), (0.105, 0.090, 0.064), rng.choice(p["gravel"]))
    for k in range(16):
        x = rng.uniform(-1.65, 1.65)
        y = mid + rng.uniform(-1.13, 1.13)
        z = -0.53 + 0.16 * max(abs(x) / 1.65, abs(y - mid) / 1.13)
        r = rng.uniform(0.072, 0.15)
        g.ball((x, y, z), (r * 1.2, r * 0.83, r * 0.71), rng.choice(p["gravel"]))
    for k in range(4):
        x = rng.uniform(-1.35, 1.35)
        y = mid + rng.uniform(-1.0, 1)
        dx = rng.uniform(-0.38, 0.38)
        dy = rng.uniform(-0.28, 0.28)
        start = (x, y, -0.48)
        fork = (x + dx, y + dy, -0.66)
        tip = (x + dx * 0.8 + 0.09, y + dy * 1.8, -0.79)
        g.rod(start, fork, 0.032, 0.019, p["bark"], 5)
        g.rod(fork, tip, 0.019, 0.005, p["bark"], 4)
        g.rod(fork, (x + dx * 1.6 - 0.11, y + dy, -0.73), 0.015, 0.003, p["bark"], 4)


def plot(idx, x, p):
    rng = random.Random(401 + idx)
    root = bpy.data.objects.new("Lote %02d • terreno destacável" % (idx + 1), None)
    bpy.context.collection.objects.link(root)
    root.location = (x, 0, 0)
    root.empty_display_size = 0.21
    sections = [Geometry() for _ in range(4)]

    def section(y):
        return sections[max(0, min(3, int((y + 9) / 3)))]

    bounds = [(-15, -6), (-6, -3), (-3, 0), (0, 3)]
    for g, (y0, y1) in zip(sections, bounds):
        earth_slab(g, y0, y1, p, rng)
        start, end = y0, min(y1, -2)
        if start < end:
            g.box((0, (start + end) / 2, -0.002), (3.793, end - start, 0.012), p["border"])
    for row in range(13):
        y = -14.50 + row
        g = section(y)
        for k in range(-1, 4):
            x0 = max(-1.897, -1.897 + (k + 0.5 * (row % 2)) * 1.265)
            x1 = min(1.897, -1.897 + (k + 1 + 0.5 * (row % 2)) * 1.265)
            if x1 - x0 <= 0.03:
                continue
            g.box(((x0 + x1) / 2, y, 0.008), (x1 - x0 - 0.018, 0.982, 0.014), rng.choice(p["pavers"]))
    g = section(-1.83)
    for k in range(7):
        g.box(((k - 3) * 0.544, -1.83, 0.043), (0.526, 0.345, 0.085), rng.choice(p["stones"]))
    for k in range(4):
        g.box(
            ((-0.63 if idx % 2 == 0 else 0.62), -1.40 - k * 0.103, 0.032),
            (0.83, 0.094, 0.060),
            rng.choice(p["pavers"]),
        )
    for side in (-1, 1):
        if (idx + int(side)) % 3 == 1:
            continue
        for j in range(5):
            bx = side * (0.99 + rng.random() * 0.36)
            by = -1.18 - rng.random() * 0.39
            g.ball((bx, by, 0.100), (0.12, 0.116, 0.095), rng.choice(p["hedges"]))
            if j % 2 == 0:
                g.ball((bx, by, 0.194), (0.035, 0.034, 0.029), p["flor"])
    for j, g in enumerate(sections):
        center = sum(bounds[j]) / 2
        g.v = [(v[0], v[1] - center, v[2]) for v in g.v]
        g.finish("Torrão %02d.%d • laje, raízes e seixos" % (idx + 1, j + 1), root, (0, center, 0))
    return root


def landheight(x, y):
    amp = min(1, max(0, (y - 3) / 16))
    a = 0.9 + 0.67 * math.sin(x * 0.114) + 0.65 * math.sin(y * 0.16 + x * 0.048)
    b = 2.35 * math.exp(-(((x + 20) / 15) ** 2) - ((y - 29) / 13) ** 2)
    c = 2.0 * math.exp(-(((x - 26) / 20) ** 2) - ((y - 30) / 13) ** 2)
    return -0.20 + amp * (a + b + c + max(0, (y - 29)) * 0.045)


def hills(p):
    rng = random.Random(9421)
    fields = Geometry()
    xs = list(range(-132, 133, 6))
    ys = [3, 7, 13, 21, 29, 39, 52, 69, 85, 108]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            a, b = xs[i : i + 2]
            y, z = ys[j : j + 2]
            pts = [
                (a, y, landheight(a, y)),
                (b, y, landheight(b, y)),
                (b, z, landheight(b, z)),
                (a, z, landheight(a, z)),
            ]
            fields.mesh(pts, [(0, 1, 2), (0, 2, 3)], rng.choice(p["hills"]))
    for j in range(2):
        y = 69 + j * 23
        for x in range(-145, 145, 5):
            a = 4.5 + 2.4 * math.sin(x * 0.054 + j * 0.9) + 2 * math.cos(x * 0.109 - j)
            b = 4.5 + 2.4 * math.sin((x + 5) * 0.054 + j * 0.9) + 2 * math.cos((x + 5) * 0.109 - j)
            fields.mesh(
                [(x, y, -0.1), (x + 5, y, -0.1), (x + 5, y, b + j * 1.5), (x, y, a + j * 1.5)],
                [(0, 1, 2, 3)],
                p["far"][j],
            )
    # Distinct clusters break evenly spaced horizons.
    for center, depth in [(-24, 21), (-12, 35), (12, 28), (27, 22), (38, 27), (-41, 31), (0, 50)]:
        for i in range(rng.randint(11, 22)):
            x = center + rng.uniform(-3.8, 3.8)
            y = depth + rng.uniform(-2.1, 2.3)
            z = landheight(x, y) - 0.08
            h = rng.uniform(0.74, 2.0)
            fields.rod((x, y, z), (x, y, z + 0.5 * h), 0.055 * h, 0.035 * h, p["bark"], 5)
            fields.rod((x, y, z + 0.27 * h), (x, y, z + 0.96 * h), 0.31 * h, 0.01, rng.choice(p["pine"]), 6)
            fields.rod(
                (x, y, z + 0.55 * h), (x, y, z + 1.14 * h), 0.23 * h, 0.006, rng.choice(p["pine"]), 6
            )
    fields.finish("Vale • colinas, campos e bosques")


def build_village():
    """Criar cinco casas e cinco lotes destacáveis. +Z para cima, fachadas voltadas a -Y."""
    from vila_ceu import apply_sky

    p = materials()
    base = Geometry()
    base.box((0, -10, -0.23), (320, 300, 0.20), clay_ground())
    base.finish("Subsolo • argila exposta")
    hills(p)
    xs = (-7.6, -3.8, 0, 3.8, 7.6)
    plots = [plot(i, x, p) for i, x in enumerate(xs)]
    houses = [house(i, x, p) for i, x in enumerate(xs)]
    rng = random.Random(74)
    trees = [
        tree("Árvore de rua %02d" % (i + 1), x, y, s, p, rng)
        for i, (x, y, s) in enumerate(
            [
                (-5.7, -0.52, 1.12),
                (-1.91, 0.15, 1.12),
                (1.91, 0.69, 1.03),
                (5.69, -0.62, 1.21),
                (-9.30, 0.27, 1.24),
                (9.34, 0.55, 1.26),
            ]
        )
    ]
    witness = person("Testemunha • casaco de açafrão", (-2, -2.30, 0.016), p, p["coat"])
    apply_sky()
    return {"houses": houses, "plots": plots, "trees": trees, "witness": witness}
