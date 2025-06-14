from telethon import TelegramClient, events
import os
from flask import Flask
from threading import Thread, Timer
import re
import asyncio

# Flask para manter online no Railway
app = Flask('')

@app.route('/')
def home():
    return "Bot está online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def manter_online():
    Thread(target=run).start()

manter_online()

# 🔐 Credenciais da API
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
client = TelegramClient("session", api_id, api_hash)

# IDs do grupo de origem e destino
origens = [-1002368866066]
destino_id = -1002632937431

grouped_processados = set()

# Limpar grouped_processados a cada 10 min
def limpar_grouped():
    grouped_processados.clear()
    print("♻️ Limpeza de grouped_processados feita.")
    Timer(600, limpar_grouped).start()

limpar_grouped()

@client.on(events.NewMessage(chats=origens))
async def handler(event):
    try:
        msg = event.message
        texto_original = msg.message or ""

        # Remove links (mas mantém legenda)
        texto_limpo = re.sub(r'https?://\S+', '', texto_original).strip()

        if msg.grouped_id:
            if msg.grouped_id in grouped_processados:
                return
            grouped_processados.add(msg.grouped_id)

            print("📦 Álbum detectado.")
            mensagens = await client.get_messages(event.chat_id, limit=20, min_id=msg.id - 10)
            album = [m for m in mensagens if m.grouped_id == msg.grouped_id]
            album = list(reversed(album))
            media_files = [m.media for m in album if m.media]

            if media_files:
                print(f"🎯 Enviando álbum com {len(media_files)} mídias...")
                await client.send_file(destino_id, media_files, caption=texto_limpo or None)
        elif msg.video or msg.photo:
            print("📸 Mídia única detectada.")
            await client.send_file(destino_id, msg.media, caption=texto_limpo or None)
        else:
            print("⚠️ Ignorado.")
    except Exception as e:
        print(f"❌ Erro: {e}")

async def main():
    print("🤖 Bot rodando...")
    await client.start()
    await client.run_until_disconnected()

client.loop.run_until_complete(main())