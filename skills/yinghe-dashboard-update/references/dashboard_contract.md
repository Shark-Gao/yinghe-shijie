# Dashboard data contract

## Baseline

Data cutoff: 2026-07-17. These values are directional benchmarks, not universal platform averages.

| Platform | Period | Plays / views | Completion | Interaction | Followers | Notes |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 小红书 | 近30日 | 5,317观看 | 1.9% | 205赞、159收藏、18分享、6评论 | +70 | 曝光2.4万，封面点击8.5%，平均观看39秒 |
| 抖音 | 近7日 | 5,345播放 | 2.7% | 3.1%互动率 | +29 | 同类完播6.2%，搜索量831 |
| 快手 | 近30日 | 3.9万播放 | 1.4% | 54赞、14评论、0分享 | +18 | 19条作品，近7日获得6243次额外助推 |

## Record schema

`review-history.json` is a JSON array. Every entry uses this shape:

```json
{
  "id": "2026-07-18至2026-07-24-小红书",
  "platform": "小红书",
  "period": "2026-07-18至2026-07-24",
  "plays": 6200,
  "completion": 3.4,
  "interaction": 6.8,
  "followers": 82,
  "note": "将答案提前到前2秒"
}
```

Use `null` for unavailable fields. Store rate fields as percentages without the percent sign.

## Dashboard behavior

Import the JSON file from `app/page.tsx`; seed displayed review records with it, then merge records saved in browser local storage. Do not write screenshots or personal data into the site source.
