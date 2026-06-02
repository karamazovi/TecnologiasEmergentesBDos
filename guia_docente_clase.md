# 🎓 Guía del Docente: Paso a Paso para la Clase de IoT Acuícola (Semana 1)

Esta carpeta ha sido configurada y simplificada especialmente para tu clase. Sigue esta guía detallada para impartir una sesión interactiva, dinámica y sorprendente.

---

## 🎮 La Dinámica del Lanzador (Gamificación)
Para motivar a los estudiantes, el archivo `lanzador.py` es **inteligente y dinámico**. 
Al inicio de la clase, todos los archivos son plantillas (tienen comentarios del tipo `TODO-`). Si ejecutas `python lanzador.py`, el terminal mostrará los módulos con un estado de **⏳ Omitido (tiene bloques TODO)**.
A medida que completen el código de cada archivo paso a paso y guarden los cambios (eliminando o resolviendo los bloques `TODO-`), **el lanzador detectará automáticamente el archivo como listo (en verde 🟢) y lo arrancará sin detener el sistema.** 

---

## 🛠️ Paso 0: Preparativos en la Computadora del Docente/Estudiante

1.  **Abrir el terminal** en la carpeta `semanaUno`:
    ```bash
    cd C:\Users\josem\OneDrive\Desktop\semanaUno
    ```
2.  **Instalar las dependencias** del proyecto:
    ```bash
    pip install -r requisitos.txt
    ```
3.  **Iniciar el Broker MQTT (Mosquitto)** en una terminal separada:
    *   En Windows (PowerShell/CMD como Administrador):
        ```powershell
        mosquitto -v
        ```
    *   *(Nota: Esto simula nuestro servidor de mensajería en la nube).*
4.  **Arrancar el Lanzador Inteligente**:
    ```bash
    python lanzador.py
    ```
    *   *Verás que todos los módulos aparecen como "Omitidos". ¡Explícale a la clase que el reto del día es ponerlos todos en verde 🟢!*

---

## 🚶‍♂️ Paso a Paso del Desarrollo en Clase

### 📍 Paso 1: El Sensor Concreto (`miSensor.py`)
*Explicación teórica rápida: Heredamos de una clase abstracta `SensorBase` (Patrón Template Method) para reutilizar toda la lógica MQTT de red y solo preocuparnos por simular las lecturas.*

1.  Abre `miSensor.py` junto a tus estudiantes.
2.  Resuelve el **`TODO-S1`**: Importar `SensorBase`.
3.  Resuelve el **`TODO-S2`**: Sobrescribir `leerDatos()` retornando un diccionario con temperatura, pH y oxígeno disuelto simulados con rangos reales.
4.  Resuelve el **`TODO-S3`**: Instanciar los tres sensores (`estanque_a`, `estanque_b`, `estanque_c`) y ejecutarlos de forma asíncrona usando hilos (`threading.Thread`).
5.  **¡Guarda el archivo!**
6.  *Mira el Lanzador: Automáticamente se pondrá en verde y arrancará a simular sensores en consola.*

---

### 📍 Paso 2: Nodo de Borde / Computación en el Borde (`nodoEdge.py`)
*Explicación teórica rápida: ¿Por qué no enviamos todos los datos directo al servidor central? Porque saturaríamos la red con datos ruidos o idénticos. El nodo Edge filtra y promedia en el estanque antes de enviar.*

1.  Abre `nodoEdge.py` (copia de la plantilla lista para completar).
2.  Guía a la clase a través de los bloques del **`TODO-1` al `TODO-7`**:
    *   **TODO-1:** Inicializar las ventanas deslizantes (`deque` de tamaño 5) por variable.
    *   **TODO-2:** Capturar y convertir las variables.
    *   **TODO-3:** Calcular el promedio móvil con `statistics.mean()` (suavizado de ruido).
    *   **TODO-4:** Detectar anomalías (cambio instantáneo de > 20%).
    *   **TODO-5:** Aplicar el filtro delta (cambio de promedio > 5% para enviar).
    *   **TODO-6:** Calcular la tendencia del oxígeno disuelto (`SUBIENDO`/`BAJANDO`/`ESTABLE`).
    *   **TODO-7:** Construir el payload enriquecido e informar el ahorro de red (tasa de reducción).
3.  **¡Guarda el archivo!**
4.  *Mira el Lanzador: Detectará el módulo en verde y verás cómo el procesamiento Edge reduce drásticamente las publicaciones.*

---

### 📍 Paso 3: Persistencia en la Base de Datos (`baseDatos.py`)
*Explicación teórica rápida: El nodo central debe guardar los datos para el análisis histórico. Crearemos un esquema SQLite con buenas prácticas de no inyección SQL.*

1.  Abre `baseDatos.py`.
2.  Completa los bloques **`TODO-D1`** (creación de tablas SQLite), **`TODO-D2`** (inserción dinámica de datos del sensor) y **`TODO-D3`** (historial de comandos a los actuadores).
3.  **¡Guarda el archivo!**
4.  *El lanzador activará la base de datos de manera limpia.*

---

### 📍 Paso 4: El Cerebro / Reglas de Negocio (`nodoCentral.py`)
*Explicación teórica rápida: Recibe datos limpios del Edge y toma decisiones automáticas de encender o apagar el aireador (splash) utilizando histéresis.*

1.  Abre `nodoCentral.py`.
2.  Completa **`TODO-C1`**: Programar las reglas acuícolas basadas en los umbrales de oxígeno disuelto y temperatura con zona de histéresis (entre 4.0 y 4.8 mg/L).
3.  Completa **`TODO-C2`** y **`TODO-C3`**: Filtrar columnas del Edge para guardar en base de datos y disparar alertas inmediatas.
4.  **¡Guarda el archivo!**
5.  *El lanzador arrancará el Nodo Central y empezará a enrutar comandos de control.*

---

### 📍 Paso 5: Los Actuadores Físicos (`actuadores.py`)
*Explicación teórica rápida: Son los "músculos" del sistema. Escuchan los comandos MQTT del Nodo Central y ejecutan la acción (simulan pins GPIO).*

1.  Abre `actuadores.py`.
2.  Resuelve **`TODO-A1`** (guardar estado y simular relé físico) y **`TODO-A2`** (suscripción MQTT).
3.  **¡Guarda el archivo!**
4.  *El lanzador iniciará los actuadores. Verás cómo interactúan dinámicamente: Sensor publica -> Edge promedia -> Central decide -> Actuador ejecuta.*

---

### 📍 Paso 6: Monitoreo y Control Manual en el Dashboard Web (`dashboard.py`)
*Explicación teórica rápida: El administrador necesita ver todo en una consola web de alto nivel y poder forzar el encendido/apagado manualmente.*

1.  `dashboard.py` ya está completamente programado con Streamlit.
2.  Dado que los módulos anteriores ya están completados y en ejecución, el lanzador iniciará automáticamente el Dashboard en verde.
3.  Abre un navegador en: **`http://localhost:8501`**
4.  ¡Disfruta del show! Verás las métricas con colores dinámicos (rojo/verde según alertas), las gráficas en tiempo real y podrás hacer clic en "Encender/Apagar" para enviar comandos MQTT manuales directo a `actuadores.py`.

---

## 💡 Consejos para una Clase Exitosa
*   **Inspecciona el tráfico MQTT en vivo:** Mientras completan los pasos, abre otra terminal y ejecuta:
    ```bash
    mosquitto_sub -h localhost -t "#" -v
    ```
    Muéstrales cómo viajan los mensajes crudos (`sensores/estanque_a`) versus los procesados por el edge (`sensores/procesado/estanque_a`).
*   **Prueba de fallos:** Modifica manualmente los valores en `miSensor.py` para forzar un nivel de oxígeno < 3.0 mg/L y observa cómo inmediatamente se dispara la alerta crítica en el terminal del Nodo Central y los actuadores se encienden instantáneamente en el dashboard.
