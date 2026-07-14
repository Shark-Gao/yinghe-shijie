import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "skills" / "generate-narration-audio" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from build_subtitle_tts_timeline import build_timeline, parse_cues
from mix_narration_with_bgm import derive_output_path
from timeline_to_srt import build_srt, default_output_path


class SubtitleTtsTimelineTest(unittest.TestCase):
    def test_bilingual_cues_keep_only_verbatim_chinese_text(self):
        cues = parse_cues(
            "1\n00:00:00,100 --> 00:00:02,400\nHello from the forest\n从树林中发射互联网\n\n"
            "2\n00:00:02,400 --> 00:00:04,000\nNo Chinese here\n"
        )

        self.assertEqual(cues, [{
            "start": "00:00:00.100",
            "end": "00:00:02.400",
            "text": "从树林中发射互联网",
        }])

    def test_vtt_short_timestamps_are_supported(self):
        cues = parse_cues("WEBVTT\n\n00:01.200 --> 00:03.400\n你好，世界\n")

        self.assertEqual(cues, [{
            "start": "00:00:01.200",
            "end": "00:00:03.400",
            "text": "你好，世界",
        }])

    def test_timeline_uses_last_cue_duration_and_direct_audio_name(self):
        fixture = Path(__file__).resolve().parents[1] / "星链如何把网络送到全球_时间线01.srt"
        timeline = build_timeline(fixture, Path("unused.json"), None, None, "zh-CN-YunyangNeural", "+0%")

        self.assertEqual(timeline["mode"], "verbatim_chinese_subtitle_audio")
        self.assertEqual(timeline["output_audio"], "星链如何把网络送到全球_时间线01_中文字幕直读_Yunyang.mp3")
        self.assertTrue(timeline["segments"])
        self.assertEqual(timeline["segments"][0]["text"], "从树林中间发射互联网")
        self.assertEqual(timeline["video_duration"], timeline["segments"][-1]["end"])

    def test_direct_subtitle_bgm_name_is_unambiguous(self):
        narration = Path("outputs/audio/星链_中文字幕直读_Yunyang.mp3")

        self.assertEqual(
            derive_output_path(narration),
            Path("outputs/audio/星链_中文字幕直读_背景音乐_正式版.mp3"),
        )

    def test_chinese_narration_srt_contains_chinese_and_english_translation(self):
        contents = build_srt({"segments": [{
            "id": "seg_001",
            "start": "00:00:00.000",
            "end": "00:00:10.000",
            "text": "这是一段中文解说。",
            "english_text": "This is a Chinese narration.",
        }]})

        self.assertEqual(
            contents,
            "1\n00:00:00,000 --> 00:00:10,000\n这是一段中文解说。\nThis is a Chinese narration.\n",
        )

    def test_chinese_narration_srt_requires_english_translation(self):
        with self.assertRaisesRegex(ValueError, "missing english_text"):
            build_srt({"segments": [{
                "id": "seg_001",
                "start": "00:00:00.000",
                "end": "00:00:10.000",
                "text": "这是一段中文解说。",
            }]})

    def test_chinese_narration_srt_uses_the_standard_output_name(self):
        self.assertEqual(
            default_output_path(Path("outputs/audio/星链_等长解说时间线.json")),
            Path("outputs/audio/星链_中文解说.srt"),
        )


if __name__ == "__main__":
    unittest.main()
