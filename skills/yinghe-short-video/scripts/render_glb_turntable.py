"""Render a GLB mesh from multiple angles for visual QA."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arg_after(name: str, default: str) -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    for i, value in enumerate(args):
        if value == name and i + 1 < len(args):
            return Path(args[i + 1])
    return Path(default)


src = arg_after("--input", "input.glb").resolve()
out = arg_after("--output", "turntable").resolve()
out.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
if src.suffix.lower() == ".obj":
    bpy.ops.wm.obj_import(filepath=str(src))
    texture_path = src.parent / "texture.png"
    if texture_path.exists():
        image = bpy.data.images.load(str(texture_path), check_existing=True)
        material = bpy.data.materials.new("BakedTexture")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.72
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(material)
else:
    bpy.ops.import_scene.gltf(filepath=str(src))

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not meshes:
    raise RuntimeError("No mesh objects found in GLB")

corners = []
for obj in meshes:
    corners.extend([obj.matrix_world @ Vector(c) for c in obj.bound_box])
min_v = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
max_v = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
center = (min_v + max_v) * 0.5
size = max_v - min_v
radius = max(size.x, size.y, size.z) * 1.35

pivot = bpy.data.objects.new("TurntablePivot", None)
bpy.context.collection.objects.link(pivot)
pivot.location = center
for obj in meshes:
    obj.parent = pivot
    obj.matrix_parent_inverse = pivot.matrix_world.inverted()

camera_data = bpy.data.cameras.new("Camera")
camera = bpy.data.objects.new("Camera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
camera_data.lens = 55

def point_camera(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


camera.location = center + Vector((0.0, size.y * 0.05, -radius))
point_camera(camera, center + Vector((0, size.y * 0.04, 0)))

world = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.035, 0.035, 0.035, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.15

def add_area(name, loc, energy, size_xy):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size_xy
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = loc
    point_camera(light, center)
    return light


add_area("Key", center + Vector((-radius, radius * 0.45, -radius)), 120, radius * 0.8)
add_area("Fill", center + Vector((radius, -radius * 0.1, -radius * 0.55)), 60, radius * 0.7)
add_area("Rim", center + Vector((radius * 0.6, radius * 0.6, radius)), 150, radius * 0.6)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 640
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.view_settings.look = "None"
scene.view_settings.exposure = -1.2
scene.render.fps = 12
scene.frame_start = 1
scene.frame_end = 8

for frame in range(1, 9):
    # TripoSR exports this asset with its long (image-height) axis on X.
    # Rotate it upright once, then turn around that same vertical axis.
    pivot.rotation_euler = (
        math.radians((frame - 1) * 45.0),
        0.0,
        math.radians(90.0),
    )
    scene.render.filepath = str(out / f"angle_{frame:02d}.png")
    scene.frame_set(frame)
    bpy.ops.render.render(write_still=True)

print(f"Rendered turntable: {out}")
