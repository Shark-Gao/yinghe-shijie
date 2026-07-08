import copy
import json
import re
import uuid


CJK_RE = re.compile(r"[\u4e00-\u9fff]")
DEFAULT_FONT_PATH = (
    "C:/Users/sharkgao.SHARKGAO-PC2/AppData/Local/JianyingPro/Apps/"
    "10.6.0.14057/Resources/Font/SystemFont/zh-hans.ttf"
)


def new_id() -> str:
    return str(uuid.uuid4()).upper()


def reorder_lines(lines: list[str], line_order: str) -> list[str]:
    lines = [line.strip() for line in lines if line and line.strip()]
    if line_order == "source" or len(lines) < 2:
        return lines

    cjk = [line for line in lines if CJK_RE.search(line)]
    non_cjk = [line for line in lines if not CJK_RE.search(line)]
    if line_order == "en-zh" and cjk and non_cjk:
        return non_cjk + cjk
    if line_order == "zh-en" and cjk and non_cjk:
        return cjk + non_cjk
    return lines


def get_material_text(material: dict) -> str:
    content = material.get("content")
    if isinstance(content, str) and content:
        try:
            parsed = json.loads(content)
            text = parsed.get("text")
            if isinstance(text, str):
                return text.strip()
        except json.JSONDecodeError:
            pass

    for key in ("recognize_text", "base_content", "text"):
        value = material.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_cues_from_draft(draft: dict, line_order: str = "source") -> list[dict]:
    materials = draft.get("materials", {}).get("texts", []) or []
    material_by_id = {
        material.get("id"): material
        for material in materials
        if isinstance(material, dict) and material.get("id")
    }

    grouped: dict[tuple[int, int], list[tuple[int, int, str]]] = {}
    text_tracks = [
        (track_index, track)
        for track_index, track in enumerate(draft.get("tracks", []) or [])
        if isinstance(track, dict) and track.get("type") == "text"
    ]
    for track_index, track in text_tracks:
        for segment_index, segment in enumerate(track.get("segments", []) or []):
            timerange = segment.get("target_timerange") or {}
            start = timerange.get("start")
            duration = timerange.get("duration")
            material = material_by_id.get(segment.get("material_id"))
            if not isinstance(start, int) or not isinstance(duration, int) or not material:
                continue
            text = get_material_text(material)
            if not text:
                continue
            grouped.setdefault((start, duration), []).append((track_index, segment_index, text))

    cues = []
    for (start, duration), items in sorted(grouped.items(), key=lambda item: item[0][0]):
        lines = []
        for _, _, text in sorted(items, key=lambda item: (item[0], item[1])):
            lines.extend(text.splitlines())
        lines = reorder_lines(lines, line_order)
        cues.append({"start": start, "duration": duration, "text": "\n".join(lines)})
    return cues


def content_json(text: str, font_path: str, font_size: float, stroke_width: float) -> str:
    content = {
        "text": text,
        "styles": [
            {
                "fill": {"content": {"render_type": "solid", "solid": {"color": [1, 1, 1]}}},
                "font": {"path": font_path, "id": ""},
                "strokes": [
                    {
                        "content": {
                            "render_type": "solid",
                            "solid": {"color": [0, 0, 0]},
                        },
                        "width": stroke_width,
                        "mode": 0,
                    }
                ],
                "size": font_size,
                "range": [0, len(text)],
            }
        ],
    }
    return json.dumps(content, ensure_ascii=False, separators=(",", ":"))


def make_text_material(text: str, font_path: str, font_size: float, stroke_width: float) -> dict:
    return {
        "id": new_id(),
        "type": "text",
        "content": content_json(text, font_path, font_size, stroke_width),
        "base_content": "",
        "recognize_text": "",
        "recognize_task_id": "",
        "recognize_model": "",
        "recognize_type": 0,
        "words": {"start_time": [], "end_time": [], "text": []},
        "current_words": {"start_time": [], "end_time": [], "text": []},
        "combo_info": {"text_templates": []},
        "caption_template_info": {},
        "lyrics_template": {},
        "subtitle_keywords": {},
        "subtitle_keywords_config": None,
        "language": "",
        "multi_language_current": "none",
        "group_id": "",
        "add_type": 0,
        "sub_type": 0,
        "check_flag": 15,
        "alignment": 1,
        "font_path": font_path,
        "font_size": font_size,
        "font_id": "",
        "font_name": "",
        "font_resource_id": "",
        "font_source_platform": 0,
        "fonts": [],
        "text_color": "#FFFFFF",
        "text_alpha": 1.0,
        "border_color": "#000000",
        "border_alpha": 1.0,
        "border_width": stroke_width,
        "border_mode": 0,
        "has_shadow": False,
        "shadow_alpha": 0.0,
        "shadow_angle": -45.0,
        "shadow_color": "",
        "shadow_distance": 0.0,
        "shadow_point": {"x": 0.0, "y": 0.0},
        "shadow_smoothing": 0.0,
        "layer_weight": 1,
        "line_spacing": 0.02,
        "letter_spacing": 0.0,
        "line_feed": 1,
        "line_max_width": 0.86,
        "initial_scale": 1.0,
        "global_alpha": 1.0,
        "background_alpha": 1.0,
        "background_color": "",
        "background_fill": "",
        "background_style": 0,
        "is_rich_text": False,
        "is_lyric_effect": False,
        "is_words_linear": False,
        "is_batch_replace": False,
        "text_to_audio_ids": [],
        "tts_auto_update": False,
        "translate_original_text": "",
        "ssml_content": "",
    }


def make_text_segment(material_id: str, cue: dict, index: int, y: float) -> dict:
    return {
        "id": new_id(),
        "caption_info": None,
        "cartoon": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": y},
        },
        "common_keyframes": [],
        "desc": "",
        "enable_adjust": False,
        "enable_video_mask": True,
        "extra_material_refs": [],
        "group_id": "",
        "is_placeholder": False,
        "material_id": material_id,
        "render_index": 14000 + index,
        "render_timerange": {"duration": 0, "start": 0},
        "source": "segmentsourcenormal",
        "source_timerange": None,
        "speed": 1.0,
        "state": 0,
        "target_timerange": {"start": cue["start"], "duration": cue["duration"]},
        "template_id": "",
        "template_scene": "default",
        "track_attribute": 0,
        "track_render_index": 1,
        "uniform_scale": {"on": True, "value": 1.0},
        "visible": True,
        "volume": 1.0,
    }


def sanitize_draft(
    draft: dict,
    cues: list[dict],
    font_path: str,
    font_size: float,
    stroke_width: float,
    y: float,
) -> dict:
    text_track = {
        "attribute": 0,
        "flag": 0,
        "id": new_id(),
        "is_default_name": True,
        "name": "",
        "type": "text",
        "segments": [],
    }
    text_materials = []
    for index, cue in enumerate(cues):
        material = make_text_material(cue["text"], font_path, font_size, stroke_width)
        text_materials.append(material)
        text_track["segments"].append(make_text_segment(material["id"], cue, index, y))

    draft["tracks"] = [track for track in draft.get("tracks", []) if track.get("type") != "text"]
    draft["tracks"].append(text_track)

    materials = draft.setdefault("materials", {})
    materials["texts"] = text_materials
    materials["material_animations"] = []
    materials["text_templates"] = []
    materials["ai_translates"] = []
    materials["multi_language_refs"] = []

    config = draft.setdefault("config", {})
    config["multi_language_current"] = "none"
    config["multi_language_list"] = []
    config["multi_language_main"] = "none"
    config["multi_language_mode"] = "none"
    config["subtitle_recognition_id"] = ""
    config["subtitle_taskinfo"] = []
    draft["render_index_track_mode_on"] = True
    return draft


def convert_draft_to_plain_text(
    draft: dict,
    line_order: str = "source",
    font_path: str = DEFAULT_FONT_PATH,
    font_size: float = 4.4,
    stroke_width: float = 0.08,
    y: float = -0.82,
) -> dict:
    cues = extract_cues_from_draft(draft, line_order)
    if not cues:
        raise ValueError("No subtitle/text cues were found to convert.")
    return sanitize_draft(copy.deepcopy(draft), cues, font_path, font_size, stroke_width, y)


def verify_plain(draft: dict) -> dict:
    tracks = draft.get("tracks", []) or []
    text_tracks = [track for track in tracks if track.get("type") == "text"]
    texts = draft.get("materials", {}).get("texts", []) or []
    animations = draft.get("materials", {}).get("material_animations", []) or []
    return {
        "tracks_total": len(tracks),
        "text_tracks": len(text_tracks),
        "text_track_segments": [len(track.get("segments", []) or []) for track in text_tracks],
        "text_materials": sum(1 for item in texts if item.get("type") == "text"),
        "subtitle_materials": sum(1 for item in texts if item.get("type") == "subtitle"),
        "material_animations": len(animations),
        "nonempty_recognize_or_language_fields": sum(
            1
            for item in texts
            if item.get("recognize_task_id") or item.get("recognize_model") or item.get("language")
        ),
        "text_segment_extra_refs": sum(
            len(segment.get("extra_material_refs", []) or [])
            for track in text_tracks
            for segment in track.get("segments", []) or []
        ),
    }
