import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from news import candidates, fetch_text, mark_used
from script_gen import generate
from tts import synth_lines
from render import render

os.makedirs("output", exist_ok=True); tmp = "tmp"; os.makedirs(tmp, exist_ok=True)

print("1/5 fetching news")
items = candidates()[:8]
if not items: raise SystemExit("No news items found (feeds empty or all used)")
for it in items: it["text"] = fetch_text(it)
print(f"   {len(items)} stories")

print("2/5 writing script")
data = generate(items)
lines = [l for l in data.get("lines", []) if l.get("text")]
if not lines: raise SystemExit(f"Bad script JSON: {data}")
for l in lines: l.setdefault("visual", "india city")
chosen = items[min(max(int(data.get("index", 0)), 0), len(items) - 1)]
print("   headline:", data.get("headline"))

print("3/5 voice"); audio, times = synth_lines(lines, tmp)
name = f"output/short_{int(time.time())}"

print("4/5 render"); render(data.get("headline", chosen["title"]), lines, audio, times, name + ".mp4", tmp)

print("5/5 metadata")
json.dump({"title": data.get("title", chosen["title"]),
           "description": data.get("description", "") + f"\n\nस्रोत: {chosen['link']}",
           "source": chosen["link"]}, open(name + ".json", "w"), ensure_ascii=False, indent=2)
mark_used(chosen["link"])
print("done", name, f"({times[-1][1]:.1f}s)")
