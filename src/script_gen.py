import json, os, requests
from config import GEMINI_MODEL
PROMPT = """आप भारतीय न्यूज़ शॉर्ट्स के स्क्रिप्ट राइटर हैं।
नीचे आज की ख़बरों की सूची है। इनमें से सबसे ज़्यादा ट्रेंडिंग/महत्वपूर्ण (राजनीति/भारत प्राथमिकता) ख़बर चुनें और 30-40 सेकंड (लगभग 85-100 शब्द) की हिंदी स्क्रिप्ट लिखें।
नियम: सिर्फ़ दिए गए टेक्स्ट के तथ्य इस्तेमाल करें, कुछ भी अपनी तरफ़ से न जोड़ें। निष्पक्ष, तथ्यात्मक भाषा, बिना भड़काऊ/सांप्रदायिक शब्दों के। पहली लाइन एक तेज़ हुक हो। आख़िरी लाइन में "ऐसी ख़बरों के लिए चैनल फ़ॉलो करें"।
हर लाइन छोटी (8-14 शब्द) हो। केवल JSON लौटाएँ:
{"index": <चुनी ख़बर का नंबर>, "headline": "<=8 शब्द हेडलाइन", "lines": [{"text": "हिंदी लाइन", "visual": "english stock video search keywords 2-3 words"}], "title": "YouTube शीर्षक #Shorts", "description": "विवरण + हैशटैग"}
ख़बरें:
"""
def generate(items_with_text):
    body = "\n\n".join(f"[{i}] {it['title']}\n{it['text']}" for i, it in enumerate(items_with_text))
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        params={"key": os.environ["GEMINI_API_KEY"]},
        json={"contents": [{"parts": [{"text": PROMPT + body}]}],
              "generationConfig": {"responseMimeType": "application/json", "temperature": 0.5}},
        timeout=120)
    r.raise_for_status()
    return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
