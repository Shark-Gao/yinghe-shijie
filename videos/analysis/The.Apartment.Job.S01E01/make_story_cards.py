from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent / "cards"
OUT.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    candidates = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]
        if bold
        else [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]
    )
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    raise SystemExit("找不到中文字体")


W, H = 1920, 1080
BG = (8, 16, 30)
PANEL = (17, 31, 52)
WHITE = (241, 244, 247)
MUTED = (167, 183, 201)
AMBER = (229, 176, 92)
RED = (210, 75, 68)
BLUE = (79, 160, 210)


def base(title: str, kicker: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    for y in range(H):
        t = y / H
        color = tuple(round(BG[i] * (1 - t) + (18, 38, 60)[i] * t) for i in range(3))
        draw.line((0, y, W, y), fill=color)
    draw.rectangle((78, 76, 1842, 1004), outline=(45, 72, 100), width=3)
    draw.text((120, 116), kicker, font=font(30, True), fill=AMBER)
    draw.text((120, 180), title, font=font(62, True), fill=WHITE)
    draw.line((120, 284, 1800, 284), fill=(50, 84, 116), width=3)
    return image, draw


def relationship_card() -> None:
    image, draw = base("这场债，不只是 100 亿", "人物关系 / 素材已核验")
    # relationship nodes
    nodes = [
        (160, 410, 520, 620, "朴海江", "主角 / 公司老板", BLUE),
        (700, 410, 1060, 620, "朴勇万", "养父 / 被扣押", AMBER),
        (1240, 410, 1760, 620, "孙部长", "索要 100 亿", RED),
    ]
    for x1, y1, x2, y2, title, sub, color in nodes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=PANEL, outline=color, width=4)
        draw.text((x1 + 34, y1 + 42), title, font=font(48, True), fill=WHITE)
        draw.text((x1 + 34, y1 + 122), sub, font=font(30), fill=MUTED)
    draw.line((520, 515, 700, 515), fill=AMBER, width=7)
    draw.polygon([(700, 515), (670, 497), (670, 533)], fill=AMBER)
    draw.text((544, 450), "养父关系", font=font(27, True), fill=AMBER)
    draw.line((1060, 515, 1240, 515), fill=RED, width=7)
    draw.polygon([(1240, 515), (1210, 497), (1210, 533)], fill=RED)
    draw.text((1074, 450), "扣押换钱", font=font(27, True), fill=RED)
    draw.text((150, 790), "主角先把兄弟们推开，准备一个人承担这笔债。", font=font(36, True), fill=WHITE)
    draw.text((150, 858), "但这群人真正的关系，早就超过了老板和员工。", font=font(32), fill=MUTED)
    image.save(OUT / "relationship_card.png")


def analysis_card() -> None:
    image, draw = base("主角面对的不是一个数字", "剧情分析 / 三个已出现的事实")
    rows = [
        ("100 亿", "三个月内交齐，才能换回养父", RED),
        ("10 亿+", "兄弟们这些年已经被敲走的金额", AMBER),
        ("一条选择", "独自承担，还是让所有人一起冒险", BLUE),
    ]
    y = 380
    for number, text, color in rows:
        draw.rounded_rectangle((150, y, 1770, y + 150), radius=18, fill=PANEL, outline=(46, 75, 105), width=2)
        draw.text((210, y + 38), number, font=font(48, True), fill=color)
        draw.text((650, y + 52), text, font=font(34), fill=WHITE)
        y += 190
    draw.text((150, 930), "这些事实把“救父”变成了所有人的共同选择。", font=font(34, True), fill=WHITE)
    image.save(OUT / "analysis_card.png")


def closing_card() -> None:
    image, draw = base("他们决定一起扛", "阶段性结果 / 本集冲突落点")
    draw.rounded_rectangle((220, 390, 1700, 680), radius=30, fill=PANEL, outline=AMBER, width=4)
    draw.text((430, 470), "不是老板和员工", font=font(52, True), fill=WHITE)
    draw.text((490, 570), "而是一起救人的家人", font=font(52, True), fill=AMBER)
    draw.text((210, 810), "一百亿未解，但他们决定一起扛。你会怎么选？", font=font(34), fill=MUTED)
    image.save(OUT / "closing_card.png")


if __name__ == "__main__":
    relationship_card()
    analysis_card()
    closing_card()
