import json, os, time, requests
from config import GEMINI_MODEL
BASE = "https://generativelanguage.googleapis.com/v1beta"
PROMPT = """आप भारतीय न्यूज़ शॉर्ट्स के स्क्रिप्ट राइटर हैं।
नीचे आज की ख़बरों की सूची है। इनमें से सबसे ज़्यादा ट्रेंडिंग/महत्वपूर्ण (राजनीति/भारत प्राथमिकता) ख़बर चुनें और 30-40 सेकंड (लगभग 85-100 शब्द) की हिंदी स्क्रिप्ट लिखें।
नियम: सिर्फ़ दिए गए टेक्स्ट के तथ्य इस्तेमाल करें, कुछ भी अपनी तरफ़ से न जोड़ें। निष्पक्ष, तथ्यात्मक भाषा, बिना भड़काऊ/सांप्रदायिक शब्दों के। पहली लाइन एक तेज़ हुक हो। आख़िरी लाइन में "ऐसी ख़बरों के लिए चैनल फ़ॉलो करें"।
visual में कभी किसी व्यक्ति, अभिनेता, फ़िल्म या ब्रांड का नाम न लिखें (नाम से जानवर/ग़लत फ़ोटो आ जाती है)। visual सिर्फ़ जगह, इमारत, संस्था या वस्तु का हो, जैसे "Mumbai street", "Parliament of India"। एक ही visual दोबारा न दें। अगर लाइन किसी जाने-माने सार्वजनिक व्यक्ति (नेता, अभिनेता, खिलाड़ी) के बारे में है और वही ख़बर का मुख्य विषय है, तो "person" में उसका पूरा अंग्रेज़ी नाम लिखें, वरना ""। आरोपी, पीड़ित या आम नागरिक के लिए "person" हमेशा ""। पीड़ितों/मृतकों के लिए ग्राफ़िक या भयावह चित्र न माँगें, सिर्फ़ जगह या पुलिस/प्रशासन जैसे तटस्थ विषय रखें।\nहर लाइन छोटी (8-14 शब्द) हो। केवल JSON लौटाएँ:
{"index": <चुनी ख़बर का नंबर>, "headline": "<=8 शब्द हेडलाइन", "lines": [{"text": "हिंदी लाइन", "visual": "specific English photo search terms (place/person/event/organisation, 2-4 words, e.g. Kolkata Durga Puja pandal)", "visual_fallback": "general English terms 1-2 words, e.g. Kolkata", "person": ""}], "title": "YouTube शीर्षक #Shorts", "description": "विवरण + हैशटैग"}
ख़बरें:
"""
def _models(key):
    """Stable models first. Preview/omni models often have 0 free quota (429), so they go last."""
    names = [os.getenv("GEMINI_MODEL") or "", "gemini-flash-latest"]
    try:
        r = requests.get(f"{BASE}/models", params={"key": key, "pageSize": 200}, timeout=30).json()
        ok = [m["name"].split("/")[-1] for m in r.get("models", [])
              if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m["name"]
              and not any(x in m["name"] for x in ("image", "tts", "live", "audio", "robotics", "computer", "omni", "exp"))]
        stable = sorted([n for n in ok if "preview" not in n and "lite" not in n], reverse=True)
        lite = sorted([n for n in ok if "preview" not in n and "lite" in n], reverse=True)
        prev = sorted([n for n in ok if "preview" in n], reverse=True)
        names += stable + lite + prev
    except Exception:
        pass
    names.append(GEMINI_MODEL)
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
        if r.status_code == 429:  # per-minute limit: wait once and retry the same model
            print(f"  {m}: 429, waiting 25s"); time.sleep(25)
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
