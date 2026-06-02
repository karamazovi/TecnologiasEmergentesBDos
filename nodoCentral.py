"""
Nodo Central (Plantilla para clase)
=====================================
Recibe datos procesados por el Nodo Edge y aplica las reglas de negocio
para controlar el splash (aireador) y guardarlos en la base de datos.
"""

import json
import logging
import paho.mqtt.client as mqtt

import baseDatos
import configBase

logger = logging.getLogger(__name__)

# Umbrales acuícolas
OD_CRITICO = 3.0   # mg/L — alerta + splash ON
OD_BAJO    = 4.0   # mg/L — splash ON sin alerta
OD_NORMAL  = 4.8   # mg/L — splash OFF (histéresis: 4.0–4.8)
TEMP_ALTA  = 30.0  # °C   — splash ON si OD en histéresis

# Estado en memoria de los actuadores
_estadoActuadores: dict[str, dict[str, str]] = {}


def evaluarReglasAcuicolas(datos: dict) -> None:
    """Evalúa variables y activa/desactiva splash según umbrales."""
    idDispositivo = datos["idDispositivo"]

    if idDispositivo not in _estadoActuadores:
        _estadoActuadores[idDispositivo] = {"splash": "APAGAR"}

    od   = datos.get("oxigenoDisuelto", 7.0)
    temp = datos.get("temperatura", 25.0)
    ph   = datos.get("ph", 7.0)

    # ┌─────────────────────────────────────────────────────────────┐
    # │ TODO-C1: Evaluar reglas acuícolas                           │
    # │                                                             │
    # │ - Si od < OD_CRITICO: encender splash y enviar alerta crítica│
    # │ - Si od < OD_BAJO: encender splash                          │
    # │ - Si od >= OD_NORMAL y temp <= TEMP_ALTA: apagar splash      │
    # │ - Si temp > TEMP_ALTA y od está en histéresis (4.0 a 4.8):  │
    # │   encender splash y enviar alerta por temperatura alta       │
    # │ - Si ph < 6.5 o ph > 9.0: enviar alerta por ph fuera de rango│
    # └─────────────────────────────────────────────────────────────┘
    if od < OD_CRITICO:
        _aplicarCambio(idDispositivo, "splash", "ENCENDER")
        enviarAlerta(f"🚨 OD crítico en {idDispositivo}: {od} mg/L")
    elif od < OD_BAJO:
        _aplicarCambio(idDispositivo, "splash", "ENCENDER")
    elif od >= OD_NORMAL and temp <= TEMP_ALTA:
        _aplicarCambio(idDispositivo, "splash", "APAGAR")
    else:
        if temp > TEMP_ALTA:
            _aplicarCambio(idDispositivo, "splash", "ENCENDER")
            enviarAlerta(f"⚠️ Temperatura alta en {idDispositivo}: {temp}°C")

    if ph < 6.5 or ph > 9.0:
        enviarAlerta(f"⚠️ pH fuera de rango en {idDispositivo}: {ph}")


def _aplicarCambio(idDispositivo: str, nombreActuador: str, accion: str) -> None:
    """Envía comando SOLO si el estado cambió. Evita comandos redundantes."""
    estadoActual = _estadoActuadores[idDispositivo].get(nombreActuador, "")
    if estadoActual != accion:
        publicarComando(idDispositivo, nombreActuador, accion)
        _estadoActuadores[idDispositivo][nombreActuador] = accion
        baseDatos.guardarAccionActuador(idDispositivo, nombreActuador, accion)


def publicarComando(idDispositivo: str, nombreActuador: str, accion: str) -> None:
    """Publica una orden de control al actuador correspondiente."""
    payload = {
        "idDispositivo": idDispositivo,
        "nombreActuador": nombreActuador,
        "accion": accion,
    }
    tema = f"{configBase.TEMA_BASE}/actuadores/{idDispositivo}/{nombreActuador}"
    _clienteMqtt.publish(tema, json.dumps(payload), qos=1)
    logger.info("[NODO] %s/%s → %s", idDispositivo, nombreActuador, accion)


def enviarAlerta(mensajeAlerta: str) -> None:
    """Publica una alerta al canal de notificaciones push."""
    tema = f"{configBase.TEMA_BASE}/alertas"
    _clienteMqtt.publish(tema, mensajeAlerta, qos=1)
    logger.warning("[ALERTA] %s", mensajeAlerta)


def alConectar(client, userdata, flags, rc: int) -> None:
    if rc == 0:
        temaSuscripcion = f"{configBase.TEMA_BASE}/sensores/procesado/#"
        client.subscribe(temaSuscripcion)
        logger.info("Nodo Central conectado. Escuchando: %s", temaSuscripcion)
    else:
        logger.error("Fallo al conectar nodo. Código: %d", rc)


def alRecibirMensaje(client, userdata, msg) -> None:
    """Callback: recibe datos ya filtrados y enriquecidos por el nodo edge."""
    try:
        datos = json.loads(msg.payload.decode("utf-8"))
        idDisp = datos.get("idDispositivo", "desconocido")
        anomalia  = datos.get("anomalia", False)
        tendencia = datos.get("tendenciaOD", "")
        muestras  = datos.get("muestras", 1)

        logger.info(
            "Datos de [%s]: OD=%.2f T=%.1f pH=%.2f | tendencia=%s anomalía=%s muestras=%d",
            idDisp,
            datos.get("oxigenoDisuelto", 0),
            datos.get("temperatura", 0),
            datos.get("ph", 0),
            tendencia,
            anomalia,
            muestras,
        )

        # ┌─────────────────────────────────────────────────────────────┐
        # │ TODO-C2: Guardar en la Base de Datos                        │
        # │                                                             │
        # │ Filtra los campos del JSON y guarda en SQLite llamando a:  │
        # │ baseDatos.guardarLectura(...)                               │
        # └─────────────────────────────────────────────────────────────┘
        campos_bd = {k: v for k, v in datos.items()
                     if k in ("temperatura", "ph", "oxigenoDisuelto")}
        baseDatos.guardarLectura(idDisp, **campos_bd)

        evaluarReglasAcuicolas(datos)

        # ┌─────────────────────────────────────────────────────────────┐
        # │ TODO-C3: Alertas por anomalía                               │
        # │                                                             │
        # │ Si se recibe la bandera de anomalía activa, llama a         │
        # │ enviarAlerta(...) con un mensaje descriptivo.               │
        # └─────────────────────────────────────────────────────────────┘
        if anomalia:
            enviarAlerta(f"⚠️ Anomalía detectada en {idDisp} (cambio súbito en sensor)")

    except json.JSONDecodeError:
        logger.error("Payload no es JSON válido: %s", msg.payload)
    except Exception as error:
        logger.error("Error procesando mensaje: %s", error)


_clienteMqtt = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
_clienteMqtt.on_connect = alConectar
_clienteMqtt.on_message = alRecibirMensaje

if __name__ == "__main__":
    baseDatos.inicializarBaseDatos()
    logger.info("Iniciando Nodo Central...")
    _clienteMqtt.connect(configBase.BROKER_MQTT, configBase.PUERTO_MQTT, 60)
    _clienteMqtt.loop_forever()
