from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument
import os
import re
import time

# ✅ API credentials
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
client = TelegramClient("session", api_id, api_hash)

# ✅ Grupos
origem_id = -1001669256167  # <- grupo de origem
destino_id = -1002755408126  # <- grupo de destino

# ✅ Controle de duplicação
enviados_file = "ids_enviados.txt"

def carregar_ids_enviados():
    if not os.path.exists(enviados_file):
        return set()
    with open(enviados_file, "r") as f:
        return set(map(int, f.read().splitlines()))

def salvar_ids_enviados(ids):
    with open(enviados_file, "a") as f:
        for msg_id in ids:
            f.write(f"{msg_id}\n")

# 🔍 Regex para remover links
link_regex = r"https?://\S+"

# 🔁 Começar leitura
print("🔄 Iniciando varredura completa...")
ids_enviados = carregar_ids_enviados()

with client:
    for msg in client.iter_messages(origem_id, reverse=True):
        if msg.id in ids_enviados:
            continue

        # 💾 Álbum (grouped_id)
        if msg.grouped_id:
            grupo_id = msg.grouped_id
            grupo_msgs = list(client.iter_messages(origem_id, reverse=True, limit=20))

            album = [
                m for m in grupo_msgs
                if m.grouped_id == grupo_id and m.media and m.id not in ids_enviados
            ]
            album = list(reversed(album))

            if not album:
                continue

            arquivos = [m.media for m in album if m.media]
            legenda = album[0].message or ""
            legenda_limpa = re.sub(link_regex, "", legenda).strip()

            try:
                client.send_file(destino_id, arquivos, caption=legenda_limpa)
                salvar_ids_enviados([m.id for m in album])
                print(f"✅ Álbum enviado | IDs {[m.id for m in album]}")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Erro no álbum: {e}")

        # 📹 Mídia única (vídeo isolado)
        elif msg.video or (isinstance(msg.media, MessageMediaDocument) and msg.file and 'video' in msg.file.mime_type):
            legenda = msg.message or ""
            legenda_limpa = re.sub(link_regex, "", legenda).strip()

            try:
                client.send_file(destino_id, msg.media, caption=legenda_limpa)
                salvar_ids_enviados([msg.id])
                print(f"✅ Vídeo enviado: ID {msg.id}")
                time.sleep(2)
            except Exception as e:
                print(f"⚠️ Erro no ID {msg.id}: {e}")

        else:
            print(f"⏭️ Ignorado: ID {msg.id}")

print("🚀 Fim da varredura.")
