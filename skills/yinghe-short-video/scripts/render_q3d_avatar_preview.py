"""Render the Q3D avatar prototype's built-in head-turn and mouth animation."""

from __future__ import annotations

from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets" / "avatars" / "q3d_female_rig_prototype" / "preview_frames" / "frame_"

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 720
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 64
scene.render.filepath = str(OUT)
bpy.ops.render.render(animation=True)
print(f"Rendered animation frames: {OUT}")
