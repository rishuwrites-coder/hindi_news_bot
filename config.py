import os
CHANNEL_NAME = os.getenv("CHANNEL_NAME") or "भारत खबर 24"
FEEDS = [
    "https://feeds.bbci.co.uk/hindi/rss.xml",
    "https://news.google.com/rss/headlines/section/topic/NATION?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/search?q=%E0%A4%B0%E0%A4%BE%E0%A4%9C%E0%A4%A8%E0%A5%80%E0%A4%A4%E0%A4%BF+when:1d&hl=hi&gl=IN&ceid=IN:hi",
]
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID") or "pNInz6obpgDQGcFmaJgB"
ELEVEN_MODEL = os.getenv("ELEVEN_MODEL") or "eleven_multilingual_v2"
EDGE_VOICE = "hi-IN-MadhurNeural"
GEMINI_MODEL = "gemini-2.5-flash"
W, H, FPS = 1080, 1920, 30
