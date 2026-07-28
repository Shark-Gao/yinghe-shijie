import cv2

video_path = r"L:\workspace\yinghe-shijie\videos\raw\南海争的真不只是岛.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS) or 23.98
length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
hits = []
sec = 0
frame_index = 0
while frame_index <= length:
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(sec * fps))
    ok, frame = cap.read()
    if not ok:
        break
    small = cv2.resize(frame, (640, 360))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    boxes = face.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(28, 28))
    large = [b for b in boxes if b[2] * b[3] >= 900]
    if large:
        hits.append(sec)
    sec += 1
    frame_index = int(sec * fps)
cap.release()
runs = []
for sec in hits:
    if not runs or sec > runs[-1][1] + 1:
        runs.append([sec, sec])
    else:
        runs[-1][1] = sec
output = [f"hits {len(hits)}"]
for start, end in runs:
    output.append(f"{start:.0f}-{end + 1:.0f}")
print("\n".join(output))
open(r"L:\workspace\yinghe-shijie\outputs\tmp_detect_people.txt", "w", encoding="utf-8").write("\n".join(output) + "\n")
