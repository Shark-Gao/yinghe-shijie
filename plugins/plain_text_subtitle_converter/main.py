import json
import os
import shutil
import time
import traceback

from sdk import PluginContext, PluginEvent
from utils import get_draft_json_file, read_draft_json

from .core import (
    DEFAULT_FONT_PATH,
    convert_draft_to_plain_text,
    extract_cues_from_draft,
    verify_plain,
)


ACTION_ID = "plain_text_subtitle_converter"


def _line_order_value(label: str) -> str:
    return {
        "保持原顺序": "source",
        "英文在上，中文在下": "en-zh",
        "中文在上，英文在下": "zh-en",
    }.get(label, "source")


def _backup_file(draft_file: str) -> str:
    root, ext = os.path.splitext(draft_file)
    backup_path = f"{root}.plain_text_backup_{time.strftime('%Y%m%d_%H%M%S')}{ext}"
    shutil.copy2(draft_file, backup_path)
    return backup_path


def _write_draft(ctx: PluginContext, draft_file: str, draft_json: dict, encrypt: bool):
    content = json.dumps(draft_json, ensure_ascii=False, separators=(",", ":"))
    ctx.write_draft_file(draft_file, content, encrypt=encrypt)


def setup(ctx: PluginContext):
    ctx.log("会员字幕转普通字幕插件已初始化")

    ctx.register_ui_action(
        action_id=ACTION_ID,
        label="会员字幕转普通字幕",
        icon="magic",
        location="draft_action_bar",
    )

    @ctx.on(PluginEvent.UI_ACTION)
    async def on_ui_action(params):
        if params.get("actionId") != ACTION_ID:
            return {"status": "ignored"}

        selected_drafts = params.get("selectedDrafts", [])
        if not selected_drafts:
            ctx.alert("请先选择至少一个草稿。")
            return {"status": "error", "message": "未选择草稿"}

        form_result = ctx.show_custom_form(
            {
                "title": "会员字幕转普通字幕",
                "items": [
                    {"type": "label", "text": f"已选择 {len(selected_drafts)} 个草稿。"},
                    {"type": "label", "text": "处理会在原草稿上写回，并自动创建备份文件。"},
                    {
                        "type": "combox",
                        "name": "line_order",
                        "label": "双语字幕顺序",
                        "value": "保持原顺序",
                        "options": ["保持原顺序", "英文在上，中文在下", "中文在上，英文在下"],
                    },
                    {
                        "type": "input",
                        "name": "font_path",
                        "label": "字体路径",
                        "value": DEFAULT_FONT_PATH,
                    },
                ],
            }
        )
        if form_result is None:
            ctx.log("用户取消转换。")
            return {"status": "cancelled"}

        line_order = _line_order_value(form_result.get("line_order", "保持原顺序"))
        font_path = (form_result.get("font_path") or DEFAULT_FONT_PATH).strip()

        if not ctx.confirm(
            "确定开始转换吗？\n\n"
            "请确认这些草稿没有在剪映中打开。插件会先备份 draft_content.json，"
            "再把现有字幕重建为普通文本字幕。",
            title="确认转换",
        ):
            ctx.log("用户取消确认。")
            return {"status": "cancelled"}

        ctx.update_ui_action(ACTION_ID, label="处理中...", icon="sync")

        success_count = 0
        failed = []
        try:
            for index, draft in enumerate(selected_drafts, 1):
                draft_name = draft.get("name", "未命名草稿")
                folder_path = draft.get("folderPath")
                encrypt = draft.get("isEncrypted", True)
                ctx.log(f"[{index}/{len(selected_drafts)}] 处理草稿: {draft_name}")

                try:
                    if not folder_path or not os.path.isdir(folder_path):
                        raise FileNotFoundError(f"草稿目录无效: {folder_path}")
                    if ctx.is_draft_locked(folder_path):
                        raise RuntimeError("草稿正在被剪映打开，请先关闭后再处理")

                    draft_file = get_draft_json_file(folder_path)
                    if not draft_file:
                        raise FileNotFoundError("找不到 draft_content.json 或 draft_info.json")

                    draft_json = read_draft_json(draft_file, ctx)
                    cue_count = len(extract_cues_from_draft(draft_json, line_order))
                    converted = convert_draft_to_plain_text(
                        draft_json,
                        line_order=line_order,
                        font_path=font_path,
                    )
                    backup_path = _backup_file(draft_file)
                    _write_draft(ctx, draft_file, converted, encrypt=encrypt)
                    verification = verify_plain(converted)

                    success_count += 1
                    ctx.log(
                        f"  成功: {cue_count} 条字幕，备份: {backup_path}，"
                        f"文本轨道: {verification['text_tracks']}"
                    )
                except Exception as exc:
                    failed.append(f"{draft_name}: {exc}")
                    ctx.log(f"  失败: {draft_name}: {exc}")
                    ctx.log(traceback.format_exc())

            if success_count:
                ctx.show_notification(
                    f"成功转换 {success_count}/{len(selected_drafts)} 个草稿",
                    title="会员字幕转普通字幕",
                    type="success",
                )

            message = [f"转换完成：成功 {success_count}/{len(selected_drafts)} 个草稿。"]
            if failed:
                message.append("\n失败项目：")
                message.extend(f"- {item}" for item in failed)
            ctx.alert("\n".join(message), title="处理结果")
            return {
                "status": "success" if success_count else "error",
                "success": success_count,
                "failed": failed,
            }
        finally:
            ctx.update_ui_action(ACTION_ID, label="会员字幕转普通字幕", icon="magic")
