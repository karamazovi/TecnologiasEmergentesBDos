import json
import logging
import statistics
from collections import deque
import paho.mqtt.client as mqtt

import configBase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

VENTANA_N = 5
DELTA_MIN = 0.05
ANAMOLIA_TH = 0.20

VARIABLES = ["temperatura", "ph", "oxigeno_disuelto"]

_ventanas: dict[str, dict[str,int]] = {}
_ultimo_proceso: dict[str, dict[str,float]] = {}  
_contador: dict[str, dict[str, int]] = {}     

def _inicializar(idDispositivo: str) -> None:
   _ventanas[idDispositivo] = {var: deque(maxlen=VENTANA_N) for var in VARIABLES}
   _ultimo_proceso[idDispositivo] = {}
   _contador[idDispositivo] = {"recibidos": 0, "anomalos": 0}
   
   
def _tendencias(valores: deque)-> str:
    if len(valores) < 3:
        return "Desconocido"
    if valores[-1] > valores[-3]:
        return "Subiendo"
    elif valores[-1] < valores[-3]:
        return "Bajando"
    return "Estable" 

def procesarLectura(datos: dict) -> dict | None:
    idDispositivo = datos.get("idDispositivo", "")
    