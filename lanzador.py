"""
Lanzador Dinámico e Inteligente del Sistema IoT
===================================================
Este script inicia todos los componentes del sistema, pero es capaz
de detectar automáticamente qué archivos están "en blanco/plantillas"
y cuáles ya están listos (sin bloques "TODO-") para correr solo lo necesario.

Uso:
  python lanzador.py

Detener:
  Ctrl+C — detiene todos los procesos activos limpiamente.
"""

import os
import sys
import time
import signal
import logging
import subprocess

import configBase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Módulos del sistema acuícola
MODULOS: list[tuple[str, list[str]]] = [
    ("Base de Datos", [sys.executable, "baseDatos.py"]),
    ("Sensores",      [sys.executable, "miSensor.py"]),
    ("Nodo Edge",     [sys.executable, "nodoEdge.py"]),
    ("Nodo Central",  [sys.executable, "nodoCentral.py"]),
    ("Actuadores",    [sys.executable, "actuadores.py"]),
    ("Predictor IA",  [sys.executable, "iaPredictor.py"]),
    ("Chatbot IA",    [sys.executable, "parteSeteChatbot.py"]),
    ("Dashboard Web", [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.headless", "true"]),
]

_procesos: list[tuple[str, subprocess.Popen]] = []


def es_modulo_listo(nombre: str, comando: list[str]) -> bool:
    """
    Determina si un módulo está listo analizando si el archivo existe y si
    ha completado todos sus bloques "TODO-".
    """
    # Buscar el nombre del script .py en el comando
    script_py = None
    for arg in comando:
        if arg.endswith(".py"):
            script_py = arg
            break
            
    if not script_py:
        return True  # Si no hay archivo .py, asumimos que está listo
        
    if not os.path.exists(script_py):
        return False
        
    # Verificar si el archivo contiene algún comentario "TODO-"
    try:
        with open(script_py, "r", encoding="utf-8") as f:
            contenido = f.read()
            if "TODO-" in contenido:
                return False
    except Exception:
        return False
        
    return True


def mostrarBanner(modulos_listos: list[str], modulos_pendientes: list[str]) -> None:
    broker = f"{configBase.BROKER_MQTT}:{configBase.PUERTO_MQTT}"
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      🚀 LANZADOR DINÁMICO — CLASE SEMANA UNO             ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  ESTADO DE LOS MÓDULOS EN LA CARPETA:                    ║")
    print("║                                                          ║")
    
    # Mostrar listos
    for m in modulos_listos:
        print(f"║   🟢 {m:<20} → ¡LISTO PARA CORRER!              ║")
        
    # Mostrar pendientes
    for m in modulos_pendientes:
        print(f"║   ⏳ {m:<20} → Omitido (tiene bloques TODO-)     ║")
        
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  ACCESO RÁPIDO:                                          ║")
    print(f"║   Dashboard web  →  http://localhost:8501                ║")
    print(f"║   Broker MQTT    →  {broker:<39}║")
    print(f"║   Base de datos  →  {configBase.RUTA_BD:<39}║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Instrucciones:                                          ║")
    print("║   Completa los bloques TODO- de cada archivo en la clase ║")
    print("║   y guarda. El lanzador los activará automáticamente.     ║")
    print("║                                                          ║")
    print("║   Usa Ctrl+C para apagar los servicios activos.          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def lanzar(nombre: str, comando: list[str]) -> subprocess.Popen:
    p = subprocess.Popen(comando)
    logger.info("✅ %-14s iniciado  (PID %d)", nombre, p.pid)
    return p


def detenerTodos(signum=None, frame=None) -> None:
    print()
    logger.info("Deteniendo todos los servicios activos...")
    for nombre, p in _procesos:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
            logger.info("❌ %-14s detenido.", nombre)
    logger.info("Sistema apagado limpiamente.")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, detenerTodos)
    signal.signal(signal.SIGTERM, detenerTodos)

    listos = []
    pendientes = []
    modulos_a_lanzar = []

    for nombre, comando in MODULOS:
        if es_modulo_listo(nombre, comando):
            listos.append(nombre)
            modulos_a_lanzar.append((nombre, comando))
        else:
            pendientes.append(nombre)

    mostrarBanner(listos, pendientes)

    if not modulos_a_lanzar:
        logger.warning("⚠️  No hay ningún módulo listo para ejecutar todavía.")
        logger.info("Comienza abriendo 'miSensor.py' e implementando los bloques TODO-S.")
        logger.info("El lanzador se mantendrá a la espera de Ctrl+C o puedes cerrarlo.")
        
        # Mantener vivo el script por si quieren presionar Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            detenerTodos()

    logger.info("Iniciando módulos listos...")
    for nombre, comando in modulos_a_lanzar:
        # Si es base de datos o Streamlit, aseguramos un pequeño delay
        p = lanzar(nombre, comando)
        _procesos.append((nombre, p))
        time.sleep(2)

    print()
    logger.info("━" * 54)
    logger.info("  Servicios en línea. Monitoreando ejecución...")
    logger.info("  Presiona Ctrl+C para detenerlos todos a la vez.")
    logger.info("━" * 54)
    print()

    # Bucle de monitoreo
    try:
        while True:
            for nombre, p in _procesos:
                if p.poll() is not None:
                    logger.warning("⚠️  %s terminó inesperadamente (código %d)", nombre, p.returncode)
                    # Quitar de la lista para no reportar repetidamente
                    _procesos.remove((nombre, p))
            time.sleep(10)
    except KeyboardInterrupt:
        detenerTodos()
