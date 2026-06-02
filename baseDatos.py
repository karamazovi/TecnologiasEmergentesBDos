"""
Semana 4 — Capa de Persistencia con SQLite (Plantilla para clase)
===================================================================
Maneja la base de datos local SQLite del proyecto de monitoreo.
"""

import sqlite3
import logging
from typing import Any
import configBase

logger = logging.getLogger(__name__)


def inicializarBaseDatos() -> None:
    """
    Crea las tablas si no existen.
    
    ┌─────────────────────────────────────────────────────────────┐
    │ TODO-D1: Crear tablas en SQLite                             │
    │                                                             │
    │ 1. Tabla 'lecturas':                                        │
    │    id (INTEGER PRIMARY KEY AUTOINCREMENT)                   │
    │    idDispositivo (TEXT NOT NULL)                            │
    │    temperatura (REAL), ph (REAL), oxigenoDisuelto (REAL)    │
    │    fecha (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)              │
    │                                                             │
    │ 2. Tabla 'historialActuadores':                             │
    │    id, idDispositivo, nombreActuador (TEXT), accion (TEXT)  │
    │    fecha (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)              │
    └─────────────────────────────────────────────────────────────┘
    """
    with sqlite3.connect(configBase.RUTA_BD) as conexion:
        # TODO-D1: Completa la sentencia SQL
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS lecturas (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                idDispositivo    TEXT    NOT NULL,
                temperatura      REAL,
                ph               REAL,
                oxigenoDisuelto  REAL,
                fecha            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS historialActuadores (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                idDispositivo   TEXT NOT NULL,
                nombreActuador  TEXT,
                accion          TEXT,
                fecha           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    logger.info("Base de datos lista: %s", configBase.RUTA_BD)


def guardarLectura(idDispositivo: str, **camposAdicionales: float) -> None:
    """
    Guarda una lectura del sensor en la base de datos.
    
    ┌─────────────────────────────────────────────────────────────┐
    │ TODO-D2: Insertar lectura parametrizada                     │
    │                                                             │
    │ Inserta en 'lecturas' los valores recibidos de forma        │
    │ segura para evitar inyección SQL.                           │
    └─────────────────────────────────────────────────────────────┘
    """
    campos = list(camposAdicionales.keys())
    valores = list(camposAdicionales.values())

    columnas = ", ".join(["idDispositivo"] + campos)
    marcadores = ", ".join(["?"] * (1 + len(campos)))

    with sqlite3.connect(configBase.RUTA_BD) as conexion:
        # TODO-D2: Ejecutar sentencia INSERT
        conexion.execute(
            f"INSERT INTO lecturas ({columnas}) VALUES ({marcadores})",
            [idDispositivo] + valores,
        )
    logger.debug("Lectura guardada [%s]: %s", idDispositivo, camposAdicionales)


def guardarAccionActuador(idDispositivo: str, nombreActuador: str, accion: str) -> None:
    """
    Registra el historial de activaciones/desactivaciones de actuadores.
    
    ┌─────────────────────────────────────────────────────────────┐
    │ TODO-D3: Guardar acción de actuadores                       │
    └─────────────────────────────────────────────────────────────┘
    """
    with sqlite3.connect(configBase.RUTA_BD) as conexion:
        # TODO-D3: Ejecutar inserción en historialActuadores
        conexion.execute(
            "INSERT INTO historialActuadores (idDispositivo, nombreActuador, accion) VALUES (?, ?, ?)",
            (idDispositivo, nombreActuador, accion),
        )
    logger.info("Actuador registrado [%s] %s → %s", idDispositivo, nombreActuador, accion)


def obtenerUltimasLecturas(limite: int = 10) -> list[tuple[Any, ...]]:
    """Retorna las últimas N lecturas ordenadas por más reciente."""
    with sqlite3.connect(configBase.RUTA_BD) as conexion:
        cursor = conexion.execute(
            "SELECT * FROM lecturas ORDER BY id DESC LIMIT ?", (limite,)
        )
        return cursor.fetchall()


def obtenerLecturasPorDispositivo(idDispositivo: str, limite: int = 20) -> list[tuple[Any, ...]]:
    """Retorna las últimas N lecturas de un dispositivo específico."""
    with sqlite3.connect(configBase.RUTA_BD) as conexion:
        cursor = conexion.execute(
            "SELECT * FROM lecturas WHERE idDispositivo = ? ORDER BY id DESC LIMIT ?",
            (idDispositivo, limite),
        )
        return cursor.fetchall()


if __name__ == "__main__":
    inicializarBaseDatos()
    guardarLectura("estanque_a", temperatura=25.0, ph=7.2, oxigenoDisuelto=6.5)
    lecturas = obtenerUltimasLecturas(limite=5)
    logger.info("Últimas lecturas guardadas de prueba:")
    for fila in lecturas:
        logger.info("  %s", fila)
