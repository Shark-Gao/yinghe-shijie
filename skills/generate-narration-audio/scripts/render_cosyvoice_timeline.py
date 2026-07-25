#!/usr/bin/env python3
"""使用本地 CosyVoice 将中文解说时间线渲染为 MP3，并写出实测时长清单。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", required=True, help="时间线 JSON 路径。")
    parser.add_argument("--output", help="覆盖默认的 MP3 输出路径。")
    parser.add_argument("--segment-manifest", help="将每段实测音频时长写入 JSON 文件。")
    return parser.parse_args()


def hms_to_ms(value: str) -> int:
    h, m, rest = value.split(":")
    if "." in rest:
        s, ms = rest.split(".", 1)
        ms = (ms + "000")[:3]
    else:
        s, ms = rest, "000"
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def resolve_project_path(value: str, timeline_path: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    for parent in (timeline_path.parent, *timeline_path.parents):
        resolved = (parent / candidate).resolve()
        if resolved.exists():
            return resolved
    return (timeline_path.parent / candidate).resolve()


def add_cosyvoice_paths(model_dir: str, timeline_path: Path) -> None:
    """让 CosyVoice 能找到仓库本身和 Matcha-TTS 子模块。"""
    roots: list[Path] = []
    model_path = resolve_project_path(model_dir, timeline_path)
    if model_path.exists():
        roots.extend([model_path.parent.parent, model_path.parent.parent.parent])
    workspace_root = Path(__file__).resolve().parents[3]
    roots.append(workspace_root / "tools" / "CosyVoice")
    for root in roots:
        root = root.resolve()
        matcha = root / "third_party" / "Matcha-TTS"
        if (root / "cosyvoice").is_dir():
            sys.path.insert(0, str(root))
        if matcha.is_dir():
            sys.path.insert(0, str(matcha))


def rate_to_speed(rate: str | None) -> float:
    if not rate:
        return 1.0
    match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)%\s*", str(rate))
    if not match:
        return 1.0
    return max(0.5, min(2.0, 1.0 + float(match.group(1)) / 100.0))


def collect_audio(generator) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for item in generator:
        speech = item["tts_speech"]
        if hasattr(speech, "detach"):
            speech = speech.detach().cpu().numpy()
        speech = np.asarray(speech)
        if speech.ndim == 2:
            speech = speech[0]
        if speech.ndim != 1:
            raise SystemExit(f"CosyVoice 输出维度异常：{speech.shape}")
        chunks.append(speech.astype(np.float32, copy=False))
    if not chunks:
        raise SystemExit("CosyVoice 没有返回音频。")
    return np.concatenate(chunks)


def synthesize(model, data: dict, text: str) -> tuple[np.ndarray, int]:
    mode = str(data.get("cosyvoice_mode", "sft"))
    voice = str(data.get("voice") or "中文男")
    speed = float(data.get("speed") or rate_to_speed(data.get("rate")))
    speed = max(0.5, min(2.0, speed))

    if mode == "sft":
        generator = model.inference_sft(text, voice, stream=False, speed=speed)
    elif mode == "zero_shot":
        prompt_audio = data.get("prompt_audio")
        prompt_text = str(data.get("prompt_text") or "")
        if not prompt_audio or not prompt_text:
            raise SystemExit("CosyVoice zero_shot 模式需要 prompt_audio 和 prompt_text。")
        prompt_audio_path = str(resolve_project_path(prompt_audio, Path(data["_timeline_path"])))
        generator = model.inference_zero_shot(
            text,
            prompt_text,
            prompt_audio_path,
            stream=False,
            speed=speed,
        )
    elif mode in {"instruct", "instruct2"}:
        instruction = str(data.get("instruction") or "")
        if not instruction:
            raise SystemExit("CosyVoice instruct 模式需要 instruction。")
        # 官方 Instruct 示例以结束标记区分指令和要朗读的正文；用户配置时允许省略，
        # 渲染器统一补上，避免把指令内容误当成需要朗读的文本。
        if "<|endofprompt|>" not in instruction:
            instruction = instruction.rstrip() + "<|endofprompt|>"
        if mode == "instruct2" and hasattr(model, "inference_instruct2"):
            prompt_audio = data.get("prompt_audio")
            if not prompt_audio:
                raise SystemExit("CosyVoice instruct2 模式需要 prompt_audio。")
            prompt_audio_path = str(resolve_project_path(prompt_audio, Path(data["_timeline_path"])))
            generator = model.inference_instruct2(
                text,
                instruction,
                prompt_audio_path,
                stream=False,
                speed=speed,
            )
        else:
            generator = model.inference_instruct(
                text,
                voice,
                instruction,
                stream=False,
                speed=speed,
            )
    else:
        raise SystemExit("cosyvoice_mode 只支持 sft、zero_shot、instruct 或 instruct2。")
    return collect_audio(generator), int(model.sample_rate)


def render(data: dict, timeline_path: Path, output_override: str | None, segment_manifest: str | None) -> Path:
    model_dir = str(data.get("cosyvoice_model_dir") or "")
    if not model_dir:
        raise SystemExit("CosyVoice 时间线缺少 cosyvoice_model_dir。")
    add_cosyvoice_paths(model_dir, timeline_path)

    from cosyvoice.cli.cosyvoice import AutoModel
    import torch

    resolved_model_path = resolve_project_path(model_dir, timeline_path)
    model_path = str(resolved_model_path) if resolved_model_path.exists() else model_dir
    use_fp16 = bool(torch.cuda.is_available())
    print(
        f"CosyVoice 设备：{torch.cuda.get_device_name(0) if use_fp16 else 'CPU'}；"
        f"FP16：{'启用' if use_fp16 else '关闭'}",
        flush=True,
    )
    model = AutoModel(model_dir=model_path, load_jit=False, load_trt=False, fp16=use_fp16)

    output_name = output_override or data.get("output_audio") or f"{timeline_path.stem}_CosyVoice.mp3"
    output_path = Path(output_name)
    if not output_path.is_absolute():
        output_path = timeline_path.parent / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    short_temp_root = Path("C:/t")
    short_temp_root.mkdir(parents=True, exist_ok=True)
    build_dir = Path(tempfile.mkdtemp(prefix="cv", dir=short_temp_root))
    data["_timeline_path"] = str(timeline_path)
    try:
        inputs: list[str] = []
        filters: list[str] = []
        labels: list[str] = []
        measured_segments: list[dict] = []
        input_index = 0
        for segment in data.get("segments", []):
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            audio, sample_rate = synthesize(model, data, text)
            wav_path = build_dir / f"{segment['id']}.wav"
            sf.write(wav_path, audio, sample_rate, subtype="PCM_16")
            measured_segments.append(
                {
                    "id": segment["id"],
                    "start": segment["start"],
                    "end": segment.get("end"),
                    "audio_duration": probe_duration(wav_path),
                }
            )
            inputs.extend(["-i", str(wav_path)])
            delay = hms_to_ms(segment["start"])
            label = f"a{input_index}"
            filters.append(f"[{input_index}:a]adelay={delay}|{delay},volume=1[{label}]")
            labels.append(f"[{label}]")
            input_index += 1

        if not labels:
            raise SystemExit("没有可生成的 CosyVoice 解说段。")
        filter_complex = ";".join(filters) + ";" + "".join(labels)
        filter_complex += f"amix=inputs={len(labels)}:duration=longest:normalize=0,apad[mix]"
        filter_script = build_dir / "filter_complex.txt"
        filter_script.write_text(filter_complex, encoding="utf-8")
        cmd = [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex_script",
            str(filter_script),
            "-map",
            "[mix]",
            "-t",
            str(data["video_duration"]),
            "-ac",
            "2",
            "-ar",
            "44100",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)
        if segment_manifest:
            manifest_path = Path(segment_manifest)
            if not manifest_path.is_absolute():
                manifest_path = timeline_path.parent / manifest_path
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "timeline": str(timeline_path),
                        "provider": "cosyvoice",
                        "output_audio": str(output_path),
                        "segments": measured_segments,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        return output_path
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def validate_timeline(data: dict) -> None:
    if not data.get("segments"):
        raise SystemExit("时间线没有 segments。")
    previous = -1
    for segment in data["segments"]:
        start = hms_to_ms(segment["start"])
        if start < previous:
            raise SystemExit(f"时间线起点没有递增：{segment.get('id')}")
        previous = start
        if not str(segment.get("text") or "").strip():
            raise SystemExit(f"时间线段落没有文本：{segment.get('id')}")


def main() -> None:
    args = parse_args()
    timeline_path = Path(args.timeline).resolve()
    data = json.loads(timeline_path.read_text(encoding="utf-8"))
    validate_timeline(data)
    print(render(data, timeline_path, args.output, args.segment_manifest))


if __name__ == "__main__":
    main()
