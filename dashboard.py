"""
Dashboard Acuícola IoT — Streamlit
=====================================
Monitoreo en tiempo real + control manual del splash por estanque.

Ejecutar:
  streamlit run dashboard.py   →  http://localhost:8501
"""

import json
import time

import pandas as pd
import paho.mqtt.client as mqtt
import streamlit as st

import baseDatos
import configBase

st.set_page_config(
    page_title="Dashboard Acuícola IoT",
    page_icon="🐟",
    layout="wide",
)

COLS = ["id", "idDispositivo", "temperatura", "ph", "oxigenoDisuelto", "fecha"]


@st.cache_resource
def get_mqtt_client():
    """Cliente MQTT singleton — persiste entre reruns de Streamlit."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    try:
        client.connect(configBase.BROKER_MQTT, configBase.PUERTO_MQTT, keepalive=60)
        client.loop_start()
    except Exception:
        pass
    return client


def publicar_splash(idDispositivo: str, accion: str) -> None:
    payload = json.dumps({
        "idDispositivo": idDispositivo,
        "nombreActuador": "splash",
        "accion": accion,
    })
    tema = f"{configBase.TEMA_BASE}/actuadores/{idDispositivo}/splash"
    get_mqtt_client().publish(tema, payload, qos=1)


def cargarDatos() -> pd.DataFrame:
    filas = baseDatos.obtenerUltimasLecturas(limite=120)
    if not filas:
        return pd.DataFrame(columns=COLS)
    return pd.DataFrame(filas, columns=COLS)


def estado_splash(idDispositivo: str) -> str:
    """Lee el último estado del splash desde historialActuadores."""
    import sqlite3
    try:
        with sqlite3.connect(configBase.RUTA_BD) as conn:
            row = conn.execute(
                "SELECT accion FROM historialActuadores "
                "WHERE idDispositivo=? AND nombreActuador='splash' "
                "ORDER BY fecha DESC LIMIT 1",
                (idDispositivo,),
            ).fetchone()
        return row[0] if row else "APAGAR"
    except Exception:
        return "APAGAR"


def mostrarTarjetas(df: pd.DataFrame) -> None:
    dispositivos = sorted(df["idDispositivo"].unique())
    columnas = st.columns(len(dispositivos))

    for col, idDisp in zip(columnas, dispositivos):
        df_disp = df[df["idDispositivo"] == idDisp]
        if df_disp.empty:
            continue
        ultima = df_disp.iloc[0]
        temp = ultima["temperatura"]
        ph   = ultima["ph"]
        od   = ultima["oxigenoDisuelto"]

        alerta = (temp is not None and temp > 30.0) or (od is not None and od < 3.0)
        encabezado = f"🔴 {idDisp}" if alerta else f"🟢 {idDisp}"

        with col:
            st.subheader(encabezado)
            st.metric(
                "🌡️ Temperatura",
                f"{temp:.1f} °C" if temp is not None else "N/D",
                delta=f"{temp - 30.0:+.1f}°C" if temp is not None else None,
                delta_color="inverse",
            )
            st.metric("🧪 pH", f"{ph:.2f}" if ph is not None else "N/D")
            st.metric(
                "💧 Oxígeno Disuelto",
                f"{od:.2f} mg/L" if od is not None else "N/D",
                delta=f"{od - 5.0:+.2f}" if od is not None else None,
                delta_color="normal",
            )

            # ── Control del splash ──────────────────────────────
            st.divider()
            splash = estado_splash(idDisp)
            encendido = splash == "ENCENDER"
            st.caption(f"🌀 Splash: {'⚡ ENCENDIDO' if encendido else '💤 APAGADO'}")

            b1, b2 = st.columns(2)
            if b1.button("⚡ Encender", key=f"on_{idDisp}", disabled=encendido,
                         use_container_width=True, type="primary"):
                publicar_splash(idDisp, "ENCENDER")
                st.rerun()
            if b2.button("💤 Apagar", key=f"off_{idDisp}", disabled=not encendido,
                         use_container_width=True):
                publicar_splash(idDisp, "APAGAR")
                st.rerun()


def mostrarControlesGlobales(dispositivos: list) -> None:
    st.divider()
    st.subheader("🎛️ Control global")
    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("⚡ Encender todos", type="primary", use_container_width=True):
        for d in dispositivos:
            publicar_splash(d, "ENCENDER")
        st.rerun()
    if c2.button("💤 Apagar todos", use_container_width=True):
        for d in dispositivos:
            publicar_splash(d, "APAGAR")
        st.rerun()


def mostrarGraficas(df: pd.DataFrame) -> None:
    st.divider()
    df_sorted = df.sort_values("fecha")

    st.subheader("📈 Temperatura (°C)")
    st.line_chart(
        df_sorted.pivot_table(index="fecha", columns="idDispositivo", values="temperatura")
    )

    st.subheader("📈 Oxígeno Disuelto (mg/L)")
    st.line_chart(
        df_sorted.pivot_table(index="fecha", columns="idDispositivo", values="oxigenoDisuelto")
    )

    st.subheader("📈 pH")
    st.line_chart(
        df_sorted.pivot_table(index="fecha", columns="idDispositivo", values="ph")
    )


def mostrarTabla(df: pd.DataFrame) -> None:
    st.divider()
    st.subheader("🗃️ Últimas lecturas")
    st.dataframe(
        df.head(30).sort_values("fecha", ascending=False),
        use_container_width=True,
    )


# ── Bucle principal ─────────────────────────────────────────────
st.title("🐟 Dashboard Acuícola IoT")
st.caption(f"Broker: `{configBase.BROKER_MQTT}:{configBase.PUERTO_MQTT}` · actualización cada 3 s")

baseDatos.inicializarBaseDatos()
contenedor = st.empty()

while True:
    with contenedor.container():
        df = cargarDatos()

        if df.empty:
            st.warning(
                "Sin datos aún. Inicia los servicios:\n"
                "```\npython nodoCentral.py\npython miSensor.py\n```"
            )
        else:
            dispositivos = sorted(df["idDispositivo"].unique())
            mostrarTarjetas(df)
            mostrarControlesGlobales(dispositivos)
            mostrarGraficas(df)
            mostrarTabla(df)

    time.sleep(3)
    st.rerun()
