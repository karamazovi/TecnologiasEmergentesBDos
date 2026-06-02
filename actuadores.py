"""
Semana 5 — Controlador de Actuadores (Plantilla para clase)
=============================================================
Los actuadores simulan las acciones físicas ordenadas por el Nodo Central.
"""

import json
import logging
import paho.mqtt.client as mqtt
import configBase

logger = logging.getLogger(__name__)

# Registro del estado de los actuadores
_estadoActual: dict[str, dict[str, str]] = {}


def ejecutarAccion(idDispositivo: str, nombreActuador: str, accion: str) -> None:
    """
    Simula la ejecución física del actuador.
    
    ┌─────────────────────────────────────────────────────────────┐
    │ TODO-A1: Controlar actuador físico                          │
    │                                                             │
    │ 1. Guarda el estado en el dict '_estadoActual'.              │
    │ 2. Simula encendido/apagado imprimiendo registros en consola│
    │    (usando logger.info con estilo llamativo).               │
    └─────────────────────────────────────────────────────────────┘
    """
    if idDispositivo not in _estadoActual:
        _estadoActual[idDispositivo] = {}
    _estadoActual[idDispositivo][nombreActuador] = accion

    # TODO-A1: Lógica de simulación física
    if accion == "ENCENDER":
        logger.info(
            "⚡ [%s] %s → ENCENDIDO  (GPIO HIGH / relé activado)",
            idDispositivo, nombreActuador.upper(),
        )
    elif accion == "APAGAR":
        logger.info(
            "💤 [%s] %s → APAGADO  (GPIO LOW / relé desactivado)",
            idDispositivo, nombreActuador.upper(),
        )
    else:
        logger.warning("[%s] Acción desconocida para %s: %s", idDispositivo, nombreActuador, accion)


def obtenerEstado(idDispositivo: str) -> dict[str, str]:
    """Retorna el estado actual de todos los actuadores de un dispositivo."""
    return _estadoActual.get(idDispositivo, {})


def alConectar(client, userdata, flags, rc: int) -> None:
    if rc == 0:
        tema = f"{configBase.TEMA_BASE}/actuadores/#"
        client.subscribe(tema)
        logger.info("Actuadores conectados. Escuchando: %s", tema)
    else:
        logger.error("Fallo al conectar actuadores. Código: %d", rc)


def alRecibirComando(client, userdata, msg) -> None:
    """Callback: se ejecuta cuando el nodo central envía un comando."""
    try:
        # ┌─────────────────────────────────────────────────────────────┐
        # │ TODO-A2: Procesar comando MQTT                              │
        # │                                                             │
        # │ Decodifica el comando JSON y llama a ejecutarAccion()       │
        # └─────────────────────────────────────────────────────────────┘
        comando = json.loads(msg.payload.decode("utf-8"))
        idDispositivo = comando.get("idDispositivo", "desconocido")
        nombreActuador = comando.get("nombreActuador", "")
        accion = comando.get("accion", "")

        logger.info("📩 Comando recibido: %s/%s → %s", idDispositivo, nombreActuador, accion)
        ejecutarAccion(idDispositivo, nombreActuador, accion)

    except json.JSONDecodeError:
        logger.error("Comando no es JSON válido: %s", msg.payload)
    except Exception as error:
        logger.error("Error procesando comando: %s", error)


_clienteMqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
_clienteMqtt.on_connect = alConectar
_clienteMqtt.on_message = alRecibirComando

if __name__ == "__main__":
    logger.info("Iniciando Controlador de Actuadores...")
    _clienteMqtt.connect(configBase.BROKER_MQTT, configBase.PUERTO_MQTT, 60)
    _clienteMqtt.loop_forever()
