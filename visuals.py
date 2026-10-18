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

UA = {"User-Agent": "HindiNewsShortsBot/1.0 (educational automation; github actions)"}
import re, random, html as _html
from PIL import ImageFilter

def _clean(t):
    return _html.unescape(re.sub("<[^>]+>", "", t or "")).strip()

def _pexels(query, path):
    key = os.getenv("PEXELS_API_KEY")
    if not key: return None
    r = requests.get("https://api.pexels.com/videos/search", headers={"Authorization": key},
                     params={"query": query, "orientation": "portrait", "per_page": 5}, timeout=30).json()
    for v in r.get("videos", []):
        files = sorted([f for f in v["video_files"] if f.get("width") and f["width"] >= 720], key=lambda f: f["width"])
        if files:
            open(path, "wb").write(requests.get(files[0]["link"], timeout=120).content); return ("video", "Pexels")
    return None

def _pixabay(query, path):
    key = os.getenv("PIXABAY_API_KEY")
    if not key: return None
    r = requests.get("https://pixabay.com/api/videos/", params={"key": key, "q": query, "per_page": 5, "safesearch": "true"}, timeout=30).json()
    for v in r.get("hits", []):
        for size in ("medium", "large", "small"):
            u = v["videos"].get(size, {}).get("url")
            if u:
                open(path, "wb").write(requests.get(u, timeout=120).content); return ("video", "Pixabay")
    return None

def commons_images(query):
    """Real photos from Wikimedia Commons (free, no key)."""
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": query + " filetype:bitmap",
        "gsrnamespace": 6, "gsrlimit": 15, "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1600}).json()
    out = []
    for pg in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = (pg.get("imageinfo") or [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 800: continue
        t = pg.get("title", "").lower()
        if any(x in t for x in ("logo", "flag", "map", "symbol", "icon", "poster", "diagram", "signature", "coat of arms")): continue
        md = ii.get("extmetadata", {})
        credit = f'{_clean(md.get("Artist", {}).get("value", "Unknown"))[:60]} / Wikimedia Commons ({_clean(md.get("LicenseShortName", {}).get("value", "CC"))})'
        out.append({"url": ii.get("thumburl") or ii["url"], "credit": credit, "id": pg.get("title")})
    return out

def openverse_images(query):
    r = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=30,
                     params={"q": query, "page_size": 12, "license_type": "commercial", "mature": "false", "size": "large"}).json()
    return [{"url": x["url"], "credit": f'{_clean(x.get("creator") or "Unknown")[:60]} / {x.get("source", "Openverse")} ({x.get("license", "cc").upper()})',
             "id": x["url"]} for x in r.get("results", [])]

def compose_still(imgpath, out):
    """Blurred full-screen background + sharp photo in the middle (classic news-reel look)."""
    im = Image.open(imgpath).convert("RGB")
    bg = im.copy(); r = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * r) + 1, int(bg.height * r) + 1)).filter(ImageFilter.GaussianBlur(35))
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    canvas = bg.crop((l, t, l + W, t + H)); canvas = Image.eval(canvas, lambda v: int(v * 0.55))
    fr = W / im.width
    if im.height * fr < 900:  # very wide photo -> allow a taller crop so it fills more
        fg = im.resize((int(im.width * 900 / im.height), 900)); l = (fg.width - W) // 2; fg = fg.crop((l, 0, l + W, 900))
    else:
        fg = im.resize((W, int(im.height * fr)))
        if fg.height > 1100: t = (fg.height - 1100) // 2; fg = fg.crop((0, t, W, t + 1100))
    canvas.paste(fg, (0, 560 + (1100 - fg.height) // 2 if fg.height < 1100 else 560))
    canvas.save(out, quality=92)

def still_clip(png, seconds, path, idx):
    n = max(int(seconds * FPS), 2)
    z = f"min(1.0+0.0007*on,1.22)" if idx % 2 == 0 else f"max(1.22-0.0007*on,1.0)"
    vf = f"scale=1620:2880,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", png, "-vf", vf, "-frames:v", str(n),
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", path], check=True)

def _download(url, path):
    r = requests.get(url, headers=UA, timeout=60); r.raise_for_status()
    if len(r.content) < 5000: raise ValueError("tiny image")
    open(path, "wb").write(r.content)

def scene_video(query, seconds, path, tmp, state, idx=0, fallback=""):
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    enc = ["-t", f"{seconds:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-an", path]
    queries = [q for q in (query, fallback, "India") if q]
    # 1) stock video if keys exist
    src = f"{tmp}/{os.path.basename(path)}.src.mp4"
    for q in queries[:2]:
        for fn in (_pexels, _pixabay):
            try:
                if fn(q, src):
                    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=brightness=-0.12:saturation=1.1"
                    subprocess.run(base + ["-stream_loop", "-1", "-i", src, "-vf", vf] + enc, check=True)
                    print(f"  scene {idx}: stock video '{q}'"); return
            except Exception as e:
                print("  stock fail", fn.__name__, str(e)[:120])
    # 2) real photos (Wikimedia Commons, then Openverse) with slow zoom
    for q in queries:
        for fn in (commons_images, openverse_images):
            try:
                for c in fn(q)[:8]:
                    if c["id"] in state["used"]: continue
                    raw, png = f"{tmp}/img{idx}.raw", f"{tmp}/img{idx}.jpg"
                    try:
                        _download(c["url"], raw); compose_still(raw, png)
                    except Exception as e:
                        print("  img fail", str(e)[:100]); continue
                    still_clip(png, seconds, path, idx)
                    state["used"].add(c["id"]); state["credits"].append(c["credit"])
                    print(f"  scene {idx}: photo '{q}' via {fn.__name__}"); return
            except Exception as e:
                print("  search fail", fn.__name__, str(e)[:120])
    # 3) fallback: animated gradient
    print(f"  scene {idx}: gradient fallback")
    subprocess.run(base + ["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0=0x0b1b3a:c1=0x3a0b2a:speed=0.02:d={seconds:.2f}"] + enc, check=True)
