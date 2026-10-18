import json, os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from news import candidates, fetch_text, mark_used
from script_gen import generate
from tts import synth_lines
from render import render

os.makedirs("output", exist_ok=True); tmp = "tmp"; os.makedirs(tmp, exist_ok=True)
items = candidates()[:8]
for it in items: it["text"] = fetch_text(it)
data = generate(items)
chosen = items[min(int(data.get("index", 0)), len(items) - 1)]
audio, times = synth_lines(data["lines"], tmp)
name = f"output/short_{int(time.time())}"
render(data["headline"], data["lines"], audio, times, name + ".mp4", tmp)
json.dump({"title": data["title"], "description": data["description"] + f"\n\nस्रोत: {chosen['link']}",
           "source": chosen["link"]}, open(name + ".json", "w"), ensure_ascii=False, indent=2)
mark_used(chosen["link"])
print("done", name)
