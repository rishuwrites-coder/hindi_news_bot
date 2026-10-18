import json, os, requests
from config import GEMINI_MODEL
BASE = "https://generativelanguage.googleapis.com/v1beta"
PROMPT = """आप भारतीय न्यूज़ शॉर्ट्स के स्क्रिप्ट राइटर हैं।
नीचे आज की ख़बरों की सूची है। इनमें से सबसे ज़्यादा ट्रेंडिंग/महत्वपूर्ण (राजनीति/भारत प्राथमिकता) ख़बर चुनें और 30-40 सेकंड (लगभग 85-100 शब्द) की हिंदी स्क्रिप्ट लिखें।
नियम: सिर्फ़ दिए गए टेक्स्ट के तथ्य इस्तेमाल करें, कुछ भी अपनी तरफ़ से न जोड़ें। निष्पक्ष, तथ्यात्मक भाषा, बिना भड़काऊ/सांप्रदायिक शब्दों के। पहली लाइन एक तेज़ हुक हो। आख़िरी लाइन में "ऐसी ख़बरों के लिए चैनल फ़ॉलो करें"।
हर लाइन छोटी (8-14 शब्द) हो। केवल JSON लौटाएँ:
{"index": <चुनी ख़बर का नंबर>, "headline": "<=8 शब्द हेडलाइन", "lines": [{"text": "हिंदी लाइन", "visual": "english stock video search keywords 2-3 words"}], "title": "YouTube शीर्षक #Shorts", "description": "विवरण + हैशटैग"}
ख़बरें:
"""
def _models(key):
    """Flash models this key can use, newest first (model names change over time)."""
    names = [os.getenv("GEMINI_MODEL") or ""]
    try:
        r = requests.get(f"{BASE}/models", params={"key": key, "pageSize": 200}, timeout=30).json()
        ok = [m["name"].split("/")[-1] for m in r.get("models", [])
              if "generateContent" in m.get("supportedGenerationMethods", [])
              and "flash" in m["name"]
              and not any(x in m["name"] for x in ("image", "tts", "live", "audio", "thinking", "preview-0", "exp", "robotics", "computer"))]
        names += sorted(ok, key=lambda n: ("lite" in n, [-ord(c) for c in n]))
    except Exception:
        pass
    names += [GEMINI_MODEL, "gemini-flash-latest"]
    seen = []
    for n in names:
        if n and n not in seen: seen.append(n)
    return seen

def generate(items_with_text):
    key = os.environ["GEMINI_API_KEY"]
    body = "\n\n".join(f"[{i}] {it['title']}\n{it['text']}" for i, it in enumerate(items_with_text))
    payload = {"contents": [{"parts": [{"text": PROMPT + body}]}],
               "generationConfig": {"responseMimeType": "application/json", "temperature": 0.5}}
    last = None
    for m in _models(key)[:6]:
        r = requests.post(f"{BASE}/models/{m}:generateContent", params={"key": key}, json=payload, timeout=120)
        if r.status_code == 200:
            print("using model", m)
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            txt = txt.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                return json.loads(txt)
            except Exception as e:
                last = f"{m}: bad JSON ({e})"; print(last); continue
        last = f"{m}: {r.status_code} {r.text[:300]}"; print("model failed ->", last)
    raise SystemExit("All Gemini models failed. Last error: " + str(last))
