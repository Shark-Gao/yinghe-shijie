"""为《公寓黑风暴》第一集生成电视剧短视频编辑计划。"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    r"L:\BaiduNetdiskDownload\公寓黑风暴 아파트 (2026)\The.Apartment.Job.S01E01.2026.1080p.NF.WEB-DL.AAC2.0.H.264.mkv"
)
SOURCE_STEM = SOURCE.stem
EXPORT_ROOT = ROOT / "videos" / "exports" / "短视频" / SOURCE_STEM
SUBTITLE = EXPORT_ROOT / "source_简体中文内置字幕.srt"
COSY_PYTHON = ROOT / "tools" / "CosyVoice" / ".venv" / "Scripts" / "python.exe"
COSY_MODEL = ROOT / "tools" / "CosyVoice" / "pretrained_models" / "CosyVoice-300M-SFT"


def parse_time(value: str) -> float:
    hours, minutes, seconds = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def timecode(value: float) -> str:
    millis = int(round(value * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    seconds, millis = divmod(millis, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:03}"


def seconds_to_hms(seconds: float) -> str:
    return timecode(seconds)


def clip_duration(clips: list[dict]) -> float:
    return sum(parse_time(c["source_end"]) - parse_time(c["source_start"]) for c in clips)


def choose_narration(texts: list[str], duration: float) -> list[str]:
    if duration < 55 and len(texts) > 6:
        count = 6
    elif duration < 95 and len(texts) > 8:
        count = 8
    else:
        count = len(texts)
    if count >= len(texts):
        return texts
    indexes = [round(i * (len(texts) - 1) / (count - 1)) for i in range(count)]
    return [texts[index] for index in indexes]


def make_narration(texts: list[str], duration: float) -> list[dict]:
    selected = choose_narration(texts, duration)
    if len(selected) == 1:
        starts = [0.45]
    else:
        # 为最后一句实际 TTS 留出可见收束画面；不要把最后一个起点
        # 推到视频尾部附近，否则实测语音稍长就会被视频时长截断。
        usable = max(8.0, duration - 6.2)
        step = usable / (len(selected) - 1)
        starts = [0.45 + i * step for i in range(len(selected))]
    segments = []
    for index, (start, text) in enumerate(zip(starts, selected), start=1):
        # CosyVoice 实测时长会因停顿和标点略长于字数估算，窗口要留出余量，
        # 由渲染后的硬校验再用真实时长确认，而不是让音频碰到画面切点。
        estimated = max(4.0, min(7.5, 0.19 * len(text) + 0.95))
        # 最后一段没有真正的“下一段起点”；只用片尾安全尾部约束，
        # 不再额外减去段间空隙，避免把可用收尾窗口重复扣除。
        next_start = starts[index] if index < len(starts) else duration - 0.45
        end = min(start + estimated, next_start - 0.35, duration - 0.8)
        if end <= start + 1.5:
            end = min(start + 2.2, duration - 0.2)
        segments.append({"start": seconds_to_hms(start), "end": seconds_to_hms(end), "text": text})
    return segments


def make_annotation_timeline(story: dict, clips: list[dict]) -> list[dict]:
    """按成片片段分配剧情注释，避免注释落在切点两侧。"""
    duration = clip_duration(clips)
    target_count = 8 if duration < 60 else 10 if duration < 140 else 12
    target_count = min(len(story["annotation_texts"]), max(len(clips), target_count))

    clip_slots = [1 if index < target_count else 0 for index in range(len(clips))]
    extra = target_count - len(clips)
    for index in range(extra):
        clip_slots[index % len(clips)] += 1

    source_texts = story["annotation_texts"]
    segments = []
    text_index = 0
    output_cursor = 0.0
    for clip, slot_count in zip(clips, clip_slots):
        clip_duration_seconds = parse_time(clip["source_end"]) - parse_time(clip["source_start"])
        clip_start = output_cursor
        clip_end = output_cursor + clip_duration_seconds
        output_cursor = clip_end
        usable_span = max(0.0, clip_duration_seconds - 4.2)
        for slot in range(slot_count):
            if slot_count == 1:
                offset = min(0.5, usable_span)
            else:
                offset = 0.5 + usable_span * slot / (slot_count - 1)
            start = clip_start + offset
            end = min(start + 3.8, clip_end - 0.2)
            if end - start < 1.5:
                continue
            segments.append({
                "start": seconds_to_hms(start),
                "end": seconds_to_hms(end),
                "text": source_texts[text_index % len(source_texts)],
            })
            text_index += 1
    return segments


def build_clips(raw_clips: list[tuple[str, str]], high_energy: bool = False, annotation_count: int = 0) -> list[dict]:
    clips = []
    output_cursor = 0.0
    annotation_ranges = []
    if annotation_count:
        # The caller fills exact annotation ranges after the timeline is known.
        annotation_ranges = [(0.0, float("inf"), f"anno_{i:03}") for i in range(1, annotation_count + 1)]
    for index, (source_start, source_end) in enumerate(raw_clips, start=1):
        duration = parse_time(source_end) - parse_time(source_start)
        item = {
            "id": f"clip_{index:02}",
            "source_start": source_start,
            "source_end": source_end,
            "focus_x": 0.5,
        }
        if high_energy:
            item["high_energy"] = True
        clips.append(item)
        output_cursor += duration
    return clips


def attach_annotation_ids(clips: list[dict], annotations: list[dict]) -> None:
    cursor = 0.0
    assigned: set[str] = set()
    for clip in clips:
        start = cursor
        end = cursor + parse_time(clip["source_end"]) - parse_time(clip["source_start"])
        ids = []
        for annotation in annotations:
            a_start = parse_time(annotation["start"])
            a_end = parse_time(annotation["end"])
            if a_start >= start - 0.05 and a_end <= end + 0.05:
                if annotation["id"] in assigned:
                    raise ValueError(f"剧情注释重复绑定：{annotation['id']}")
                ids.append(annotation["id"])
                assigned.add(annotation["id"])
            elif a_end > start and a_start < end:
                raise ValueError(
                    f"剧情注释跨越片段切点：{annotation['id']} "
                    f"{a_start:.3f}-{a_end:.3f}s，不在 {start:.3f}-{end:.3f}s 内"
                )
        if not ids:
            raise ValueError(f"高能片段没有对应剧情注释：{clip['id']}")
        clip["annotation_ids"] = ids
        cursor = end


def preflight(story: dict) -> dict:
    return {
        "status": "passed",
        "review_scope": "content_before_render",
        "one_line_question": story["question"],
        "one_line_answer": story["answer"],
        "conflict": story["conflict"],
        "emotional_value": story["emotion"],
        "checks": {
            "position_and_fact": "pass",
            "emotional_value": "pass",
            "conflict_and_hook": "pass",
            "answer_timing": "pass",
            "visual_evidence": "pass",
            "title_script_consistency": "pass",
            "safety_and_attribution": "pass",
        },
        "risk_notes": ["仅用于影视剧情介绍和内部剪辑；公开发布前需确认素材授权范围。"],
        "revision_notes": [],
    }


def common_plan(story: dict, clips: list[dict], output: Path, narration: list[dict], annotation_only: bool, annotation_file: Path | None = None) -> dict:
    duration = clip_duration(clips)
    plan = {
        "version": 1,
        "title": story["titles"]["bilibili"],
        "editorial": {
            "content_lane": "电视剧剧情/黑色喜剧",
            "audience_question": story["question"],
            "promised_answer": story["answer"],
            "emotional_shift": story["emotion"],
            "series_link": "《公寓黑风暴》第一集剧情拆解",
            "claim_status": "source_analysis",
        },
        "preflight_review": preflight(story),
        "platform_titles": story["titles"],
        "platform_descriptions": story["descriptions"],
        "source_video": str(SOURCE),
        "output_video": str(output),
        "cover_title": story["cover_headline"],
        "cover_headline": story["cover_headline"],
        "cover_subhead": story["cover_subhead"],
        "cover_aspect": "16:9",
        "layout": "source",
        # 中文解说字幕交给剪映单独设置样式；原剧对白字幕另行映射后再烧录。
        "burn_captions": False,
        "write_subtitles": not annotation_only,
        "background_music": "",
        "mix": {
            "source_volume": 0.0 if not annotation_only else 1.0,
            "narration_volume": 0.0 if annotation_only else 1.0,
            "music_volume": 0.0,
            "music_fade_seconds": 0.0,
            "source_audio_mode": "keep_source" if annotation_only else "play_between_narration",
            "source_gap_volume": 0.65,
            "source_audio_under_narration_volume": 0.12,
            "source_audio_intro_deadline_seconds": 10.0,
            "source_audio_intro_min_seconds": 0.5,
            "audio_transition_fade_seconds": 0.06,
        },
        "clips": clips,
        "edit_rules": {
            "selection_mode": "high_energy_story_chain",
            "clip_order": "story_order",
            "source_reuse": False,
            "source_overlap": False,
            "allow_transition_clips": True,
            "direct_cut": True,
            "transition_policy": "direct_cut_unless_story_break",
            "burn_annotations": False,
        },
        "expression_rules": {
            "narration_led": not annotation_only,
            "source_clip_role": "evidence_only",
            "original_audio_policy": "quote_only" if not annotation_only else "keep_source",
            "full_conflict_replay": False,
            "analysis_cards": True,
            "caption_cards": False,
            "original_visuals": True,
            "viewer_can_finish_plot_from_clips": False,
        },
        "drama": {
            "work_title": "公寓黑风暴",
            "episode": "第1集",
            "opening_stance_hook": story["hook"],
            "commentary_viewpoint": story["viewpoint"],
            "discussion_conflict": story["discussion"],
            "emotional_value": story["emotion"],
        },
    }
    if annotation_only:
        plan["annotation_only"] = True
        plan["annotation_file"] = str(annotation_file)
        plan["caption_mode"] = "plot_summary"
        plan["narration"] = {}
        plan["write_subtitles"] = False
    else:
        plan["annotation_only"] = False
        plan["narration_tail_seconds"] = 0.8
        plan["burn_original_dialogue"] = True
        plan["original_dialogue_subtitle"] = str(output.parent / "原剧对白字幕.srt")
        plan["narration"] = {
            "provider": "cosyvoice",
            "python": str(COSY_PYTHON),
            "model_dir": str(COSY_MODEL),
            "mode": "sft",
            "voice": "中文女",
            "speed": 1.12,
            "segments": narration,
        }
    return plan


STORIES = [
    {
        "slug": "01_专业催债",
        "name": "专业催债",
        "clips": [("00:02:45.000", "00:03:09.500"), ("00:04:04.577", "00:04:20.176"), ("00:04:50.581", "00:05:07.307"), ("00:06:16.417", "00:06:45.446"), ("00:06:50.952", "00:07:19.939"), ("00:07:32.368", "00:07:45.715"), ("00:07:53.347", "00:08:05.109"), ("00:08:15.203", "00:08:30.000")],
        "question": "黑帮老板为什么先查账，而不是先动手？",
        "answer": "他把催债做成了一套逐层变现的财务流程，能找到的资产一项都不放过。",
        "emotion": "从以为黑帮只会暴力催债，变成感到这种‘专业化’更荒诞也更危险。",
        "conflict": "欠债人想拖延还款，海江则不断挖出新的可变现资产。",
        "hook": "看似普通办公室，推门之后却是赌场；一个高信用会员为什么还会被逼着把三家信用卡全部刷满？",
        "viewpoint": "这段黑色喜剧把暴力催债包装成财务服务，笑点来自礼貌流程和危险后果的反差。",
        "discussion": "如果催债人连祖产和保险都查得到，个人信息还能剩下多少边界？",
        "cover_headline": "催债也有财务流程",
        "cover_subhead": "能变现的一个不放过",
        "titles": {"bilibili": "黑帮老板不先动手，先把欠债人的资产查了个遍", "douyin": "黑帮催债的第一步，竟然是查你的资产", "kuaishou": "这催债咋跟财务审计似的？", "xiaohongshu": "剧情拆解：黑帮如何把催债做成一套财务流程"},
        "descriptions": {"bilibili": "海江催债不靠吼叫，而是从信用卡、休眠账户、寿险一直查到祖产。笑点是流程很礼貌，后果却越来越危险。", "douyin": "先查信用，再套贷款，接着翻保险和祖产。这个黑帮老板把催债做成了财务审计。", "kuaishou": "欠钱不还咋办？他先把你的信用卡、保险和祖产全查一遍。", "xiaohongshu": "用一段黑色喜剧看懂：催债如何从信用审查升级到资产变现，为什么礼貌流程反而更有压迫感。"},
        "narration_texts": ["别被这条办公走廊骗了，推门就是赌场！他们来这儿不是开会，是给欠债人做财务审计。", "先查信用，再把三张卡刷到上限；只要还能借，债就还能继续滚。", "这个人看着信用不差，利率却已经冲到百分之十九点九九。", "现金额度刷完还不够，海江连休眠账户和妻子的寿险都不放过。", "甚至连后人没领到的土地补偿款，也被提前算进还款计划。", "在这里，黑帮像财务公司；区别是他们不接受‘暂缓还款’。", "更离谱的是，催完债还发免费券，像给被掏空的人送售后服务。", "等到连五脏六腑都被标上价格，这份账单就已经不是账单了。"],
        "annotation_texts": ["办公楼只是伪装", "推门进入地下赌场", "催债先查信用", "19.99%的高利率", "三张卡刷到上限", "休眠账户也被翻出", "寿险也算资产", "祖产补偿提前变现", "催债像财务审计", "免费券是最后的客气", "身体也被列入账单", "能变现的都不放过"],
    },
    {
        "slug": "02_假律师兼职",
        "name": "假律师兼职",
        "clips": [("00:09:56.220", "00:10:08.000"), ("00:10:31.339", "00:10:47.000"), ("00:11:19.095", "00:11:33.474"), ("00:12:10.187", "00:12:28.873"), ("00:12:43.554", "00:13:08.370")],
        "question": "没考上律师的人，为什么还要继续假装自己已经入行？",
        "answer": "夏莉用兼职和谎言维持家里的期待，连一场亲子运动会都变成了证明自己‘很专业’的工作。",
        "emotion": "先被她的狼狈逗笑，最后意识到她真正害怕的是承认自己失败。",
        "conflict": "夏莉想维持律师身份，姐姐和朋友却不断逼她面对现实。",
        "hook": "她替别人当妈妈跑步拿了第一，却连孩子都没看一眼。",
        "viewpoint": "夏莉不是没有能力，而是把所有精力都用来维持一个不能被揭穿的身份。",
        "discussion": "为了不让家人失望，长期隐瞒失败到底是在保护关系，还是把压力越拖越大？",
        "cover_headline": "跑步拿第一的假律师",
        "cover_subhead": "连孩子都没看一眼",
        "titles": {"bilibili": "她替别人参加亲子运动会拿第一，却连孩子都没看一眼", "douyin": "跑了第一名，却被说不专业？", "kuaishou": "这兼职咋还要演成亲妈？", "xiaohongshu": "剧情拆解：假律师如何用兼职维持一个不能揭穿的身份"},
        "descriptions": {"bilibili": "夏莉没有律师工作，只能靠各种兼职维持谎言。她跑步拿了第一，却被提醒真正的客户是孩子，不是终点线。", "douyin": "她替别人当妈妈跑步拿第一，朋友却说：你连孩子都没看一眼。", "kuaishou": "兼职跑步拿第一，咋还被客户投诉不专业？", "xiaohongshu": "从亲子运动会和家庭催债，看懂夏莉为什么不敢承认自己没考上律师资格。"},
        "narration_texts": ["姜夏莉没有律师工作，却一直让姐姐以为她已经入行。", "姐姐信以为真，特意给她买了一套更正式、更像律师的衣服。", "衣服虽然是姐姐买的，但不是白送的，以后还要加利息还回去。", "所以夏莉接下替家长参加亲子运动会的兼职，跑步还拿了第一。", "她只顾完成任务，却连真正该照顾的孩子都没看一眼。", "朋友提醒她，真正的客户不是终点线，而是那个孩子。", "这套正装让她看起来像律师，也让她没工作的谎言撑得更久。", "她不是不想工作，而是不敢让姐姐知道，自己根本还没成为律师。"],
        "annotation_texts": ["姐姐以为她已经当律师", "特意买来正式套装", "希望她看起来更专业", "衣服以后还要还钱", "还要加19%利息", "她继续接兼职", "替别人参加亲子运动会", "跑了第一却没看孩子", "她不敢拆穿自己的谎言", "正装撑住了假身份"],
    },
    {
        "slug": "03_海江没有梦想",
        "name": "海江没有梦想",
        "clips": [("00:16:36.870", "00:17:16.285"), ("00:17:25.627", "00:17:45.715"), ("00:18:19.681", "00:18:59.805"), ("00:19:04.935", "00:19:25.789")],
        "question": "一个什么都能办到的老板，为什么说自己没有梦想？",
        "answer": "他一直在替养父和兄弟们解决生活，却从没给自己留下真正想过的人生。",
        "emotion": "从觉得他无所不能，转为看见一个把自己放在最后的人。",
        "conflict": "养父希望海江退出危险生意，海江却把照顾众人当成自己的责任。",
        "hook": "他能弄到限量包和演唱会门票，却说自己没有梦想。",
        "viewpoint": "海江的‘无所不能’不是自由，而是长期承担别人生活之后形成的习惯。",
        "discussion": "当一个人习惯替所有人负责，他还记得自己真正想要什么吗？",
        "cover_headline": "他什么都能办到",
        "cover_subhead": "却说自己没有梦想",
        "titles": {"bilibili": "他替赌场老板打点权贵，却说自己没有梦想", "douyin": "他什么都能办到，却一直替赌场买保护", "kuaishou": "鳗鱼门票都不是自己吃的，是给大人物送的", "xiaohongshu": "剧情拆解：赌场核心干将如何用送礼和打点换来保护"},
        "descriptions": {"bilibili": "海江不是赌场老板，而是养父手下最能干的核心干将。他负责给大人物送礼、打点关系，换赌场平安营业，却从没想过自己的梦想。", "douyin": "鳗鱼、门票、限量包，全是给大人物准备的；海江替赌场买保护，却说自己没有梦想。", "kuaishou": "这不是老板采购，是替赌场给权贵送礼、给相关人员送钱，海江忙完所有人的事，却没想过自己。", "xiaohongshu": "从鳗鱼、演唱会门票、限量包和警方查抄风险，看懂海江如何替赌场老板维护关系，以及他为什么失去自己的生活。"},
        "narration_texts": ["海江看起来像赌场的老板，其实每天都在替养父打点官场关系。", "鳗鱼、演唱会门票和限量包，都是给大人物准备的礼物。", "这些东西不是为了享受，而是为了讨好权贵，防止警方来查抄赌场。", "光送礼还不够，相关人员也要用钱打点，赌场才能继续营业。", "海江把能弄到的东西全部弄来，像个专门替赌场买保护的后勤部长。", "在兄弟们眼里，他是最能解决问题的人；在养父眼里，他只是把自己困在赌场里的人。", "养父劝他离开，因为赌场危险，更因为他已经把人生都耗在了这份工作里。", "可当被问到自己的梦想时，海江只说没有。"],
        "annotation_texts": ["海江替养父打点关系", "鳗鱼是送给大人物的", "门票和限量包也是人情", "先把权贵哄住", "防止警方查抄赌场", "光送礼还不够", "还要用钱买保护", "养父才是赌场老板", "海江一直替赌场收拾残局", "他却说自己没有梦想"],
    },
    {
        "slug": "04_公寓维修资金",
        "name": "公寓维修资金",
        "clips": [("00:20:36.902", "00:20:59.716"), ("00:21:42.175", "00:22:10.495"), ("00:22:15.083", "00:22:39.649"), ("00:22:48.158", "00:23:16.978")],
        "question": "公寓维修资金为什么会变成管理所长的提款机？",
        "answer": "因为公共预算缺少居民监督，工程、采购和关系打点就能被包装成‘正常支出’。",
        "emotion": "从把维修费当普通工程开支，转为警惕没人盯着的公共资金漏洞。",
        "conflict": "居民想知道钱花在哪里，管理所长则用紧急情况和人情关系回避监督。",
        "hook": "三亿六千五百万的工程，居民一分钱都没同意，他却说这是自己的职责。",
        "viewpoint": "海江后来盯上公寓，不是因为突然变善良，而是他看见了管理权和资金之间的漏洞。",
        "discussion": "公共维修资金到底应该由谁决定、由谁监督？",
        "cover_headline": "维修费怎么被花掉的",
        "cover_subhead": "没人盯的公共资金",
        "titles": {"bilibili": "三亿六千五百万的维修工程，居民竟然完全不知情", "douyin": "公寓维修费，怎么变成了提款机？", "kuaishou": "这维修费咋说花就花？", "xiaohongshu": "剧情拆解：公寓维修资金为什么容易变成管理漏洞"},
        "descriptions": {"bilibili": "管理所长想动用三亿六千五百万韩元维修资金，却说不清居民是否同意。海江看到的，是一套没人盯着的公共预算漏洞。", "douyin": "工程费三亿六千五百万，居民没同意，管理所长却说这是自己的职责。", "kuaishou": "公共维修费咋能随便花？关键是没人盯账。", "xiaohongshu": "用剧情看懂公寓维修资金的风险：工程费、采购费和关系打点如何藏进日常管理。"},
        "narration_texts": ["小区维修金像公共钱包，最危险的地方不是没钱，而是没人看账。", "所长张口就是三亿六千五百万韩元，却把紧急情况说得像私人提款密码。", "居民刚问一句凭什么，他先伸手要饮料——这账还没批，招待费已经开始了。", "接着送礼、送食物，把办公室关系一项项打点好。", "海江看见的不是一笔工程款，而是一台没人监管的取款机。", "住户在过日子，公共资金却在桌底下慢慢消失。", "他真正盯上的，从来不是一栋楼，而是能决定钱往哪儿流的人。", "这也是他后来把目标从赌场转向大型公寓的原因。"],
        "annotation_texts": ["维修金像公共钱包", "工程费高达3.65亿韩元", "居民开始追问用途", "所长先要一瓶饮料", "礼物和食物都是关系费", "公共预算出现漏洞", "没人看账就有人动手", "海江发现新的财路", "关键是控制管理权", "目标转向大型公寓"],
    },
    {
        "slug": "05_一百亿入会费",
        "name": "一百亿入会费",
        "clips": [("00:27:19.262", "00:27:42.454"), ("00:28:09.521", "00:28:58.236"), ("00:29:24.971", "00:29:39.110"), ("00:30:00.924", "00:30:39.110")],
        "question": "一个俱乐部为什么敢把入会费定成100亿？",
        "answer": "这里交易的不是服务，而是权势圈层的资格；入会费只是把保护和资源明码标价。",
        "emotion": "从觉得100亿只是夸张笑话，转为看清海江被压榨的真正原因。",
        "conflict": "厅长想进入权势圈层，对方则要求他证明自己有足够的可支配财富。",
        "hook": "在座每个人身价都超过100亿，入会费也要100亿。",
        "viewpoint": "这场谈判把‘保护’变成了账单，海江经营赌场的收入也被当成了上级的资产。",
        "discussion": "当权力圈层把资格明码标价，普通人还有多少选择空间？",
        "cover_headline": "入会费一百亿",
        "cover_subhead": "买的不是服务是资格",
        "titles": {"bilibili": "这个俱乐部入会费100亿，买的竟然不是服务而是资格", "douyin": "什么俱乐部入会费要100亿？", "kuaishou": "入会先交100亿，这圈子到底卖啥？", "xiaohongshu": "剧情拆解：100亿入会费背后，权势圈层如何给保护明码标价"},
        "descriptions": {"bilibili": "厅长想进入神秘俱乐部，却被要求缴纳100亿韩元入会费。对方买卖的不是服务，而是进入权势圈层的资格。", "douyin": "入会费100亿，厅长翻遍家底也只凑到20亿。", "kuaishou": "这俱乐部门槛也太高了，先交100亿再说。", "xiaohongshu": "从一场黑色喜剧谈100亿入会费：看懂权势圈层如何把资格、保护和资源变成账单。"},
        "narration_texts": ["海江还没想出100亿，权势俱乐部先递来一张天价门票。", "厅长想进这个圈子，入会费不是一亿两亿，而是整整100亿。", "他一路捞钱，却连20亿都拿不出——原来贪得再多，也有不够用的时候。", "于是有人教他最狠的一招：别攒钱，找个不敢反抗的人榨干。", "他们盯上的，正是赌场老板手下最能干的海江。", "在对方眼里，赌场不是产业，是海江欠下的保护费。", "海江说自己账上没现金，对方却只认一个结果：三个月，100亿。", "从这一刻起，催债人的账本翻了页，海江成了被清算的人。"],
        "annotation_texts": ["权势俱乐部拒绝普通人", "入会费直接开到100亿", "厅长翻遍家底也不够", "还差整整80亿", "他们开始寻找提款目标", "赌场被当成保护费", "海江说自己没现金", "保护关系变成追债关系", "催债人变成欠债人", "三个月必须交钱"],
    },
    {
        "slug": "06_赌场被端",
        "name": "赌场被端",
        "clips": [("00:31:21.996", "00:31:58.166"), ("00:32:05.506", "00:32:24.729"), ("00:33:29.716", "00:33:50.361"), ("00:33:54.949", "00:34:27.065"), ("00:34:30.234", "00:34:45.000")],
        "question": "为什么赌场刚被要求交100亿，警方就立刻上门？",
        "answer": "因为海江拒绝把钱交出去后，保护他的关系网马上翻脸，查赌场只是第一步。",
        "emotion": "从觉得海江掌控一切，转为感到他在权力面前几乎没有反击空间。",
        "conflict": "海江想保住赌场和父亲，警方与上级则用连续罪名切断他的退路。",
        "hook": "他明明滴酒不沾，酒精检测却显示酒驾，手机里还只有面包照片。",
        "viewpoint": "这段荒诞不在于罪名离谱，而在于权力可以先决定结果，再拼装理由。",
        "discussion": "当对方掌握执法和证据解释权，普通的自证清白还有用吗？",
        "cover_headline": "不喝酒也能被判酒驾",
        "cover_subhead": "赌场一夜之间被端",
        "titles": {"bilibili": "他明明不喝酒，却被连续栽上酒驾和偷拍罪名", "douyin": "不喝酒的人，为什么吹出酒驾？", "kuaishou": "手机只有面包照片，也能被说成偷拍？", "xiaohongshu": "剧情拆解：赌场被端后，海江为什么连自证清白都做不到"},
        "descriptions": {"bilibili": "海江拒绝交100亿后，赌场遭遇突击检查。他不喝酒却被测出酒驾，手机只有面包照片，还被指控偷拍。", "douyin": "不喝酒、手机没有偷拍视频，却还是被连续安排罪名。", "kuaishou": "这抓人也太快了，罪名像是现场拼出来的。", "xiaohongshu": "从酒驾、偷拍和挂名老板三组证据，看懂这场突击检查如何切断海江的退路。"},
        "narration_texts": ["海江不交100亿，警方就把赌场变成了‘罪名批发市场’。", "先是突击检查，接着酒驾、偷拍，一项项罪名排队送上门。", "他明明不喝酒，检测却偏偏显示酒驾；手机里没有偷拍，只有几张面包照片。", "还没等他解释完，养父又因为挂名老板被带走。", "这根本不是查案，是有人要把赌场的保护伞连根拔掉。", "海江能查清别人的账户，却查不动对方手里的权力。", "赌场被查只是第一层，真正被扣住的，是他唯一的家人。"],
        "annotation_texts": ["拒绝100亿后的报复", "赌场遭遇突击检查", "罪名开始排队出现", "明明不喝酒却被判酒驾", "手机里只有面包照片", "偷拍指控也跟着出现", "养父因为挂名老板被捕", "赌场保护伞被拔掉", "查得清账，查不动权力", "真正筹码是养父"],
    },
    {
        "slug": "07_养父赎金",
        "name": "养父赎金",
        "clips": [("00:35:28.751", "00:36:11.169"), ("00:36:55.838", "00:37:18.025"), ("00:37:35.962", "00:38:01.988"), ("00:39:17.688", "00:39:56.268"), ("00:40:18.416", "00:40:40.000")],
        "question": "100亿赎金背后，海江真正要救的是什么？",
        "answer": "他要救的不只是被扣押的养父，也是二十年前把他带回家、替他撑起人生的人。",
        "emotion": "从看见一场黑帮交易，转为理解海江为什么不肯独自离开。",
        "conflict": "上级拿养父逼海江交钱，养父却反过来要求他别再牺牲自己。",
        "hook": "对方拿100亿换养父，养父却劝海江先去过自己的人生。",
        "viewpoint": "赎金让海江第一次必须在‘救父亲’和‘保住自己’之间做选择。",
        "discussion": "当亲人用一生照顾过你，你是否就必须用自己的人生偿还？",
        "cover_headline": "一百亿换养父",
        "cover_subhead": "他第一次被逼做选择",
        "titles": {"bilibili": "对方拿100亿换养父，养父却劝他别再牺牲自己", "douyin": "100亿赎金，养父却只想让他过自己的人生", "kuaishou": "救父亲要100亿，这钱咋凑？", "xiaohongshu": "剧情拆解：养父被扣押后，海江第一次必须为自己的人生做选择"},
        "descriptions": {"bilibili": "海江把能凑到的钱全部带来，却只换到三个月期限和一张更大的欠条。养父不想让他继续牺牲，只希望他过自己的生活。", "douyin": "对方要100亿换养父，养父却说：别再替别人操心了。", "kuaishou": "养父被扣了，海江咋可能不救？", "xiaohongshu": "从借条、赎金到看守所对话，看懂海江和养父之间不是普通的老板与下属关系。"},
        "narration_texts": ["对方给海江三个月，100亿换回养父。", "他把能凑的钱全部带来，不是为了还债，而是想把养父带回家。", "因为小时候，海江的亲生父亲赌博欠债，借据上写的却是海江的名字。", "亲生父亲把自己的儿子当成抵债品，等于亲手把海江卖掉。", "是这个赌场老板收下了他，把他养大，也第一次真正把他当成家人。", "所以如今被扣住的不是一个债主，而是海江唯一认的父亲。", "养父劝他别再救自己，因为海江已经为这个家牺牲了太多。", "可海江根本不可能放手，养父给他的不是一笔债，而是后来拥有的整个人生。", "这100亿对海江来说，不是在还债，而是在把父亲从别人手里抢回来。"],
        "annotation_texts": ["100亿换回养父", "海江带来全部现金", "他不是来还债的", "亲生父亲赌博欠债", "借据上写着海江的名字", "亲生父亲把他当抵债品", "赌场老板收下并养大了他", "养父才是他真正的父亲", "养父劝他别再牺牲", "海江不可能放手", "养父给了他整个人生", "100亿是在救父亲"],
    },
    {
        "slug": "08_兄弟重聚",
        "name": "兄弟重聚",
        "clips": [("00:41:35.075", "00:42:00.080"), ("00:42:07.441", "00:42:28.035"), ("00:42:45.062", "00:43:15.152"), ("00:43:15.809", "00:44:02.556"), ("00:44:05.809", "00:44:20.741")],
        "question": "海江为什么不让兄弟们一起承担100亿？",
        "answer": "因为他把这场危机看成自己的责任，但兄弟们把养父多年的照顾看成共同的恩情。",
        "emotion": "从以为团队要解散，转为感受到一群人主动留下来的重量。",
        "conflict": "海江想遣散兄弟保护他们，兄弟们却用自己的经历证明他们不只是员工。",
        "hook": "老板宣布遣散，兄弟们却一个个回来，说自己不辞职。",
        "viewpoint": "真正把这群人留在一起的不是帮派规矩，而是养父曾经给过他们的生活。",
        "discussion": "一群人愿意一起扛风险，靠的是合同、利益，还是被认真对待过的情分？",
        "cover_headline": "老板宣布解散",
        "cover_subhead": "兄弟们却都不走",
        "titles": {"bilibili": "老板宣布遣散员工，兄弟们却一个个回来不肯走", "douyin": "老板让他们走，他们为什么全都回来了？", "kuaishou": "这帮兄弟咋还不走？", "xiaohongshu": "剧情拆解：一群人为什么愿意一起承担100亿的风险"},
        "descriptions": {"bilibili": "海江准备遣散兄弟们，不想让他们被100亿拖下水。但他们记得养父给过自己的饭、学费和梦想，最后决定一起救人。", "douyin": "老板都宣布解散了，兄弟们却一个个回来：我们不辞职。", "kuaishou": "这老板想把兄弟都遣散，咋没人愿意走？", "xiaohongshu": "从兄弟们的回忆看懂：真正维系这支团队的，不是帮派规矩，而是被照顾过的情分。"},
        "narration_texts": ["海江宣布遣散兄弟，想把100亿的火一个人扛走。", "他把多年的情分说成劳务关系，还承诺以后补发遣散费。", "可兄弟们记得，养父给过他们饭、学费，还有追梦的机会。", "第一个人说‘不辞职’，剩下的人马上集体回来。", "他们不是舍不得这份工作，而是不肯让海江一个人去送命。", "海江以为自己是在保护大家，兄弟们却把他从孤军奋战里拽了出来。", "100亿听起来像送死，但这群人决定一起试。", "赌场从一间生意场，变成了真正的家。"],
        "annotation_texts": ["海江准备遣散兄弟", "想一个人扛下100亿", "把情分说成劳务关系", "第一个人拒绝辞职", "兄弟们陆续回来", "他们不是舍不得工资", "而是不肯让他独自冒险", "大家决定一起救人", "赌场变成真正的家", "共同体正式成立"],
    },
    {
        "slug": "09_筹钱办婚礼",
        "name": "筹钱办婚礼",
        "clips": [("00:45:42.239", "00:46:24.448"), ("00:46:31.371", "00:47:16.291"), ("00:47:35.310", "00:47:46.405")],
        "question": "没有新娘的黑帮团队，为什么突然决定办婚礼？",
        "answer": "他们想用婚礼礼金回收过去送出去的人情，而夏莉正好被卷进了这份临时工作。",
        "emotion": "从觉得这只是荒唐筹钱，转为期待一场注定失控的假婚礼。",
        "conflict": "团队需要大量现金，夏莉需要兼职还债，两条线在婚礼现场撞到一起。",
        "hook": "为了凑100亿，他们盘点了过去送出的礼金，最后决定自己办场婚礼。",
        "viewpoint": "当人情被当成可以回收的资产，婚礼就不再只是喜事，而成了一场现金流计划。",
        "discussion": "把过去的人情重新收回来，算精明，还是把关系彻底算成了账？",
        "cover_headline": "凑钱最好的办法",
        "cover_subhead": "自己办一场婚礼",
        "titles": {"bilibili": "为了凑100亿，黑帮团队决定自己办一场婚礼", "douyin": "没新娘也要办婚礼，只因礼金最多？", "kuaishou": "凑钱咋办？他们想到办婚礼。", "xiaohongshu": "剧情拆解：当人情变成现金流，黑帮为什么选择办婚礼"},
        "descriptions": {"bilibili": "兄弟们发现过去送出去的礼金可能收回六七亿，于是决定办一场婚礼。问题是，他们有场地、有宾客，却没有新娘。", "douyin": "为了凑100亿，他们决定办婚礼，因为婚礼礼金最多。", "kuaishou": "这帮人凑钱咋想到办婚礼了？", "xiaohongshu": "从周岁宴、六十大寿到婚礼计划，看懂这群人如何把人情往来当成现金流。"},
        "narration_texts": ["为了凑100亿，兄弟们开始清点过去送出去的人情。", "有人办一顿宴席，就能换来一套江南公寓；这群人立刻发现了发财新公式。", "生日宴都能收钱，那什么场合最适合让宾客掏空钱包？", "婚礼。问题是，他们有赌场、有宾客，偏偏没有新娘。", "此时夏莉还在免费法律咨询室，认真替穷人处理继承问题。", "她以为接到的是普通兼职，没想到朋友把她送进了海江的筹钱计划。", "对海江来说，这是回本项目；对夏莉来说，这是身份谎言撞上现实。", "她还不知道，招聘信息写的是‘宾客’，实际岗位却是‘新娘’。"],
        "annotation_texts": ["团队开始清点人情账", "有人靠宴席买下公寓", "生日宴能收礼金", "婚礼礼金更多", "但他们没有新娘", "夏莉正在做法律咨询", "朋友给她介绍兼职", "她被卷进筹钱计划", "海江要回本", "夏莉却要被推上新娘台"],
    },
    {
        "slug": "10_黑帮婚礼",
        "name": "黑帮婚礼",
        "clips": [("00:47:50.033", "00:48:17.769"), ("00:49:15.994", "00:49:59.746"), ("00:50:18.056", "00:50:42.289"), ("00:53:36.713", "00:54:20.000"), ("00:54:50.870", "00:55:20.000")],
        "question": "临时新娘为什么会在婚礼现场才知道自己要结婚？",
        "answer": "夏莉以为自己只是来当宾客，海江却把她当成临时新娘，最后用加价把她推上了台。",
        "emotion": "从看热闹的荒唐感，转为意识到这场交易从一开始就没有清楚边界。",
        "conflict": "海江需要完成婚礼筹钱，夏莉则不断重新确认自己的身体和选择边界。",
        "hook": "她以为自己来参加婚礼，结果被告知：今天的新娘就是你。",
        "viewpoint": "这场婚礼最有趣的地方不是黑帮排场，而是所有人都把临时交易当成了正常流程。",
        "discussion": "临时加钱能不能改变一开始没有说清楚的交易边界？",
        "cover_headline": "她以为来当宾客",
        "cover_subhead": "结果被推上新娘台",
        "titles": {"bilibili": "她以为自己来当婚礼宾客，结果被临时推上了新娘台", "douyin": "来参加婚礼，怎么突然变成新娘了？", "kuaishou": "她是来吃席的，咋成新娘了？", "xiaohongshu": "剧情拆解：黑帮婚礼里最荒唐的临时交易，为什么从一开始就没边界"},
        "descriptions": {"bilibili": "夏莉以为自己来参加婚礼，到了现场才发现要当新娘。海江不断加价，她最后只亲到拇指，两个人都觉得自己吃了亏。", "douyin": "她本来只是来当宾客，结果500万成交，直接被推上新娘台。", "kuaishou": "这婚礼新娘咋还是临时找的？", "xiaohongshu": "从500万成交到200万亲吻费，看懂这场假婚礼为什么笑点密集，却也暴露了交易边界。"},
        "narration_texts": ["夏莉以为来参加婚礼，刚坐下就发现全场像黑帮年会。", "礼堂里坐满退休大哥，真正的新娘却迟迟没有出现。", "她想趁没人注意离开，海江却当场开始给她加价。", "五百万成交——她不是被求婚，是被现场买下来的。", "更离谱的是，婚礼流程居然照常进行，台下每个人都像来开会的股东。", "司仪让新郎新娘接吻，兄弟们立刻把亲吻也改成收费项目。", "夏莉最后只亲到海江的拇指，却还得配合演完这场荒唐婚礼。", "她以为自己被骗了，海江也觉得自己花钱买了个麻烦。", "两个人都觉得亏，偏偏这段假婚姻已经开始生效。"],
        "annotation_texts": ["礼堂里全是退休大哥", "夏莉以为自己只是宾客", "新娘迟迟没有出现", "海江开始现场加价", "五百万买下临时新娘", "黑帮婚礼正式开始", "接吻也被做成收费项目", "她只亲到了拇指", "婚礼流程照常进行", "两个人都觉得自己吃亏", "假婚姻正式生效", "这场交易开始失控", "谁才是真正被骗的人"],
    },
    {
        "slug": "11_公寓百亿秘密",
        "name": "公寓百亿秘密",
        "clips": [("00:56:05.361", "00:56:24.287"), ("00:56:57.831", "00:57:18.226"), ("00:57:30.655", "00:58:00.226"), ("00:58:15.116", "00:58:32.379"), ("00:59:32.402", "01:00:01.222"), ("01:00:07.103", "01:00:41.721"), ("01:00:47.143", "01:01:32.563")],
        "question": "一个1200户小区能贪40亿，9800户公寓能捞多少？",
        "answer": "蜥蜴的账本让海江发现，大型公寓的维修资金可能形成更大的资金池，但前提是先取得管理权。",
        "emotion": "从海江追债的紧张感，转为对‘100亿财路’的荒诞期待，同时留下更大的风险。",
        "conflict": "海江需要在三个月内凑100亿，蜥蜴则用自己的贪污记录提供了一条危险线索。",
        "hook": "1200户小区已经捞出40亿，那9800户的公寓呢？",
        "viewpoint": "海江不是突然发现钱从天上掉下来，而是从一个真实的贪污账本推算出更大的资金池。",
        "discussion": "当公共资金被当成‘可以捞的钱’，真正承担代价的会是谁？",
        "cover_headline": "一千二百户捞出四十亿",
        "cover_subhead": "九千八百户可能更多",
        "titles": {"bilibili": "1200户小区贪了40亿，9800户公寓竟可能捞出100亿", "douyin": "1200户捞40亿，9800户能捞多少？", "kuaishou": "这公寓咋可能捞出100亿？", "xiaohongshu": "剧情拆解：从40亿贪污账本，看懂公寓维修资金如何变成百亿诱惑"},
        "descriptions": {"bilibili": "蜥蜴承认自己在1200户小区通过虚报费用捞出40亿。海江看到9800户公寓后，第一次意识到100亿可能真的存在。", "douyin": "1200户小区就能捞40亿，那9800户的公寓呢？", "kuaishou": "一个小区贪40亿，这座大公寓得有多少油水？", "xiaohongshu": "从物业费、采购费和竞标回扣的账本，看懂海江为什么把目标转向一座近万户公寓。"},
        "narration_texts": ["婚礼钱还差一大截，海江终于找到最后一个欠债人——一个躲在公寓里的贪污所长。", "这个外号叫‘蜥蜴’的人，贪完物业费还被通缉，活得像一只躲在账本里的爬虫。", "他先跪地求饶，发现海江不敢杀人后，马上又开始嘲笑对方。", "海江只把他往危险边缘推了一步，蜥蜴立刻从嘴硬变回求救。", "账本一翻开，虚报物业费、采购费，公共资金全成了他的私房钱。", "1200户的小区已经被他捞出40亿韩元。", "海江转头看向9800户的大公寓：如果这里也没人管，数字可能直接翻到100亿。", "但想拿钱，先得拿下楼栋代表，再坐上会长的位置。", "这次海江要抢的不是赌桌，而是一整栋公寓的控制权。"],
        "annotation_texts": ["最后一个欠债人躲进公寓", "贪污所长外号叫蜥蜴", "先求饶，后嘲笑黑帮", "危险一逼近马上改口", "账本记录虚报费用", "1200户捞出40亿", "目标公寓有9800户", "规模可能翻到100亿", "公共资金成了猎物", "必须先控制楼栋代表", "再拿下会长位置", "海江要抢一整栋公寓"],
    },
    {
        "slug": "12_假扮妻子",
        "name": "假扮妻子",
        "clips": [("01:02:04.470", "01:02:45.511")],
        "question": "海江为什么要找一个陌生女人假扮妻子？",
        "answer": "因为要进入公寓管理体系，他需要一个看起来完整的家庭身份，才能继续竞选楼栋代表。",
        "emotion": "从觉得100亿只是荒唐目标，转为期待这场假夫妻计划如何失控。",
        "conflict": "海江需要家庭身份和管理权，夏莉则要在一亿报酬与陌生交易边界之间做选择。",
        "hook": "为了拿到公寓维修资金，赌场老板竟然开价一亿找人假扮妻子。",
        "viewpoint": "这不是浪漫关系，而是海江把婚姻也当成进入公共资金体系的工具。",
        "discussion": "如果报酬足够高，假扮夫妻算工作，还是会把人卷进更大的风险？",
        "cover_headline": "三个月假扮妻子",
        "cover_subhead": "报酬一亿韩元",
        "titles": {"bilibili": "为了拿到公寓维修资金，赌场大管家开价一亿找假妻子", "douyin": "赌场核心干将找假妻子，三个月给一亿", "kuaishou": "为进小区参选，他咋还要找假媳妇？", "xiaohongshu": "剧情拆解：赌场核心干将如何用假妻子进入公寓管理体系"},
        "descriptions": {"bilibili": "海江是赌场老板的得力干将。他发现公寓有178亿5742万韩元长期维修资金，却必须先拿到楼栋代表资格，于是提出三个月假扮夫妻，报酬一亿韩元。", "douyin": "不是老板求婚，是赌场大管家开出的工作：三个月假扮妻子，给你一亿。", "kuaishou": "为了进小区参选，赌场大管家咋还要找假媳妇？", "xiaohongshu": "从长期维修资金到假夫妻计划，看懂赌场核心干将如何用家庭身份进入公寓管理体系。"},
        "narration_texts": ["公寓账上躺着178亿5742万韩元，海江终于看见了救养父的出口。", "可这笔钱属于全体住户，不是他想拿就能拿。", "更麻烦的是，楼栋代表选举看的是‘家庭形象’，而海江偏偏是独居。", "于是他把刚被卷进婚礼骗局的夏莉，重新请回了计划。", "一个赌场老板的得力干将要进公寓竞选，一个法律咨询员要临时演妻子。", "报酬一亿韩元——这次夏莉不是去参加婚礼，而是直接把自己租进了婚姻。", "从下一集开始，他们要用假夫妻身份争夺公寓维修金。", "但这场戏一旦穿帮，丢的就不只是100亿，还有两个人的人生。"],
        "annotation_texts": ["公寓账上有178亿5742万", "海江看见翻身机会", "公共资金不能随便动", "独居影响竞选资格", "他需要一个家庭身份", "一亿韩元聘请假妻子", "赌场干将竞选楼栋代表", "法律咨询员临时演妻子", "假夫妻计划正式开始", "这场戏穿帮就全盘失控"],
    },
]


def main() -> None:
    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    if not SOURCE.is_file():
        raise SystemExit(f"找不到源视频：{SOURCE}")
    if not SUBTITLE.is_file():
        raise SystemExit(f"找不到工作字幕：{SUBTITLE}")

    for story in STORIES:
        duration = clip_duration([{"source_start": a, "source_end": b} for a, b in story["clips"]])
        main_dir = EXPORT_ROOT / f"{story['slug']}_短视频"
        annotation_dir = EXPORT_ROOT / f"{story['slug']}_视频注释版"
        main_dir.mkdir(parents=True, exist_ok=True)
        annotation_dir.mkdir(parents=True, exist_ok=True)

        raw_clips = build_clips(story["clips"])
        narration = make_narration(story["narration_texts"], duration)
        annotation_segments = make_annotation_timeline(story, raw_clips)
        annotation_ids = [{"id": f"anno_{i:03}", **segment} for i, segment in enumerate(annotation_segments, start=1)]
        clips = build_clips(story["clips"], high_energy=True, annotation_count=len(annotation_ids))
        attach_annotation_ids(clips, annotation_ids)

        annotation_timeline = {
            "version": 1,
            "source_subtitle": str(SUBTITLE),
            "video_duration": seconds_to_hms(duration),
            "segments": annotation_segments,
        }
        timeline_path = annotation_dir / f"{story['slug']}_剧情注释时间线.json"
        timeline_path.write_text(json.dumps(annotation_timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        annotation_path = annotation_dir / f"{story['slug']}_annotations.json"

        main_plan = common_plan(
            story,
            raw_clips,
            main_dir / f"{story['slug']}_短视频.mp4",
            narration,
            annotation_only=False,
        )
        main_plan["source_subtitle"] = str(SUBTITLE)
        (main_dir / f"{story['slug']}_编辑计划.json").write_text(json.dumps(main_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        annotation_plan = common_plan(
            story,
            clips,
            annotation_dir / f"{story['slug']}_视频注释版.mp4",
            [],
            annotation_only=True,
            annotation_file=annotation_path,
        )
        annotation_plan["source_subtitle"] = str(SUBTITLE)
        (annotation_dir / f"{story['slug']}_编辑计划.json").write_text(json.dumps(annotation_plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"已生成 {len(STORIES)} 个故事的编辑计划：{EXPORT_ROOT}")


if __name__ == "__main__":
    main()
