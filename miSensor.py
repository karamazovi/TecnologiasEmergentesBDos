"""
Semana 2 — MI SENSOR (Plantilla para clase)
=========================================================
INSTRUCCIONES:
  1. Completa los bloques TODO-S para implementar el sensor de tu dominio.
  2. Al completar los TODOs, el lanzador automático detectará este archivo como listo.
"""

import random
import logging
import threading

# ┌─────────────────────────────────────────────────────────────┐
# │ TODO-S1: Importar la clase base SensorBase                  │
# └─────────────────────────────────────────────────────────────┘
# Escribe la importación de SensorBase desde sensorBase
from sensorBase import SensorBase

logger = logging.getLogger(__name__)


# ┌─────────────────────────────────────────────────────────────┐
# │ TODO-S2: Definir la clase del Sensor e implementar método   │
# │                                                             │
# │ Tu clase debe heredar de SensorBase.                        │
# │ El método leerDatos() debe retornar siempre:                │
# │   {"idDispositivo": self.idDispositivo, ...variables...}     │
# └─────────────────────────────────────────────────────────────┘

class SensorAcuicola(SensorBase):
    """Sensor de estanque acuícola: temperatura, pH y oxígeno disuelto."""

    def leerDatos(self) -> dict:
        # TODO-S2: Retorna un diccionario con datos aleatorios realistas
        # temperatura: 18.0 a 34.0
        # ph: 6.0 a 9.5
        # oxigenoDisuelto: 1.5 a 10.0
        return {
            "idDispositivo":   self.idDispositivo,
            "temperatura":     round(random.uniform(18.0, 34.0), 2),
            "ph":              round(random.uniform(6.0, 9.5), 2),
            "oxigenoDisuelto": round(random.uniform(1.5, 10.0), 2),
        }


# ═══════════════════════════════════════════════════════════════
# Punto de entrada: inicia los sensores
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # ┌─────────────────────────────────────────────────────────────┐
    # │ TODO-S3: Crear la lista de sensores y arrancarlos en hilos  │
    # └─────────────────────────────────────────────────────────────┘
    CANTIDAD_DISPOSITIVOS = 3  # estanque_a, estanque_b, estanque_c

    # TODO-S3: Crea e inicia los sensores en paralelo usando hilos
    sensores = [
        SensorAcuicola(idDispositivo=f"estanque_{chr(ord('a') + i)}", intervaloSegundos=5)
        for i in range(CANTIDAD_DISPOSITIVOS)
    ]

    hilos = [threading.Thread(target=s.iniciar, daemon=True) for s in sensores]

    logger.info("Iniciando %d sensores acuícolas...", CANTIDAD_DISPOSITIVOS)
    for hilo in hilos:
        hilo.start()

    try:
        for hilo in hilos:
            hilo.join()
    except KeyboardInterrupt:
        logger.info("Sensores detenidos.")
