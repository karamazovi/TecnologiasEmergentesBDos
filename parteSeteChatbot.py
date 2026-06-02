"""
Semana 7 — Chatbot de Telegram con control de splash (Plantilla)
==================================================================
Conecta Telegram con el broker MQTT y la IA conversacional de Groq.
"""

import json
import logging
import threading
import paho.mqtt.client as mqtt

# ┌─────────────────────────────────────────────────────────────┐
# │ TODO-BOT1: Importar telebot (pyTelegramBotAPI)              │
# └─────────────────────────────────────────────────────────────┘
import telebot

import baseDatos
import configBase
import iaChatGroq
import iaPredictor

logger = logging.getLogger(__name__)

# TODO-BOT1: Inicializar el bot de Telegram
bot = telebot.TeleBot(configBase.TELEGRAM_TOKEN, parse_mode="Markdown")

_clienteMqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
_ultimas_alertas: list[str] = []
_estado_splash: dict[str, str] = {}
_estanques: set[str] = set()

_alertasIAActivas: bool = True
_INTERVALO_VERIFICACION_IA: int = 60


def _publicarComandoSplash(idDispositivo: str, accion: str) -> None:
    payload = {
        "idDispositivo": idDispositivo,
        "nombreActuador": "splash",
        "accion": accion,
    }
    tema = f"{configBase.TEMA_BASE}/actuadores/{idDispositivo}/splash"
    _clienteMqtt.publish(tema, json.dumps(payload), qos=1)


# ┌─────────────────────────────────────────────────────────────┐
# │ TODO-BOT2: Configurar Handlers de comandos de Telegram      │
# │                                                             │
# │ Registra los comandos obligatorios:                          │
# │ - /estado: Muestra lecturas más recientes desde base de datos│
# │ - /splash: Estado de encendido de los aireadores           │
# │ - /prediccion: Muestra predicción de riesgo con iaPredictor  │
# │ - /ia <pregunta>: Llama a la IA conversacional (iaChatGroq)  │
# └─────────────────────────────────────────────────────────────┘

@bot.message_handler(commands=["estado"])
def cmd_estado(message):
    lecturas = baseDatos.obtenerUltimasLecturas(limite=6)
    if not lecturas:
        bot.reply_to(message, "Sin datos de sensores. Inicia miSensor.py.")
        return

    seen = set()
    lineas = ["📊 *Estado de estanques:*\n"]
    for fila in lecturas:
        _, idDisp, temp, ph, od, fecha = fila
        if idDisp in seen: continue
        seen.add(idDisp)
        lineas.append(f"🟢 *{idDisp}*: T={temp:.1f}°C  pH={ph:.2f}  OD={od:.2f} mg/L")
    bot.reply_to(message, "\n".join(lineas))


@bot.message_handler(commands=["splash"])
def cmd_splash_estado(message):
    lineas = ["💧 *Estado del splash:*\n"]
    for estanque, estado in sorted(_estado_splash.items()):
        lineas.append(f"🌀 *{estanque}*: {estado}")
    bot.reply_to(message, "\n".join(lineas))


@bot.message_handler(commands=["prediccion"])
def cmd_prediccion(message):
    partes = message.text.split()
    objetivos = [partes[1]] if len(partes) > 1 else sorted(_estanques)
    if not objetivos:
        bot.reply_to(message, "Sin estanques conocidos aún.")
        return

    bot.reply_to(message, "🤖 Analizando datos con IA... un momento.")
    lineas = ["*Predicción de Oxígeno Disuelto (IA):*\n"]
    for idDisp in objetivos:
        res = iaPredictor.predecirEstanque(idDisp)
        lineas.append(res.mensaje)
    bot.reply_to(message, "\n".join(lineas))


def _responder_con_ia(message, pregunta: str) -> None:
    def _tarea():
        respuesta = iaChatGroq.preguntarIA(str(message.chat.id), pregunta)
        bot.reply_to(message, respuesta, parse_mode=None)
    threading.Thread(target=_tarea, daemon=True).start()


@bot.message_handler(commands=["ia"])
def cmd_ia(message):
    partes = message.text.split(maxsplit=1)
    if len(partes) < 2:
        bot.reply_to(message, "Escríbeme tu pregunta después de /ia.")
        return
    bot.reply_to(message, "🤔 Consultando la IA...")
    _responder_con_ia(message, partes[1])


@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith("/"))
def cmd_lenguaje_natural(message):
    bot.reply_to(message, "🤔 Consultando la IA...")
    _responder_con_ia(message, message.text)


# ── Callbacks MQTT ─────────────────────────────────────────────

def alConectarMqtt(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(f"{configBase.TEMA_BASE}/alertas")
        client.subscribe(f"{configBase.TEMA_BASE}/actuadores/#")
        logger.info("Chatbot MQTT conectado.")


def alRecibirMensaje(client, userdata, msg):
    tema = msg.topic
    payload = msg.payload.decode("utf-8")
    if "/actuadores/" in tema:
        try:
            datos = json.loads(payload)
            idDisp = datos.get("idDispositivo", "")
            accion = datos.get("accion", "")
            if idDisp and accion:
                _estado_splash[idDisp] = "ENCENDIDO" if accion == "ENCENDER" else "APAGADO"
                _estanques.add(idDisp)
        except Exception:
            pass


def escucharMqtt():
    _clienteMqtt.on_connect = alConectarMqtt
    _clienteMqtt.on_message = alRecibirMensaje
    _clienteMqtt.connect(configBase.BROKER_MQTT, configBase.PUERTO_MQTT, keepalive=60)
    _clienteMqtt.loop_forever()


if __name__ == "__main__":
    if not configBase.TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN no configurado en el archivo .env.")
        raise SystemExit(1)

    # Iniciar hilos daemon
    threading.Thread(target=escucharMqtt, daemon=True).start()
    logger.info("Chatbot Telegram (Plantilla) activo.")
    bot.infinity_polling()
