---
name: yinghe-dashboard-update
description: Update the 硬核视界 multi-platform review dashboard when the user sends new 小红书、抖音或快手 analytics screenshots or asks to update/review the next data period. Extract verifiable metrics, compare them to the baseline, diagnose the 2/5/10-second hook, retention, interaction, saves/shares, and follower conversion, append a structured review record, update the dashboard source, build, and privately redeploy the existing Sites page.
---

# 硬核视界看板更新

Use this workflow whenever the user provides a new set of platform analytics screenshots or asks to add the next review period to the dashboard.

## Source of truth

- Dashboard project: `L:\workspace\yinghe-shijie\web-dashboard`
- Hosted project ID: read `web-dashboard/.openai/hosting.json`; reuse it and never create another site.
- Read [references/dashboard_contract.md](references/dashboard_contract.md) before interpreting or changing data.

## Workflow

1. Read every provided screenshot and transcribe only visible, unambiguous values. Record the backend's original metric name and period. Capture, when available, `2秒留存`, `5秒留存`, `10秒留存`, completion, plays/views, likes, comments, saves, shares, followers, and the platform's interaction rate. Do not invent a missing rate or normalize unlike periods.
2. Compare the new data with the matching platform baseline in the reference. State that the comparison is directional if the periods or work counts differ.
3. Keep raw records in `web-dashboard/data/review-history.json`. If it does not exist, create `[]`, then refactor the dashboard once to import this file and initialize its history list from it. Do not overwrite the 2026-07-17 baseline.
4. Run `scripts/append_review_record.py` once per platform with verified values. Use `--replace` only when correcting the same platform and period.
5. Update dashboard copy only when the data changes the conclusion; keep unknown values as null and render them as `—`. Treat followers as a secondary result. Prefer the diagnosis order `hook → retention → interaction/save/share → follower conversion`; do not call high-play/low-follow content fake without evidence.
6. Follow the `sites-building` and `sites-hosting` skills: run the production build, commit and push the exact source, save a version, and privately redeploy the existing site. Do not make it public without explicit user approval.
7. Report: the main cross-platform conclusion, each platform's largest change, and the refreshed private URL.

## Data entry

Run the append script with one record per platform. `plays`, `completion`, `interaction`, and `followers` are optional; omit unavailable values rather than using zero.

```powershell
python <skill-dir>\scripts\append_review_record.py `
  --file L:\workspace\yinghe-shijie\web-dashboard\data\review-history.json `
  --platform 小红书 --period 2026-07-18至2026-07-24 `
  --plays 6200 --completion 3.4 --interaction 6.8 --followers 82 `
  --hook-2s 38.0 --hook-5s 24.0 --hook-10s 12.0 `
  --likes 205 --comments 6 --saves 159 --shares 18 `
  --note "将答案提前到前2秒"
```

The extra fields are optional. Use them when the platform exposes them; otherwise leave them null. `follow_conversion` may be calculated only when plays/views and new followers refer to the same period and scope.

## Guardrails

- Preserve platform-specific terms: 小红书“观看数”、抖音/快手“播放量”并不自动等价。
- Compare complete periods with complete periods; mark early single-work data as provisional.
- Treat completion as duration-sensitive. Do not claim improvement solely because a shorter version has a higher completion rate.
- Compare 2/5/10-second retention before diagnosing the whole video; if the drop occurs immediately, fix the hook before changing the topic.
- Separate likes, comments, saves, and shares when available. Saves/shares indicate reference or forwarding value; comments may indicate either useful discussion or controversy.
- Use `follow_conversion = new followers / plays or views` only when denominators match. Do not optimize for follower count alone.
- Keep the first baseline visible and append later cycles; never replace historical records with a new total.
- Keep the dashboard private by default. Ask before changing its audience or access policy.
