---
name: yinghe-dashboard-update
description: Update the 硬核视界 multi-platform review dashboard when the user sends new 小红书、抖音或快手 analytics screenshots or asks to update/review the next data period. Extract verifiable metrics, compare them to the 2026-07-17 baseline, append a structured review record, update the dashboard source, build, and privately redeploy the existing Sites page.
---

# 硬核视界看板更新

Use this workflow whenever the user provides a new set of platform analytics screenshots or asks to add the next review period to the dashboard.

## Source of truth

- Dashboard project: `L:\workspace\yinghe-shijie\web-dashboard`
- Hosted project ID: read `web-dashboard/.openai/hosting.json`; reuse it and never create another site.
- Read [references/dashboard_contract.md](references/dashboard_contract.md) before interpreting or changing data.

## Workflow

1. Read every provided screenshot and transcribe only visible, unambiguous values. Record the backend's original metric name and period. Do not invent a missing rate or normalize unlike periods.
2. Compare the new data with the matching platform baseline in the reference. State that the comparison is directional if the periods or work counts differ.
3. Keep raw records in `web-dashboard/data/review-history.json`. If it does not exist, create `[]`, then refactor the dashboard once to import this file and initialize its history list from it. Do not overwrite the 2026-07-17 baseline.
4. Run `scripts/append_review_record.py` once per platform with verified values. Use `--replace` only when correcting the same platform and period.
5. Update dashboard copy only when the data changes the conclusion; keep unknown values as null and render them as `—`.
6. Follow the `sites-building` and `sites-hosting` skills: run the production build, commit and push the exact source, save a version, and privately redeploy the existing site. Do not make it public without explicit user approval.
7. Report: the main cross-platform conclusion, each platform's largest change, and the refreshed private URL.

## Data entry

Run the append script with one record per platform. `plays`, `completion`, `interaction`, and `followers` are optional; omit unavailable values rather than using zero.

```powershell
python <skill-dir>\scripts\append_review_record.py `
  --file L:\workspace\yinghe-shijie\web-dashboard\data\review-history.json `
  --platform 小红书 --period 2026-07-18至2026-07-24 `
  --plays 6200 --completion 3.4 --interaction 6.8 --followers 82 `
  --note "将答案提前到前2秒"
```

## Guardrails

- Preserve platform-specific terms: 小红书“观看数”、抖音/快手“播放量”并不自动等价。
- Compare complete periods with complete periods; mark early single-work data as provisional.
- Treat completion as duration-sensitive. Do not claim improvement solely because a shorter version has a higher completion rate.
- Keep the first baseline visible and append later cycles; never replace historical records with a new total.
- Keep the dashboard private by default. Ask before changing its audience or access policy.
