import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── Configuración MQTT ─────────────────────────────────────────
BROKER_MQTT: str = os.getenv("BROKER_MQTT", "localhost")
PUERTO_MQTT: int = int(os.getenv("PUERTO_MQTT", "1883"))

# Prefijo de todos los tópicos del proyecto
# Ejemplo: "miProyecto/dominio" → "miProyecto/dominio/sensores/sensor_1"
TEMA_BASE: str = os.getenv("TEMA_BASE", "miProyecto/dominio")

# ── Telegram (Parte 7 / Semana 6) ─────────────────────────────
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Base de datos SQLite (Semana 4) ───────────────────────────
RUTA_BD: str = os.getenv("RUTA_BD", "miProyecto.db")

# ── IA conversacional — Groq (gratis en https://console.groq.com) ──
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
