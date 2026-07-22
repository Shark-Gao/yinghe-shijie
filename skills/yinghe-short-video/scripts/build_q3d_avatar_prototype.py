"""Build a rigged Q-style 3D female-avatar prototype in Blender.

Run with:
    blender --background --python build_q3d_avatar_prototype.py

The output is a genuine 3D .blend and animated .glb prototype.  It is a
functional rig foundation for the channel character, not a final sculpt.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "avatars" / "q3d_female_rig_prototype"


def material(name: str, color: tuple[float, float, float, float], roughness: float = 0.55) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def parent_to_bone(obj: bpy.types.Object, armature: bpy.types.Object, bone: str) -> None:
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    mat: bpy.types.Material,
    armature: bpy.types.Object | None = None,
    bone: str | None = None,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    if armature and bone:
        parent_to_bone(obj, armature, bone)
    return obj


def make_armature() -> bpy.types.Object:
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    armature = bpy.context.object
    armature.name = "Q3D_Female_Rig"
    armature.data.name = "Q3D_Female_RigData"
    root = armature.data.edit_bones[0]
    root.name = "root"
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.8)

    def bone(name: str, head: tuple[float, float, float], tail: tuple[float, float, float], parent: bpy.types.EditBone) -> bpy.types.EditBone:
        created = armature.data.edit_bones.new(name)
        created.head = head
        created.tail = tail
        created.parent = parent
        return created

    spine = bone("spine", (0, 0, 0.8), (0, 0, 2.05), root)
    neck = bone("neck", (0, 0, 2.05), (0, 0, 2.45), spine)
    head = bone("head", (0, 0, 2.45), (0, 0, 4.15), neck)
    bone("upper_arm.L", (-0.72, 0, 1.92), (-1.25, 0, 1.48), spine)
    bone("upper_arm.R", (0.72, 0, 1.92), (1.25, 0, 1.48), spine)
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in armature.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")
    return armature


def look_at(obj: bpy.types.Object, target: tuple[float, float, float]) -> None:
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_light(name: str, location: tuple[float, float, float], energy: float, size: float, color: tuple[float, float, float]) -> None:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, (0, 0, 2.5))


def animate(armature: bpy.types.Object, mouth: bpy.types.Object, left_eye: bpy.types.Object, right_eye: bpy.types.Object) -> None:
    head = armature.pose.bones["head"]
    for frame, yaw in ((1, 0), (20, math.radians(11)), (42, math.radians(-11)), (64, 0)):
        bpy.context.scene.frame_set(frame)
        head.rotation_euler[2] = yaw
        head.keyframe_insert(data_path="rotation_euler", index=2)

    open_key = mouth.data.shape_keys.key_blocks["Mouth_Open"]
    for frame, value in ((1, 0.0), (8, 1.0), (15, 0.2), (22, 0.9), (30, 0.0), (40, 0.8), (50, 0.0), (64, 0.0)):
        bpy.context.scene.frame_set(frame)
        open_key.value = value
        open_key.keyframe_insert(data_path="value")

    for eye in (left_eye, right_eye):
        original = eye.scale.z
        for frame, z_scale in ((1, original), (27, original), (29, original * 0.08), (31, original), (64, original)):
            bpy.context.scene.frame_set(frame)
            eye.scale.z = z_scale
            eye.keyframe_insert(data_path="scale", index=2)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

    skin = material("Skin", (0.96, 0.65, 0.52, 1))
    hair = material("Chestnut_Hair", (0.22, 0.055, 0.018, 1), 0.42)
    lavender = material("Lavender_Cardigan", (0.43, 0.25, 0.72, 1))
    cream = material("Cream_Shirt", (0.95, 0.84, 0.66, 1))
    white = material("Eye_White", (1, 0.98, 0.94, 1), 0.35)
    iris = material("Warm_Brown_Iris", (0.16, 0.035, 0.01, 1), 0.3)
    pupil = material("Pupil", (0.01, 0.004, 0.003, 1), 0.2)
    mouth_mat = material("Mouth", (0.18, 0.015, 0.02, 1), 0.4)

    armature = make_armature()
    # Torso and oversized head give the intended Q-style silhouette.
    sphere("Cardigan_Torso", (0, 0.08, 1.35), (1.1, 0.58, 1.22), lavender, armature, "spine")
    sphere("Cream_Shirt", (0, -0.52, 1.63), (0.62, 0.10, 0.72), cream, armature, "spine")
    sphere("Head", (0, 0, 3.25), (1.36, 1.15, 1.34), skin, armature, "head")
    sphere("Hair_Back", (0, 0.18, 3.52), (1.48, 1.16, 1.47), hair, armature, "head")
    # Face covers the front of the hair cap; fringe strands restore a readable hairstyle.
    sphere("Face", (0, -0.28, 3.22), (1.26, 0.98, 1.24), skin, armature, "head")
    for index, x in enumerate((-0.62, -0.25, 0.16, 0.54)):
        strand = sphere(f"Hair_Fringes_{index}", (x, -1.00, 4.02 - abs(x) * 0.34), (0.34, 0.16, 0.62), hair, armature, "head")
        strand.rotation_euler[1] = math.radians(-16 if x < 0 else 16)

    left_white = sphere("EyeWhite.L", (-0.48, -1.10, 3.46), (0.35, 0.11, 0.46), white, armature, "head")
    right_white = sphere("EyeWhite.R", (0.48, -1.10, 3.46), (0.35, 0.11, 0.46), white, armature, "head")
    left_eye = sphere("Iris.L", (-0.48, -1.205, 3.45), (0.19, 0.055, 0.26), iris, armature, "head")
    right_eye = sphere("Iris.R", (0.48, -1.205, 3.45), (0.19, 0.055, 0.26), iris, armature, "head")
    sphere("Pupil.L", (-0.48, -1.255, 3.45), (0.092, 0.035, 0.13), pupil, armature, "head")
    sphere("Pupil.R", (0.48, -1.255, 3.45), (0.092, 0.035, 0.13), pupil, armature, "head")

    mouth = sphere("Mouth", (0, -1.17, 2.93), (0.34, 0.055, 0.105), mouth_mat, armature, "head")
    mouth.shape_key_add(name="Basis")
    open_key = mouth.shape_key_add(name="Mouth_Open")
    for vertex in open_key.data:
        vertex.co.z *= 1.85
        vertex.co.x *= 0.92

    # Simple articulated arms and a hand-on-heart gesture.
    left_arm = sphere("Cardigan_Arm.L", (-0.92, -0.02, 1.34), (0.35, 0.38, 0.90), lavender, armature, "upper_arm.L")
    left_arm.rotation_euler[1] = math.radians(-28)
    right_arm = sphere("Cardigan_Arm.R", (0.88, -0.08, 1.35), (0.35, 0.38, 0.90), lavender, armature, "upper_arm.R")
    right_arm.rotation_euler[1] = math.radians(32)
    hand = sphere("Hand_On_Heart", (0.38, -0.71, 1.84), (0.30, 0.11, 0.48), skin, armature, "spine")
    hand.rotation_euler[1] = math.radians(-36)

    armature["avatar_type"] = "q3d_female_prototype"
    armature["mouth_shape_key"] = "Mouth_Open"
    armature["head_bone"] = "head"
    animate(armature, mouth, left_eye, right_eye)

    bpy.ops.object.camera_add(location=(0, -11.5, 3.0))
    camera = bpy.context.object
    camera.data.lens = 54
    look_at(camera, (0, 0, 2.45))
    bpy.context.scene.camera = camera
    add_light("Key", (-4, -5, 7), 900, 4.5, (1.0, 0.78, 0.65))
    add_light("Fill", (4, -3, 5), 500, 4, (0.60, 0.70, 1.0))
    add_light("Rim", (0, 3, 6), 650, 3, (1.0, 0.65, 0.85))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world.color = (0.055, 0.035, 0.09)
    scene.frame_start = 1
    scene.frame_end = 64
    scene.render.filepath = str(OUT / "q3d_female_rig_preview.png")
    scene.frame_set(20)
    bpy.ops.render.render(write_still=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "q3d_female_rig_prototype.blend"))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=str(OUT / "q3d_female_rig_prototype.glb"),
        export_format="GLB",
        export_animations=True,
        export_cameras=False,
        export_lights=False,
    )
    print(f"Built rigged prototype: {OUT}")


if __name__ == "__main__":
    build()
