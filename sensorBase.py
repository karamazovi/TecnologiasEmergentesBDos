"""
Semana 2 — Clase base para sensores IoT
========================================
SensorBase define la interfaz común que TODOS los sensores deben implementar.
Tu sensor hereda de esta clase y sobreescribe el método leerDatos().

Patrón: Template Method — la lógica de publicación está aquí,
        solo los datos simulados cambian según el dominio.
"""

import json
import logging
import time
from abc import ABC, abstractmethod

import paho.mqtt.client as mqtt

import configBase

logger = logging.getLogger(__name__)


class SensorBase(ABC):
    """
    Clase abstracta que define el contrato para todos los sensores del proyecto.
    Hereda de esta clase para crear tu sensor específico del dominio.
    """

    def __init__(self, idDispositivo: str, intervaloSegundos: int = 5) -> None:
        self.idDispositivo: str = idDispositivo
        self.intervaloSegundos: int = intervaloSegundos
        self._clienteMqtt: mqtt.Client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._clienteMqtt.on_connect = self._alConectar
        self._clienteMqtt.on_publish = self._alPublicar

    @abstractmethod
    def leerDatos(self) -> dict:
        """
        Genera (o lee) los datos del sensor.
        DEBE retornar un diccionario con al menos {"idDispositivo": self.idDispositivo}.
        Tu subclase implementa este método con las variables de tu dominio.
        """
        ...

    def obtenerTema(self) -> str:
        """Construye el tópico MQTT basado en la configuración."""
        return f"{configBase.TEMA_BASE}/sensores/{self.idDispositivo}"

    def iniciar(self) -> None:
        """Conecta al broker y empieza a publicar datos en bucle."""
        logger.info(
            "Sensor [%s] conectando a %s:%d",
            self.idDispositivo, configBase.BROKER_MQTT, configBase.PUERTO_MQTT,
        )
        self._clienteMqtt.connect(configBase.BROKER_MQTT, configBase.PUERTO_MQTT, 60)
        self._clienteMqtt.loop_start()

        logger.info("Sensor [%s] publicando en: %s", self.idDispositivo, self.obtenerTema())
        try:
            while True:
                datos = self.leerDatos()
                self._clienteMqtt.publish(
                    self.obtenerTema(),
                    json.dumps(datos),
                    qos=0,
                )
                logger.info("[%s] Datos publicados: %s", self.idDispositivo, datos)
                time.sleep(self.intervaloSegundos)

        except KeyboardInterrupt:
            logger.info("Sensor [%s] detenido por el usuario.", self.idDispositivo)
        finally:
            self._clienteMqtt.loop_stop()
            self._clienteMqtt.disconnect()

    def _alConectar(self, client, userdata, flags, rc: int) -> None:
        if rc == 0:
            logger.info("Sensor [%s] conectado al broker.", self.idDispositivo)
        else:
            logger.error("Sensor [%s] fallo de conexión. Código: %d", self.idDispositivo, rc)

    def _alPublicar(self, client, userdata, mid: int) -> None:
        logger.debug("Sensor [%s] mensaje confirmado (id=%d)", self.idDispositivo, mid)
