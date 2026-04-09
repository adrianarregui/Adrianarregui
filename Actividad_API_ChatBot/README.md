# TEMATICA ELEGIDA
En mi caso la tematica elegida es "ChatBot de Inventario"

# Chatbot de Inventario (Gestión de Almacén)

Este proyecto es un sistema inteligente diseñado para gestionar el stock de un almacén de recambios (baterías, filtros, neumáticos, etc.). El sistema permite consultar productos, conocer su ubicación exacta y calcular datos logísticos en tiempo real.

He implementado la temática de **Chatbot de Inventario**, donde el sistema actúa como un asistente que conecta al usuario con los datos reales de las estanterías

---

## Estructura del Proyecto

El sistema se divide en cuatro piezas que trabajan en equipo para garantizar que la lógica esté separada de los datos:

### 1. Base de Datos: `chatbot_almacen` (MySQL)
* **Función**: Almacenamiento permanente mediante XAMPP.

* **Tablas principales**:
    * **`productos`**: Guarda el nombre (ej. Batería 75A), la cantidad disponible y el enlace a su ubicación.
    * **`ubicaciones`**: Define las zonas físicas del almacén.
    * **`historial_consultas`**: Registra la actividad del chatbot para auditoría.



### 2. Módulo CORE: `core.py` (El Traductor Inteligente)

* **Función**: Es el "cerebro" del chatbot. No realiza búsquedas directas, sino que interpreta lo que el usuario quiere decir.
* **Lógica de Procesamiento**:
    * **Análisis de Intenciones**: Detecta si el usuario está preocupado por el stock bajo (palabras como "poco", "escaso") o si busca productos agotados ("cero", "sin stock").
    * **Extracción de Entidades**: Identifica automáticamente de qué producto se habla (batería, aceite, etc.) y en qué pasillo se encuentra mediante patrones de texto.
    * **Resultado**: Convierte una frase normal en una lista de filtros que la API puede entender perfectamente.



### 3. La API: `api.py` (El Servidor y Conector)
* **Tecnología**: FastAPI y SQLAlchemy.
* **Función**: Actúa como el "camarero" que recibe la petición del cliente y coordina al resto del sistema.
* **Proceso de la API**:
    1. Recibe el texto del usuario.
    2. Pide al **CORE** que extraiga los filtros de búsqueda.
    3. **Guarda el historial**: Registra la pregunta y los filtros en la tabla `historial_consultas`.
    4. Realiza una **consulta SQL dinámica** para encontrar exactamente lo que el usuario pidió.
    5. Devuelve la respuesta final lista para leer.



### 4. El Cliente: `cliente.py` (La Interfaz/Monitor)
* **Función**: Es el programa que utiliza el operario o cliente final.
* **Interfaz Profesional**: Diseñada con `ttkbootstrap`
* **Operación**: Envía las preguntas a la API y muestra la respuesta del bot en un chat interactivo.
* **Panel de Diagnóstico**: Incluye indicadores visuales (Semáforo de stock) que se iluminan en tiempo real según los filtros que la IA detecta en cada consulta (Bajo stock, Agotado, Mucho Stock).

---

## Cómo ejecutarlo

1. **Base de Datos**: Inicia MySQL en XAMPP y asegúrate de que la base de datos `chatbot_almacen` esté activa.
2. **Servidor API**: Ejecuta `python api.py`. Puedes acceder a la documentación interactiva en `http://127.0.0.1:8000/docs`.
3. **Monitor**: Ejecuta `python cliente.py` para visualizar el inventario y los cálculos en tiempo real.

---
