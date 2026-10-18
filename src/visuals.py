import glob, os, requests, subprocess
from PIL import Image, ImageDraw, ImageFont
from config import *

def find_font():
    for pat in ["/usr/share/fonts/**/NotoSansDevanagari-Bold.ttf", "/usr/share/fonts/**/NotoSansDevanagari*Bold*.ttf",
                "/usr/share/fonts/**/Mukta*Bold*.ttf", "/usr/share/fonts/**/*Devanagari*.ttf"]:
        f = glob.glob(pat, recursive=True)
        if f: return f[0]
    raise SystemExit("No Devanagari font found (apt install fonts-noto-core)")

def font(size):
    return ImageFont.truetype(find_font(), size, layout_engine=ImageFont.Layout.RAQM)

def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def caption_png(text, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(78); ls = wrap(d, text, f, W - 160); lh = 120
    y0 = 1180
    d.rounded_rectangle((50, y0 - 30, W - 50, y0 + lh * len(ls) + 10), 40, fill=(0, 0, 0, 150))
    for i, l in enumerate(ls):
        x = (W - d.textlength(l, font=f)) / 2
        d.text((x, y0 + i * lh), l, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
    im.save(path)

def header_png(headline, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle((0, 150, W, 330), fill=(200, 0, 20, 235))
    d.rectangle((0, 330, W, 520), fill=(10, 10, 20, 215))
    d.text((50, 175), "ब्रेकिंग न्यूज़", font=font(64), fill=(255, 255, 255))
    f = font(76); ls = wrap(d, headline, f, W - 100)[:2]
    for i, l in enumerate(ls):
        d.text((50, 345 + i * 95), l, font=f, fill=(255, 215, 0))
    d.text((50, 1700), CHANNEL_NAME, font=font(60), fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    im.save(path)

def stock_clip(query, path):
    key = os.getenv("PEXELS_API_KEY")
    if not key: return False
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                         params={"query": query, "orientation": "portrait", "per_page": 5}, timeout=30).json()
        for v in r.get("videos", []):
            files = sorted([f for f in v["video_files"] if f.get("width") and f["width"] >= 720], key=lambda f: f["width"])
            if files:
                open(path, "wb").write(requests.get(files[0]["link"], timeout=120).content); return True
    except Exception: pass
    return False

def scene_video(query, seconds, path, tmp):
    src = f"{tmp}/{os.path.basename(path)}.src.mp4"
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    enc = ["-t", f"{seconds:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", path]
    if stock_clip(query, src):
        vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=brightness=-0.12:saturation=1.1"
        subprocess.run(base + ["-stream_loop", "-1", "-i", src, "-vf", vf] + enc, check=True)
    else:
        subprocess.run(base + ["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0=0x0b1b3a:c1=0x3a0b2a:speed=0.02:d={seconds:.2f}"] + enc, check=True)
