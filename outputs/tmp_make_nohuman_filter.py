from pathlib import Path

kept = [(87.266, 409.466), (558.533, 1028.566), (1028.566, 1346.8)]
people = []
for line in Path(r"L:\workspace\yinghe-shijie\outputs\tmp_detect_people.txt").read_text(encoding="utf-8").splitlines()[1:]:
    if "-" in line:
        start, end = line.split("-", 1)
        people.append((float(start), float(end)))

margin = 1.0
people.append((1325.0, 1334.0))
# 地图动画中还叠有一段主持人转场和历史人物照片，按画面抽检手工剔除。
people.append((570.0, 595.0))
people.append((598.0, 600.0))
people.append((610.0, 615.0))
people.append((628.0, 633.0))
people.append((721.0, 760.0))
people.append((800.0, 817.0))
people.append((824.0, 828.0))
people.append((838.0, 841.0))
# 该地图段含历史人物肖像，连同前后的真人转场一并剔除。
people.append((775.0, 791.0))
people.sort()
base = []
for keep_start, keep_end in kept:
    cursor = keep_start
    for person_start, person_end in people:
        if person_end <= keep_start or person_start >= keep_end:
            continue
        person_start = max(keep_start, person_start)
        person_end = min(keep_end, person_end)
        cut_start = max(keep_start, person_start - margin)
        cut_end = min(keep_end, person_end + margin)
        if cut_start > cursor + 0.08:
            base.append((cursor, cut_start))
        cursor = max(cursor, cut_end)
    if keep_end > cursor + 0.08:
        base.append((cursor, keep_end))

base = [(start, end) for start, end in base if end - start >= 0.25]
late = [(start, end) for start, end in base if start >= 558.0]

def expression(intervals):
    return "+".join(f"between(t,{start:.3f},{end:.3f})" for start, end in intervals)

parts = [
    "[0:v]split=4[basein][late1in][late2in][late3in]",
    f"[basein]select='{expression(base)}',setpts=N/FRAME_RATE/TB,fps=30,format=yuv420p[base]",
    f"[late1in]select='{expression(late)}',setpts=N/FRAME_RATE/TB,fps=30,format=yuv420p[late1]",
    f"[late2in]select='{expression(late)}',setpts=N/FRAME_RATE/TB,fps=30,format=yuv420p[late2]",
    f"[late3in]select='{expression(late)}',setpts=N/FRAME_RATE/TB,fps=30,format=yuv420p[late3]",
    "[base][late1][late2][late3]concat=n=4:v=1:a=0,trim=duration=1109.450,setpts=PTS-STARTPTS[vout]",
]
Path(r"L:\workspace\yinghe-shijie\outputs\tmp_nohuman_filter.txt").write_text(";\n".join(parts), encoding="utf-8")
print(f"base={sum(end - start for start, end in base):.3f} late={sum(end - start for start, end in late):.3f}")
