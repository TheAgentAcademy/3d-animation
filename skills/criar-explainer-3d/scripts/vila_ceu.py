"""Céu panorâmico CC0 de Greg Zaal e Jarod Guest, Poly Haven.
https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky
https://polyhaven.com/license

A cópia 4K recebeu uma grade de azul e é incorporada ao .blend.
"""

from math import radians
from pathlib import Path

import bpy


def apply_sky(scene=None, rotation_degrees=0.0):
    """Aplicar o céu à câmera. O sol da cena continua a definir as sombras."""
    scene = scene or bpy.context.scene
    world = scene.world or bpy.data.worlds.new("Céu da vila")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputWorld")
    path = nodes.new("ShaderNodeLightPath")
    coordinate = nodes.new("ShaderNodeTexCoord")
    rotation = nodes.new("ShaderNodeVectorRotate")
    rotation.rotation_type = "Z_AXIS"
    rotation.inputs["Angle"].default_value = radians(rotation_degrees)
    links.new(coordinate.outputs["Generated"], rotation.inputs["Vector"])

    pano = nodes.new("ShaderNodeTexEnvironment")
    asset = Path(__file__).resolve().parents[1] / "assets" / "ceu-kloofendal.jpg"
    pano.image = bpy.data.images.load(str(asset), check_existing=True)
    if not pano.image.packed_file:
        pano.image.pack()
    pano.projection = "EQUIRECTANGULAR"
    pano.interpolation = "Linear"
    links.new(rotation.outputs["Vector"], pano.inputs["Vector"])

    camera = nodes.new("ShaderNodeBackground")
    camera.label = "Panorama fotografado"
    camera.inputs["Strength"].default_value = 1.0
    links.new(pano.outputs["Color"], camera.inputs["Color"])
    fill = nodes.new("ShaderNodeBackground")
    fill.label = "Preenchimento de luz do céu"
    fill.inputs["Color"].default_value = (0.75, 0.845, 1.0, 1)
    fill.inputs["Strength"].default_value = 0.48
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(fill.outputs[0], mix.inputs[1])
    links.new(camera.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    return world
