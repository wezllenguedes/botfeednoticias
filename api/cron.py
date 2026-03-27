import os
import requests
import random

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def gerar_noticia():
    noticias = [
        "O preço do petróleo voltou a subir e impacta mercados globais.",
        "Governo anuncia novas medidas econômicas para conter inflação.",
        "Tecnologia avança com novas soluções em inteligência artificial.",
        "Conflitos internacionais aumentam tensão no cenário global.",
        "Mercado financeiro reage a decisões de juros nos EUA."
    ]
    return random.choice(noticias)

def montar_mensagem(texto):
    return f"🌍 | {texto}\n\n⭐️ Feed\n#⃣ #Mundo"

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

def handler(request):
    noticia = gerar_noticia()
    msg = montar_mensagem(noticia)

    enviar_telegram(msg)

    return {
        "statusCode": 200,
        "body": "OK"
    }
