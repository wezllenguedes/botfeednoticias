import json
import os
import re
import time
import html
import hashlib
import datetime
import requests
import xml.etree.ElementTree as ET

from typing import List, Dict, Optional, Tuple
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

os.environ["NO_PROXY"] = "*"

TELEGRAM_TOKEN = "8735928848:AAFRBIjnrbMO3LB5airvo0hn7QAoYQFql8c"
CHAT_ID = "659119789"
GEMINI_API_KEY = "AIzaSyC66iiAQ7Km2Kf_3vkC6pYZ-ti2ozV2GbY"

POLL_SECONDS = 120
DAILY_LIMIT = 80
NEWS_WINDOW_MINUTES = 360
REQUEST_TIMEOUT = 25
MAX_ITEMS_PER_FEED = 8
MAX_SUMMARY_CHARS = 280
MAX_LINK_MEMORY = 10000
MAX_TITLE_MEMORY = 6000
POST_DELAY_SECONDS = 4

COUNT_FILE = "daily_count.json"
STATE_FILE = "sent_links.json"
TITLE_STATE_FILE = "sent_titles.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
}

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

session = requests.Session()
session.headers.update(HEADERS)
session.trust_env = False


def google_news_search_rss(query: str, lang: str = "pt-BR", country: str = "BR", ceid: str = "BR:pt-419") -> str:
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={country}&ceid={ceid}"


RSS_FEEDS: List[Dict[str, str]] = [
    {"source": "G1 - Todas", "url": "https://g1.globo.com/dynamo/rss2.xml"},
    {"source": "G1 - Brasil", "url": "https://g1.globo.com/dynamo/brasil/rss2.xml"},
    {"source": "G1 - Carros", "url": "https://g1.globo.com/dynamo/carros/rss2.xml"},
    {"source": "G1 - Ciência e Saúde", "url": "https://g1.globo.com/dynamo/ciencia-e-saude/rss2.xml"},
    {"source": "G1 - Concursos e Emprego", "url": "https://g1.globo.com/dynamo/concursos-e-emprego/rss2.xml"},
    {"source": "G1 - Economia", "url": "https://g1.globo.com/dynamo/economia/rss2.xml"},
    {"source": "G1 - Educação", "url": "https://g1.globo.com/dynamo/educacao/rss2.xml"},
    {"source": "G1 - Loterias", "url": "https://g1.globo.com/dynamo/loterias/rss2.xml"},
    {"source": "G1 - Mundo", "url": "https://g1.globo.com/dynamo/mundo/rss2.xml"},
    {"source": "G1 - Música", "url": "https://g1.globo.com/dynamo/musica/rss2.xml"},
    {"source": "G1 - Natureza", "url": "https://g1.globo.com/dynamo/natureza/rss2.xml"},
    {"source": "G1 - Planeta Bizarro", "url": "https://g1.globo.com/dynamo/planeta-bizarro/rss2.xml"},
    {"source": "G1 - Política", "url": "https://g1.globo.com/dynamo/politica/mensalao/rss2.xml"},
    {"source": "G1 - Pop & Arte", "url": "https://g1.globo.com/dynamo/pop-arte/rss2.xml"},
    {"source": "G1 - Tecnologia", "url": "https://g1.globo.com/dynamo/tecnologia/rss2.xml"},
    {"source": "G1 - Turismo e Viagem", "url": "https://g1.globo.com/dynamo/turismo-e-viagem/rss2.xml"},
    {"source": "UOL Notícias", "url": "https://rss.uol.com.br/feed/noticias.xml"},
    {"source": "Nitter G1", "url": "https://nitter.net/g1/rss"},
    {"source": "Nitter Choquei", "url": "https://nitter.net/choquei/rss"},
    {"source": "Nitter Oxente Pipoca", "url": "https://nitter.net/oxentepipoca/rss"},
    {"source": "Google News BR - Top", "url": "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"},
    {"source": "Google News BR - Destaques", "url": "https://news.google.com/rss/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNREUxWm5JU0JYQjBMVUpTS0FBUAE?hl=pt-BR&gl=BR&ceid=BR:pt-419"},
    {"source": "Google News BR - Política", "url": google_news_search_rss("política brasil")},
    {"source": "Google News BR - Economia", "url": google_news_search_rss("economia brasil")},
    {"source": "Google News BR - Crime", "url": google_news_search_rss("crime brasil")},
    {"source": "Google News BR - STF", "url": google_news_search_rss("STF")},
    {"source": "Google News BR - Congresso", "url": google_news_search_rss("Congresso Nacional")},
    {"source": "Google News BR - Polícia Federal", "url": google_news_search_rss("Polícia Federal")},
    {"source": "Google News BR - Tecnologia", "url": google_news_search_rss("tecnologia brasil")},
    {"source": "Google News BR - Entretenimento", "url": google_news_search_rss("entretenimento brasil")},
    {"source": "DW Brasil", "url": "https://rss.dw.com/rdf/rss-br-br"},
    {"source": "DW World EN", "url": "https://rss.dw.com/rdf/rss-en-world"},
    {"source": "DW All EN", "url": "https://rss.dw.com/rdf/rss-en-all"},
    {"source": "The Guardian World", "url": "https://www.theguardian.com/world/rss"},
    {"source": "The Guardian Technology", "url": "https://www.theguardian.com/uk/technology/rss"},
    {"source": "The Guardian Business", "url": "https://www.theguardian.com/uk/business/rss"},
    {"source": "The Guardian Politics", "url": "https://www.theguardian.com/politics/rss"},
    {"source": "The Guardian Science", "url": "https://www.theguardian.com/science/rss"},
    {"source": "The Guardian Culture", "url": "https://www.theguardian.com/uk/culture/rss"},
    {"source": "The Guardian Media", "url": "https://www.theguardian.com/uk/media/rss"},
    {"source": "France24 via Google News", "url": google_news_search_rss("site:france24.com France24")},
    {"source": "Reuters via Google News", "url": google_news_search_rss("site:reuters.com Reuters")},
    {"source": "Politico via Google News", "url": google_news_search_rss("site:politico.com Politico")},
    {"source": "Axios via Google News", "url": google_news_search_rss("site:axios.com Axios")},
    {"source": "Ekathimerini via Google News", "url": google_news_search_rss("site:ekathimerini.com Ekathimerini")},
    {"source": "Wired via Google News", "url": google_news_search_rss("site:wired.com Wired")},
    {"source": "The Verge via Google News", "url": google_news_search_rss("site:theverge.com The Verge")},
    {"source": "Ars Technica via Google News", "url": google_news_search_rss("site:arstechnica.com Ars Technica")},
    {"source": "404 Media via Google News", "url": google_news_search_rss("site:404media.co 404 Media")},
    {"source": "AI via Google News", "url": google_news_search_rss("artificial intelligence")},
    {"source": "Big Tech via Google News", "url": google_news_search_rss("big tech")},
    {"source": "OpenAI via Google News", "url": google_news_search_rss("OpenAI")},
    {"source": "Google via Google News", "url": google_news_search_rss("Google technology")},
    {"source": "Apple via Google News", "url": google_news_search_rss("Apple technology")},
    {"source": "Microsoft via Google News", "url": google_news_search_rss("Microsoft technology")},
    {"source": "Meta via Google News", "url": google_news_search_rss("Meta technology")},
    {"source": "Amazon via Google News", "url": google_news_search_rss("Amazon technology")},
    {"source": "Nvidia via Google News", "url": google_news_search_rss("Nvidia")},
    {"source": "Cybersecurity via Google News", "url": google_news_search_rss("cybersecurity")},
    {"source": "Space via Google News", "url": google_news_search_rss("space exploration")},
    {"source": "Recife", "url": google_news_search_rss("Recife notícias")},
    {"source": "Pernambuco", "url": google_news_search_rss("Pernambuco notícias")},
    {"source": "São Paulo", "url": google_news_search_rss("São Paulo notícias")},
    {"source": "Rio de Janeiro", "url": google_news_search_rss("Rio de Janeiro notícias")},
    {"source": "Minas Gerais", "url": google_news_search_rss("Minas Gerais notícias")},
    {"source": "Bahia", "url": google_news_search_rss("Bahia notícias")},
    {"source": "Ceará", "url": google_news_search_rss("Ceará notícias")},
    {"source": "Paraná", "url": google_news_search_rss("Paraná notícias")},
    {"source": "Rio Grande do Sul", "url": google_news_search_rss("Rio Grande do Sul notícias")},
    {"source": "Santa Catarina", "url": google_news_search_rss("Santa Catarina notícias")},
    {"source": "Amazonas", "url": google_news_search_rss("Amazonas notícias")},
    {"source": "Pará", "url": google_news_search_rss("Pará notícias")},
    {"source": "Goiás", "url": google_news_search_rss("Goiás notícias")},
    {"source": "Distrito Federal", "url": google_news_search_rss("Distrito Federal notícias")},
    {"source": "Nordeste", "url": google_news_search_rss("Nordeste notícias")},
    {"source": "Dólar", "url": google_news_search_rss("dólar hoje brasil")},
    {"source": "Ibovespa", "url": google_news_search_rss("Ibovespa")},
    {"source": "Selic", "url": google_news_search_rss("Selic")},
    {"source": "Copom", "url": google_news_search_rss("Copom")},
    {"source": "Petrobras", "url": google_news_search_rss("Petrobras")},
    {"source": "Pix", "url": google_news_search_rss("Pix Brasil")},
    {"source": "Receita Federal", "url": google_news_search_rss("Receita Federal")},
    {"source": "Serasa", "url": google_news_search_rss("Serasa")},
    {"source": "ANP", "url": google_news_search_rss("ANP Brasil")},
    {"source": "Senacon", "url": google_news_search_rss("Senacon")},
    {"source": "Ministério da Justiça", "url": google_news_search_rss("Ministério da Justiça Brasil")},
    {"source": "Operação Polícia", "url": google_news_search_rss("operação polícia brasil")},
    {"source": "Prisão", "url": google_news_search_rss("prisão brasil")},
    {"source": "Investigação", "url": google_news_search_rss("investigação brasil")},
    {"source": "Tribunais", "url": google_news_search_rss("tribunais brasil")},
    {"source": "BBB", "url": google_news_search_rss("BBB")},
    {"source": "Celebridades", "url": google_news_search_rss("celebridades")},
    {"source": "Futebol", "url": google_news_search_rss("futebol")},
    {"source": "Esportes", "url": google_news_search_rss("esportes")},
    {"source": "Educação Brasil", "url": google_news_search_rss("educação brasil")},
    {"source": "Saúde Brasil", "url": google_news_search_rss("saúde brasil")},
    {"source": "Clima Brasil", "url": google_news_search_rss("clima brasil")},
    {"source": "Chuvas Brasil", "url": google_news_search_rss("chuvas brasil")},
    {"source": "Empregos Brasil", "url": google_news_search_rss("empregos brasil")},
    {"source": "Concursos Brasil", "url": google_news_search_rss("concurso público brasil")},
]


def now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_title(text: str) -> str:
    text = clean_text(text).lower()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9áàâãéèêíìîóòôõúùûç ]+", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:220]


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json_file(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_file(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print("erro salvando", path, repr(e))


def load_sent_links() -> set:
    return set(load_json_file(STATE_FILE, []))


def save_sent_links(sent: set) -> None:
    data = sorted(list(sent))[-MAX_LINK_MEMORY:]
    save_json_file(STATE_FILE, data)


def load_sent_titles() -> set:
    return set(load_json_file(TITLE_STATE_FILE, []))


def save_sent_titles(sent: set) -> None:
    data = sorted(list(sent))[-MAX_TITLE_MEMORY:]
    save_json_file(TITLE_STATE_FILE, data)


def load_count() -> Dict[str, int]:
    return load_json_file(COUNT_FILE, {"date": "", "count": 0})


def save_count(data: Dict[str, int]) -> None:
    save_json_file(COUNT_FILE, data)


def can_post() -> bool:
    data = load_count()
    today = str(datetime.date.today())
    if data.get("date") != today:
        data = {"date": today, "count": 0}
        save_count(data)
    return data.get("count", 0) < DAILY_LIMIT


def increment_post() -> None:
    data = load_count()
    today = str(datetime.date.today())
    if data.get("date") != today:
        data = {"date": today, "count": 0}
    data["count"] = data.get("count", 0) + 1
    save_count(data)


def parse_datetime(value: Optional[str]) -> Optional[datetime.datetime]:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except Exception:
        return None


def is_recent(dt: Optional[datetime.datetime]) -> bool:
    if not dt:
        return True
    delta = now_utc() - dt
    return 0 <= delta.total_seconds() <= NEWS_WINDOW_MINUTES * 60


def extract_image_from_description(description: str) -> Optional[str]:
    if not description:
        return None
    match = re.search(r'<img[^>]+src="([^"]+)"', description, flags=re.I)
    if match:
        url = clean_text(match.group(1))
        if url.startswith("http"):
            return url
    return None


def build_source_text(title: str, description: str) -> str:
    title = clean_text(title)
    description = clean_text(description)
    if description and description.lower() not in title.lower():
        return f"{title}. {description}"
    return title


def gemini_generate(model: str, prompt: str) -> Tuple[bool, str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 140,
            "topP": 0.9
        }
    }

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=REQUEST_TIMEOUT,
            proxies={"http": None, "https": None},
        )
    except Exception as e:
        return False, f"request_error={repr(e)}"

    if r.status_code != 200:
        return False, f"status={r.status_code} body={r.text[:500]}"

    try:
        data = r.json()
    except Exception as e:
        return False, f"json_error={repr(e)} raw={r.text[:300]}"

    candidates = data.get("candidates") or []
    if not candidates:
        return False, f"no_candidates={str(data)[:500]}"

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return False, f"no_parts={str(data)[:500]}"

    text = clean_text(parts[0].get("text", ""))
    if not text:
        return False, "empty_text"

    return True, text


def summarize_with_gemini(text: str) -> Tuple[str, str]:
    base_text = clean_text(text)[:4500]

    prompt = f"""
Você é um redator de notícias para Telegram.

Objetivo:
Reescreva o conteúdo abaixo em português do Brasil, de forma clara, curta e objetiva.
Se o texto estiver em inglês ou outro idioma, traduza para pt-BR.
Não copie frases do feed. Reescreva de verdade.

Regras:
- máximo de {MAX_SUMMARY_CHARS} caracteres
- linguagem jornalística, simples e natural
- diga o fato principal
- não cite o nome do veículo
- não use aspas
- não use emojis
- não use hashtags
- não use "segundo o texto" ou "a matéria diz"
- não faça introdução
- responda apenas com o texto final

Conteúdo:
{base_text}
""".strip()

    for model in GEMINI_MODELS:
        ok, result = gemini_generate(model, prompt)
        print(f"gemini model={model} ok={ok} info={result[:180]}")
        if ok:
            result = result.replace("|", "-").replace("#", "")
            result = re.sub(r"\s+", " ", result).strip()
            if len(result) > MAX_SUMMARY_CHARS:
                result = result[:MAX_SUMMARY_CHARS].rsplit(" ", 1)[0].strip() + "..."
            if result:
                return result, model

    fallback = clean_text(base_text)
    if len(fallback) > MAX_SUMMARY_CHARS:
        fallback = fallback[:MAX_SUMMARY_CHARS].rsplit(" ", 1)[0].strip() + "..."
    return fallback, "fallback"


def classify(text: str) -> Tuple[str, List[str]]:
    t = text.lower()

    if any(x in t for x in ["crime", "polícia", "preso", "prisão", "operação", "investigação", "delegado", "pf", "assalto", "homicídio"]):
        return "🚨", ["#Crime", "#Brasil"]

    if any(x in t for x in ["governo", "stf", "congresso", "senado", "câmara", "planalto", "presidente", "ministro", "lula", "bolsonaro"]):
        return "🇧🇷", ["#Política", "#Brasil"]

    if any(x in t for x in ["dólar", "ibovespa", "selic", "economia", "mercado", "inflação", "copom", "juros", "petrobras", "pix"]):
        return "💰", ["#Economia"]

    if any(x in t for x in ["futebol", "partida", "campeonato", "gol", "técnico", "seleção", "clube"]):
        return "⚽", ["#Esportes"]

    if any(x in t for x in ["cantor", "atriz", "ator", "bbb", "reality", "show", "filme", "série", "celebridade"]):
        return "🎬", ["#Entretenimento"]

    if any(x in t for x in ["tecnologia", "ia", "inteligência artificial", "iphone", "android", "google", "microsoft", "meta", "nvidia", "chip"]):
        return "💻", ["#Tecnologia"]

    if any(x in t for x in ["mundo", "guerra", "onu", "europa", "eua", "ucrânia", "israel", "gaza", "china"]):
        return "🌍", ["#Mundo"]

    return "📰", ["#Notícia"]


def build_message(summary: str, emoji: str, tags: List[str], link: Optional[str] = None) -> str:
    tags_txt = " ".join(tags).strip()
    base = f"{emoji} | {summary} {tags_txt}".strip()
    if link:
        return f"{base}\n{link}"
    return base


def send_message(text: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": text[:4096],
                "disable_web_page_preview": False
            },
            timeout=REQUEST_TIMEOUT,
            proxies={"http": None, "https": None},
        )
        print("telegram message:", r.status_code, r.text[:300])
        return r.status_code == 200
    except Exception as e:
        print("erro send_message:", repr(e))
        return False


def send_photo(photo: str, caption: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        r = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "photo": photo,
                "caption": caption[:1024]
            },
            timeout=REQUEST_TIMEOUT,
            proxies={"http": None, "https": None},
        )
        print("telegram photo:", r.status_code, r.text[:300])
        return r.status_code == 200
    except Exception as e:
        print("erro send_photo:", repr(e))
        return False


def send(photo: Optional[str], caption: str) -> bool:
    if photo and photo.startswith("http"):
        ok = send_photo(photo, caption)
        if ok:
            return True
        print("falha na foto; fallback para texto")
    return send_message(caption)


def parse_feed(url: str) -> List[Dict]:
    items = []

    try:
        r = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            proxies={"http": None, "https": None},
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception as e:
        print("erro rss:", url, repr(e))
        return items

    for item in root.findall(".//item")[:MAX_ITEMS_PER_FEED]:
        title = item.findtext("title") or ""
        desc_raw = item.findtext("description") or ""
        link = clean_text(item.findtext("link") or "")
        pub = parse_datetime(item.findtext("pubDate"))
        guid = clean_text(item.findtext("guid") or "")

        if not title or not (link or guid):
            continue

        if pub and not is_recent(pub):
            continue

        image = extract_image_from_description(desc_raw)
        source_text = build_source_text(title, desc_raw)
        canonical_link = link or guid

        items.append({
            "title": clean_text(title),
            "link": canonical_link,
            "text": source_text,
            "image": image,
            "published_at": pub.isoformat() if pub else "",
            "title_norm_hash": hash_text(normalize_title(title)),
        })

    return items


def validate_env() -> None:
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if not CHAT_ID:
        missing.append("CHAT_ID")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        raise RuntimeError("variáveis ausentes: " + ", ".join(missing))


def main():
    validate_env()

    sent_links = load_sent_links()
    sent_titles = load_sent_titles()

    while True:
        try:
            if not can_post():
                print("limite diário atingido")
                time.sleep(POLL_SECONDS)
                continue

            for feed in RSS_FEEDS:
                if not can_post():
                    print("limite diário atingido")
                    break

                print(f"\n===== lendo feed: {feed['source']} =====")
                news_items = parse_feed(feed["url"])

                for item in news_items:
                    if not can_post():
                        break

                    if item["link"] in sent_links:
                        continue

                    if item["title_norm_hash"] in sent_titles:
                        print("duplicada por título:", item["title"])
                        sent_links.add(item["link"])
                        continue

                    summary, used_model = summarize_with_gemini(item["text"])
                    emoji, tags = classify(summary)
                    msg = build_message(summary, emoji, tags, item["link"])

                    ok = send(item["image"], msg)
                    if ok:
                        print("enviado:", feed["source"], "| modelo:", used_model, "|", item["title"][:120])
                        sent_links.add(item["link"])
                        sent_titles.add(item["title_norm_hash"])
                        save_sent_links(sent_links)
                        save_sent_titles(sent_titles)
                        increment_post()
                        time.sleep(POST_DELAY_SECONDS)
                    else:
                        print("falha ao enviar:", item["link"])

        except Exception as e:
            print("erro geral:", repr(e))

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()