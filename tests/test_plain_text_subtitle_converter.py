import json
import sys
import unittest
from pathlib import Path


PLUGIN_DIR = Path(__file__).resolve().parents[1] / "plugins" / "plain_text_subtitle_converter"
sys.path.insert(0, str(PLUGIN_DIR))


def make_text_material(material_id, text):
    return {
        "id": material_id,
        "type": "subtitle",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }


class PlainTextSubtitleConverterTest(unittest.TestCase):
    def test_converts_existing_subtitle_tracks_to_one_plain_text_track(self):
        from core import convert_draft_to_plain_text, verify_plain

        draft = {
            "tracks": [
                {
                    "type": "text",
                    "segments": [
                        {
                            "material_id": "en",
                            "target_timerange": {"start": 1000, "duration": 2000},
                        }
                    ],
                },
                {
                    "type": "text",
                    "segments": [
                        {
                            "material_id": "zh",
                            "target_timerange": {"start": 1000, "duration": 2000},
                        }
                    ],
                },
            ],
            "materials": {
                "texts": [
                    make_text_material("zh", "你好"),
                    make_text_material("en", "Hello"),
                ],
                "material_animations": [{"id": "old"}],
            },
        }

        converted = convert_draft_to_plain_text(draft, line_order="en-zh")

        self.assertEqual(len(converted["tracks"]), 1)
        self.assertEqual(converted["tracks"][0]["type"], "text")
        self.assertEqual(
            converted["tracks"][0]["segments"][0]["target_timerange"],
            {"start": 1000, "duration": 2000},
        )
        self.assertEqual(len(converted["materials"]["texts"]), 1)
        content = json.loads(converted["materials"]["texts"][0]["content"])
        self.assertEqual(content["text"], "Hello\n你好")
        self.assertEqual(verify_plain(converted)["subtitle_materials"], 0)

    def test_raises_when_no_subtitles_are_found(self):
        from core import convert_draft_to_plain_text

        with self.assertRaisesRegex(ValueError, "No subtitle/text cues"):
            convert_draft_to_plain_text({"tracks": [], "materials": {"texts": []}})


if __name__ == "__main__":
    unittest.main()
