import os
import time
import requests
import feedparser

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

RSS_FEEDS = [
    "https://g1.globo.com/dynamo/rss2.xml",
    "https://rss.uol.com.br/feed/noticias.xml",
    "https://www.metropoles.com/feed",
    "https://nitter.net/g1/rss",
    "https://nitter.net/choquei/rss",
    "https://news.google.com/rss/search?q=site:r7.com&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
]

def summarize(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
Resuma em até 180 caracteres, direto e claro, sem emoji e sem hashtags:

{text}
"""

    try:
        r = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}]
        }, timeout=10)

        if r.status_code != 200:
            return text[:180]

        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    except:
        return text[:180]

def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )

def run():
    enviados = set()

    while True:
        for feed_url in RSS_FEEDS:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:1]:
                titulo = entry.title

                if titulo in enviados:
                    continue

                resumo = summarize(titulo)
                msg = f"📰 | {resumo} #Notícia"

                send(msg)
                enviados.add(titulo)

                time.sleep(8)

        time.sleep(180)

if __name__ == "__main__":
    run()
