import os, subprocess
from config import *
from visuals import *

def render(headline, lines, audio, times, out, tmp):
    scenes = []; state = {"used": set(), "credits": []}
    for i, (ln, (a, b)) in enumerate(zip(lines, times)):
        p = f"{tmp}/s{i}.mp4"; scene_video(ln["visual"], b - a, p, tmp, state, i, ln.get("visual_fallback", "")); scenes.append(p)
    open(f"{tmp}/c.txt", "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in scenes))
    bg = f"{tmp}/bg.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/c.txt", "-c", "copy", bg], check=True)
    header_png(headline, f"{tmp}/h.png")
    ins = ["-i", bg, "-i", audio, "-i", f"{tmp}/h.png"]; flt = "[0:v][2:v]overlay=0:0[v0];"
    for i, (ln, (a, b)) in enumerate(zip(lines, times)):
        caption_png(ln["text"], f"{tmp}/cap{i}.png"); ins += ["-i", f"{tmp}/cap{i}.png"]
        flt += f"[v{i}][{i+3}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{i+1}];"
    flt = flt.rstrip(";")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", flt, "-map", f"[v{len(lines)}]", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    return state["credits"]
