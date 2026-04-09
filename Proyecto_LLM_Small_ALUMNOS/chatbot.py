# PROYECTO: NovaBot - Asistente de Ingeniería

# Este es un bot "híbrido" porque no hace solo una cosa, hace varias:

# 1. RAG: Lee documentos y busca respuestas en ellos.
# 2. SQL: Transforma tu texto en código SQL para sacar datos de una base de datos.
# 3. Memoria: Se acuerda de cosas de la charla actual y de días anteriores.
# 4. Enrutador: Un "cerebro" que lee tu pregunta y decide qué herramienta usar.


"""
PROYECTO: NovaBot - Asistente de Ingeniería

NovaBot - Chatbot híbrido con:
1. RAG sobre documentos (PDF, DOCX, MD)
2. Consulta a base de datos MySQL mediante generación de SQL con LLM
3. Memoria corta (historial reciente)
4. Memoria larga persistente con FAISS
5. Enrutado de intención tipo ReAct simplificado

La idea general del script es construir un asistente capaz de decidir
qué herramienta debe usar según la pregunta del usuario:
- Si la pregunta trata sobre normativa o documentación técnica -> RAG
- Si la pregunta trata sobre datos estructurados -> SQL
- Si la pregunta trata sobre algo recordado previamente -> MEMORIA
- Si no encaja en lo anterior -> conversación GENERAL

"""

import os # # Para movernos por las carpetas del ordenador
import fitz  # PyMuPDF: librería para leer archivos PDF
import docx  # Librería para leer documentos .docx de Word
import faiss  # Motor de búsqueda vectorial para embeddings
import numpy as np
from sentence_transformers import SentenceTransformer  # Modelo de embeddings
import ollama  # Cliente para hablar con modelos LLM locales mediante Ollama
from sqlalchemy import create_engine, text  # Para conectar con la base de datos
import pandas as pd
import warnings # Para ocultar avisos molestos de la consola
import tiktoken

# Omitimos warnings que no aportan valor al flujo didáctico del script.
# Esto hace que la consola quede más limpia.
warnings.filterwarnings('ignore')

# ==========================================
# 1. PREPARACIÓN DE RAG
# ==========================================

print("Cargando modelo de embeddings y documentos RAG...")
# TODO: Inicializar SentenceTransformer 'all-MiniLM-L6-v2'
# El SenteceTransformer transforma el texto en vectores numéricos --> embedding
# que luego podemos comparar matemáticamente para encontrar similitud semántica con
# la pregunta del usuario.

# Cargamos el modelo que convierte texto en "coordenadas matemáticas" (Vectores/Embeddings)
# Así la IA sabe si dos textos hablan de lo mismo aunque usen palabras distintas.
modelo_emb = SentenceTransformer("all-MiniLM-L6-v2") 

# -- Funciones para leer diferentes tipos de archivos --
def leer_pdf(ruta):
    """Extrae texto de un PDF.
    - Abre el pdf con PyMuPDF (fitz)
    - Recorre cada página
    - Extrae su texto y lo concatena en un sólo string
    """
    texto = ""
    try:
        documento = fitz.open(ruta)
        for pagina in documento:
            texto += pagina.get_text() + "\n"
    except Exception as e:
        print(f"Error en ruta: {ruta}: {e}")
    return texto
    

def leer_docx(ruta):
    """Extrae texto de un Word."""
    texto = ""
    try:
        documento = docx.Document(ruta)
        for pagina in documento.paragraphs:
            texto += pagina.text + "\n"
    except Exception as e:
        print(f"Error en ruta: {ruta}: {e}")
    return texto

def leer_md(ruta):
    """Extrae texto de un Markdown."""
    texto = ""
    try:
        with open(ruta, "r", encoding="utf-8") as file:
            texto = file.read()
    except Exception as e:
        print(f"Error en ruta: {ruta}: {e}")
    return texto

# Carpeta donde guardamos los documentos que servirán de base para el RAG.
docs_path = "documentos"

# Aquí iremos acumulando el texto de todos los documentos encontrados.
texto_total = ""

# TODO: Crear bucle que recorra la carpeta 'documentos' y use las funciones anteriores
# Recorremos todos los archivos de la carpeta y decidimos cómo leer cada uno
# según su extensión.

# Recorremos la carpeta. Si es PDF usa leer_pdf, si es Word usa leer_docx, etc.
for archivo in os.listdir(docs_path):
    ruta = os.path.join(docs_path, archivo)
    
    if archivo.endswith(".pdf"):
        print(f"    -> Leyendo PDF: {archivo}")
        texto_total += leer_pdf(ruta)
        
    elif archivo.endswith(".docx"):
        print(f"    -> Leyendo DOCX (WORD): {archivo}")
        texto_total += leer_docx(ruta)
        
    elif archivo.endswith(".md"):
        print(f"    -> Leyendo MD: {archivo}")
        texto_total += leer_md(ruta)
    
# Chunks tokenizados:
def chunk_por_tokens(texto, tokens_max=100, overlap=30):
    """    
    Divide un texto largo en fragmentos más pequeños (chunks) por número de tokens.

    Parámetros:
        texto (str): texto completo a fragmentar.
        tokens_max (int): máximo número de tokens por fragmento.
        overlap (int): número de tokens solapados entre fragmentos consecutivos.

    Devuelve:
        list[str]: lista de fragmentos de texto.

    Por qué esto es importante:
    Los LLM y los sistemas RAG no suelen trabajar bien con documentos enormes
    enviados de golpe. Lo normal es partir el texto en trozos pequeños.
    
    Qué significa "overlap":
    - Si un fragmento termina en una idea importante, el siguiente fragmento
      repite una parte de esa zona.
    - Esto evita perder contexto justo en los bordes de los chunks.

    Proceso:
    1. Tokenizamos el texto.
    2. Vamos cogiendo ventanas de tokens.
    3. Decodificamos cada ventana a texto.
    4. Solo guardamos los fragmentos que tengan contenido razonable.
    """
    # TODO: Implementar lógica de tokenización con tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(texto)
    
    chunks = []
    i = 0
    
    while i < len(tokens):
        chunk = encoder.decode(tokens[i:i + tokens_max])
        chunks.append(chunk)
        i += (tokens_max - overlap)
    
    return chunks

print("Generando fragmentos de texto (chunks)...")
chunks_rag = chunk_por_tokens(texto_total)

print(f"Generando embeddings para {len(chunks_rag)} fragmentos de normativa...")
# TODO: Crear vectores_rag e inicializar indice_faiss (IndexFlatL2)
# Convertimos cada chunk en un vector numérico
vectores_rag = modelo_emb.encode(chunks_rag)

# shape[1] representa el número de dimensiones del embedding --> MiniLLM es 384
dimensiones = vectores_rag.shape[1]

# Utilizamos estas dimensiones para crear el índice FAISS para búsqueda por distancia
indice_faiss = faiss.IndexFlatL2(dimensiones)

# Indexamos los chunks para luego poder buscar los más parecidos a la pregunta del usuario
indice_faiss.add(np.array(vectores_rag))

# ==========================================
# 1.5 MEMORIA DEL CHAT (PERSISTENTE)
# ==========================================

# Memoria corta (volátil):
# Aquí guardamos los últimos mensajes de la conversación actual.
# Sirve para mantener algo de contexto reciente.
historial_corto = []

# Memoria larga (persistente):
# Archivos donde persistiremos la memoria larga en disco.
# - Un archivo .index para FAISS
# - Un archivo .txt para guardar los textos originales
F_MEM_INDEX = os.path.join("database", "memoria_larga.index")
F_MEM_TEXTOS = os.path.join("database", "memoria_larga.txt")

fragmentos_memoria = []

def inicializar_memoria_larga():
    """
    Carga la memoria persistente desde disco si existe.
    Si no existe, crea una nueva memoria vacía.
    """
    os.makedirs("database", exist_ok=True)
    global fragmentos_memoria, indice_memoria 
    # TODO: Carga faiss.read_index si los archivos existen
    if os.path.exists(F_MEM_INDEX) and os.path.exists(F_MEM_TEXTOS):
        print("     --> Cargando memoria persistente...")
        indice_memoria = faiss.read_index(F_MEM_INDEX)
        
        with open(F_MEM_TEXTOS, "r", encoding="utf-8") as fichero:
            fragmentos_memoria = [linea.strip() for linea in fichero.readlines()]
            
    else:
        print("     --> Inicializando una nueva memoria...")
        # Como no existe nada en disco, creamos un índice vacío
        indice_memoria = faiss.IndexFlatL2(dimensiones)

def redactar_informacion_sensible(texto):
    """
    Security by Design:
    pide al LLM que oculte información sensible antes de almacenarla.

    Ejemplos de datos sensibles:
    - Contraseñas
    - Claves
    - Pines
    - Accesos privados

    La idea no es guardar datos delicados tal cual en la memoria persistente.
    """
    prompt = (
        "Eres un filtro de seguridad automatizado. Tu ÚNICA tarea es CENSURAR información sensible "
        "(como contraseñas, pines o claves de acceso) del siguiente texto, sustituyéndola por ****. "
        "Si NO hay ninguna información sensible en el texto, debes devolver el texto EXACTAMENTE IGUAL, sin cambiar nada. "
        "NO des explicaciones, NO te disculpes y NO añadas comentarios. Solo devuelve el texto resultante.\n\n"
        f"TEXTO: {texto}"
    )
    print("  [Seguridad]: Redactando información sensible...")
    # TODO: Llamar a ollama.chat con un prompt de seguridad
    respuesta = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role":"user", "content":prompt}]
    )
    
    return respuesta["message"]["content"].strip()

def guardar_en_memoria_larga(pregunta, respuesta):
    """
    Guarda una interacción en la memoria larga persistente.

    Flujo:
    1. Junta pregunta y respuesta en un único texto.
    2. Redacta/oculta información sensible.
    3. Genera embedding del texto seguro.
    4. Lo añade al índice FAISS.
    5. Lo guarda en disco para futuras ejecuciones.

    Así logramos una memoria persistente entre sesiones.
    """
    # TODO: Unir P+R, redactar, vectorizar y guardar en archivos
    texto_puro = f"Pregunta: {pregunta} | Respuesta: {respuesta}"
    
    # Antes de guardar, aplica seguridad
    texto_seguro = redactar_informacion_sensible(texto_puro)
    
    # Vectorizamos 
    vector = modelo_emb.encode([texto_seguro])
    indice_memoria.add(np.array(vector))
    
    # Añadimos el texto ya una vez sin información sensible
    # a la memoria a largo plazo
    fragmentos_memoria.append(texto_seguro)
    
    # Actualizamos el índice faiss y el texto plano
    faiss.write_index(indice_memoria, F_MEM_INDEX)
    with open(F_MEM_TEXTOS, "a", encoding="utf-8") as fichero:
        fichero.write(texto_seguro + "\n")

def recuperar_memoria_relevante(pregunta):
    """
    Busca en la memoria larga el recuerdo más parecido a la pregunta actual.

    Devuelve:
        str: texto formateado con el recuerdo encontrado, o cadena vacía.

    Proceso:
    - Embebemos la nueva pregunta.
    - Buscamos el vector más cercano en FAISS.
    - Si la distancia es suficientemente baja, lo consideramos relevante.

    Nota importante:
    En un índice L2, cuanto menor sea la distancia, más similares son los vectores.
    Por eso aquí se usa un umbral: si la distancia es pequeña, recuperamos ese recuerdo.
    """
    # TODO: Búsqueda en indice_memoria con un umbral de distancia
    if len(fragmentos_memoria) == 0:
        return ""
    
    vector_pregunta = modelo_emb.encode([pregunta])
    
    D, I = indice_memoria.search(vector_pregunta, k=1)
    
    if D[0][0] < 0.8:
        return f"\nRECUERDO RECUPERADO:\n{fragmentos_memoria[I[0][0]]}\n"
    
    return ""

def debe_guardar_memoria(pregunta, respuesta):
    """
    Usa el LLM para razonar si esta interacción contiene datos que valga la pena
    guardar a largo plazo (códigos, preferencias, cambios de estado).
    """
    prompt = (
        "Eres un gestor de memoria para NovaBot. Tu objetivo es detectar si el usuario "
        "ha proporcionado datos concretos (códigos, nombres, preferencias técnicas, "
        "instrucciones específicas) que deban recordarse en el futuro.\n\n"
        "Analiza la conversación:\n"
        f"Ingeniero: {pregunta}\nNovaBot: {respuesta}\n\n"
        "¿Contiene información que deba ser guardada permanentemente? "
        "Responde SOLO con la palabra 'SI' o 'NO'."
    )
    # TODO: Preguntar al LLM y devolver True/False
    respuesta = ollama.chat(model="llama3.2:3b", 
                            messages=[
                                {"role":"user", "content": prompt}
                            ])
    
    decision = respuesta["message"]["content"].upper().strip().replace(".", "")
    
    print(f"    [DEBUG] ¿Debe guardar?: -> {decision}")
    
    return "SI" in decision or "SÍ" in decision

def debe_consultar_memoria(pregunta):
    """
    Primer paso agéntico: El LLM decide si para responder a esta pregunta
    necesita consultar su baúl de recuerdos almacenados.
    """
    prompt = (
        "Como asistente de ingeniería, analiza si la siguiente DEBE buscar datos previos "
        "o preferencias en su memoria para responder con precisión.\n"
        f"Pregunta: {pregunta}\n"
        "¿Necesitas consultar tus recuerdos? Responde SOLO con la palabra 'SI' o 'NO'."
    )

    # TODO: Preguntar al LLM y devolver True/False
    respuesta = ollama.chat(model="llama3.2:3b", 
                            messages=[
                                {"role":"user", "content": prompt}
                            ])
    
    decision = respuesta["message"]["content"].upper().strip().replace(".", "")
    
    print(f"    [DEBUG] ¿Debe consultar?: -> {decision}")
    
    return "SI" in decision or "SÍ" in decision

# Cargamos o inicializamos la memoria larga al arrancar el programa.
inicializar_memoria_larga()


# ==========================================
# 2. PREPARACIÓN BASE DE DATOS (SQL)
# ==========================================

print("Conectando a Base de Datos de Edificios...")
# TODO: Crear engine de SQLAlchemy para MySQL
# Conecta Python a tu base de datos MariaDB/MySQL de XAMPP usando SQLAlchemy
motor_db = create_engine("mysql+pymysql://root:@localhost/ingenova_db")

# Esquema resumido que le damos al LLM para que sepa qué tabla y columnas existen.
# Esto es clave en Text-to-SQL: si el modelo no sabe qué estructura tiene la base,
# se inventará columnas o tablas.
ESQUEMA_SQL = """
Tabla: edificios_datacenter
Columnas:
- id (INT, Autoincremental, PK)
- nombre (VARCHAR 50): Nombre del edificio (ej: 'Edificio A', 'Edificio B', etc.)
- ubicacion (VARCHAR 100): Ciudad o zona (ej: 'Madrid Norte', 'Barcelona')
- capacidad_racks (INT): Número total de racks disponibles.
- consumo_electrico_mw (DECIMAL 5,2): Consumo en Megavatios (MW).
- estado_operativo (VARCHAR 20): Estado actual (ACTIVO, MANTENIMIENTO, CONSTRUCCION).
"""

def es_query_segura(sql):
    """
    Security by Design:
    bloquea consultas SQL potencialmente peligrosas.

    Objetivo:
    - Permitir consultas SELECT
    - Permitir modificaciones controladas INSERT y UPDATE
    - Bloquear operaciones destructivas o de estructura

    Esto no sustituye un sistema profesional de seguridad,
    pero es una buena capa mínima para un ejemplo didáctico.
    """
    prohibidos = ["DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "REPLACE", "GRANT", "REVOKE"]
    
    sql_upper = sql.upper()
    
    for palabra in prohibidos:
        if palabra in sql_upper:
            return False
        
    permitidos = ["SELECT", "INSERT", "UPDATE"]
    
    for palabra in permitidos:
        if palabra in sql_upper:
            return True
    
    return False

# ==========================================
# 3. AGENTES Y HERRAMIENTAS (TOOLS)
# ==========================================

def consultar_normativa(pregunta, recuerdo=""):
    """
    Herramienta RAG usando:
    - búsqueda semántica con FAISS
    - contexto documental recuperado
    - memoria relevante (opcional, si se encontró en el pre-chequeo)
    - historial corto de conversación
    - generación final con Ollama
    """
    # TODO: Búsqueda en faiss, crear prompt con contexto y llamar a ollama
    pregunta_vectorizada = modelo_emb.encode([pregunta])
    
    # Vamos a recuperar los 3 fragmentos más cercanos del RAG
    # Tanto D como I tienen forma: X[Y][Z] siendo Y el número de preguntas
    # y Z los chunks más cercanos.
    D, I = indice_faiss.search(pregunta_vectorizada, k=3)
    
    # Reconstruimos el contexto textual a partir de los resultados
    # i -> I[0][0], I[0][1], I[0][2] 
    # CORREGIR
    contexto = "\n".join(chunks_rag[i] for i in I[0])
    
    # Si acabamos de empezar y no hay recuerdo, metemos la memoria relevante a la pregunta
    if not recuerdo:
        recuerdo = recuperar_memoria_relevante(pregunta)
    
    # Construimos la conversacion para el modelo
    mensaje = [
        {
            "role":"system",
            "content": (
                "Eres un ingeniero jefe de IngeNova experto en normativas."
                "Responde basándote en el contexto del documento y en tus recuerdos"
                "si son relevantes.\n"
                f"CONTEXTO DOCUMENTOS: {contexto}\nCONTEXTO RECUERDOS: {recuerdo}"
            )
        }
    ]
    
    # Añadimos el historial a corto plazo para mantener el contexto conversacional
    mensaje.extend(historial_corto)
    
    # Finalmente le añadimos la pregunta del usuario
    mensaje.append({"role":"user", "content":pregunta})
    
    respuesta = ollama.chat(model="llama3.2:3b", messages=mensaje)
    
    return respuesta["message"]["content"]

def consultar_base_datos(pregunta):
    """
    Herramienta Text-to-SQL avanzada con:
    - generación de SQL mediante LLM
    - validación de seguridad
    - ejecución real en MySQL
    - reinterpretación amigable de resultados con otro paso LLM

    Idea general:
    El usuario pregunta en lenguaje natural y el sistema intenta:
    1. Traducir la pregunta a SQL
    2. Validar que la consulta sea segura
    3. Ejecutarla
    4. Traducir el resultado técnico a lenguaje más natural
    """
    # TODO: Generar SQL, validar seguridad, ejecutar en pandas y responder
    # 1. Generar la consulta SQL utilizando nuestro modelo LLM
    prompt_sql = (
        "Eres un experto en MySQL. Genera EXCLUSIVAMENTE la consulta SQL (SELECT, INSERT o UPDATE)."
        f"Esquema: {ESQUEMA_SQL}\nSólo devuelve el código SQL sin markdown ni explicaciones."
    )
    
    mensaje = [
        {"role":"system", "content":prompt_sql},
        {"role":"user", "content": f"Pregunta: {pregunta}"}
    ]
    
    respuesta = ollama.chat(model="llama3.2:3b", messages=mensaje)
    
    # 2. Limpiamos por el si el modelo ha metido espacios o marcado
    consulta_llm = respuesta["message"]["content"].strip().replace("```sql", "").replace("```", "").strip()
    
    # 3. Comprobamos que es segura
    if not es_query_segura(consulta_llm):
        return f"ALERTA DE SEGURIDAD: Bloqueando: {consulta_llm}"
    
    # 4. Probamos la consulta
    try:
        consulta_upper = consulta_llm.upper()
        
        with motor_db.connect() as conexion:
            
            # Si la consulta es un SELECT, usamos pandas para obtener el resultado
            if consulta_upper.startswith("SELECT"):
                resultado = pd.read_sql(text(consulta_llm), conexion)
                
                if resultado.empty:
                    return f"No hay datos de la BD para: {pregunta}"
            
                # Añadiremos también la posible memoria relevante
                recuerdo = recuperar_memoria_relevante(pregunta)
                
                # Obtenermos la respuesta natural
                mensaje = [
                    {
                        "role":"system",
                        "content": "Eres un analista de datos de IngeNova."
                        "Responde utilizando los siguientes datos reales de la base de datos"
                        "y recuerdos de la memoria persistente."
                        f"Estos datos reales: {resultado.to_string(index=False)}"
                        f"Puede ser que necesites estos recuerdos: {recuerdo}"
                    }
                ]
                
                # Añadimos el historial a corto plazo para mantener el contexto conversacional
                mensaje.extend(historial_corto)
                
                # Finalmente le añadimos la pregunta del usuario
                mensaje.append({"role":"user", "content":pregunta})
                
                respuesta = ollama.chat(model="llama3.2:3b", messages=mensaje)
                
                return respuesta["message"]["content"]
            
            else:
                # Caso INSERT o UPDATE
                # Solo ejecutamos la operación y confirmamos
                conexion.execute(text(consulta_llm)) # Prepara el cambio
                conexion.commit() # Aplica el cambio de forma definitiva en la bd
                
                return f"Operación SQL realizada: '{consulta_llm}'"
                
    except Exception as e:
        return f"Error SQL: {consulta_llm}: {e}."
    
    
    return "Respuesta SQL no implementada."

def consultar_memoria_personal(pregunta):
    """
    Herramienta específica para recuperar información guardada en memoria larga.

    Se usa cuando el usuario pregunta por algo dicho anteriormente,
    por una preferencia, por una instrucción guardada, etc.
    """
    recuerdo = recuperar_memoria_relevante(pregunta)
    
    if not recuerdo:
        return "No tengo recuerdos en mi memoria sobre este tema."
    
    mensaje = [
        {
            "role":"system",
            "content":f"Basándote en este recuerdo, responde al usuario: \n{recuerdo}"
        }
    ]
    
    respuesta = ollama.chat(model="llama3.2:3b", messages = mensaje)
    return respuesta["message"]["content"]

def respuesta_general(pregunta):
    """
    Conversación general del asistente.

    Esta función se usa para:
    - saludos
    - charla normal
    - despedidas
    - preguntas que no encajan claramente en RAG, SQL o MEMORIA

    Aun así, aprovecha memoria relevante e historial corto.
    """
    recuerdo = recuperar_memoria_relevante(pregunta)

    mensaje = [
        {
            "role":"system",
            "content":f"Eres NovaBot de IngeNova Datacenters. Responde de manera amable al usuario"
            "Si te pregunta sobre tus funciones: puedes consultar documentación de la empresa, de "
            "la base de datos o dar respuestas generales. "
            f"Si lo necesitas, puedes recurrir a la memoria persistente: \n{recuerdo}"
            "No te inventes nada sobre lo que no tengas información, en su lugar, pregunta al usuario."
        }
    ]
    
    mensaje.extend(historial_corto)
    mensaje.append({"role":"user", "content":pregunta})
    
    respuesta = ollama.chat(model="llama3.2:3b", messages = mensaje)
    return respuesta["message"]["content"]
    

# ==========================================
# 4. ENRUTADOR (ROUTER)
# ==========================================

def enrutador_llm(pregunta, recuerdo=""):
    """
    Clasifica la intención de la pregunta y decide qué herramienta usar.
    
    Acepta un 'recuerdo' opcional pero ya NO decide sobre MEMORIA como herramienta,
    ya que la memoria se trata ahora como contexto previo (pre-chequeo).
    """
    contexto_extra = f"\nRECUERDO DEL PASADO:\n{recuerdo}" if recuerdo else ""
    
    prompt_router = (
        "Clasifica la intención del usuario. Responde SOLO con una palabra:\n"
        "- RAG: Normativas, seguridad, electricidad o comunicaciones.\n"
        "- SQL: Datos de edificios, consumo, racks o estado de la planta.\n"
        "- GENERAL: Saludos, charla normal o despedidas.\n\n"
        f"CONTEXTO DE MEMORIA PERSISTENTE ENCONTRADO (Usa esto para decidir mejor): {contexto_extra}"
        f"CONTEXTO DE MEMORIA RECIENTE (Usa esto para añadir contexto): {historial_corto}"
    )
    # TODO: Prompt de clasificación y llamada a ollama
    
    mensaje = [
        {"role": "system", "content":prompt_router},
        {"role": "user", "content": pregunta}
    ]

    respuesta = ollama.chat(model="llama3.2:3b", messages = mensaje)

    decision = respuesta["message"]["content"].strip().upper()
    
    if "RAG" in decision:
        return "RAG"
    
    if "SQL" in decision:
        return "SQL"
        
    return "GENERAL"

# ==========================================
# 5. BUCLE PRINCIPAL (CLI)
# ==========================================

def iniciar_chat():
    """
    Inicia el bucle principal del chatbot en consola (CLI).

    Flujo de cada iteración:
    1. Leer entrada del usuario
    2. Comprobar si quiere salir
    3. Enrutar la pregunta a la herramienta adecuada
    4. Ejecutar la herramienta
    5. Mostrar la respuesta
    6. Actualizar historial corto
    7. Guardar en memoria larga si procede
    """
    print("\n" + "="*50)
    print("🚀 INGENOVA DATACENTERS - Asistente NovaBot 🚀")
    print("="*50)
    print("Escribe 'salir' para terminar la conversación.")

    while True:
        usuario = input("\n🧑‍💻 Ingeniero: ")

        # Comandos para finalizar el chat
        if usuario.strip().lower() in ['salir', 'exit', 'quit']:
            print("🤖 NovaBot: ¡Hasta la próxima resolución de incidencias!")
            break

        # Si el usuario pulsa Enter sin escribir nada, simplemente seguimos
        if not usuario.strip():
            continue

        # 1. PASO PREVIO: ¿Necesita consultar su memoria?
        # Enfoque agéntico: razonar antes de actuar.
        recuerdo_agente = ""
        if debe_consultar_memoria(usuario):
            print("🤖 NovaBot: Consultando memoria larga...")
            recuerdo_agente = recuperar_memoria_relevante(usuario)

        # 2. Enrutamiento:
        # primero decidimos qué herramienta usar, pasándole el posible recuerdo.
        print("🤖 NovaBot pensando...", end="\r")
        herramienta = enrutador_llm(usuario, recuerdo_agente)

        # 3. Acción:
        # según la herramienta elegida, llamamos a una función distinta.
        try:
            if herramienta == "RAG":
                respuesta = consultar_normativa(usuario, recuerdo_agente)

            elif herramienta == "SQL":
                # La herramienta SQL puede beneficiarse del recuerdo si incluye nombres de edificios
                respuesta = consultar_base_datos(usuario)

            else:
                respuesta = respuesta_general(usuario)

            print(f"🤖 NovaBot [{herramienta}]: {respuesta}")

            # 4. ACTUALIZAR MEMORIA CORTA
            # Guardamos la interacción reciente para mantener contexto conversacional.
            historial_corto.append({'role': 'user', 'content': usuario})
            historial_corto.append({'role': 'assistant', 'content': respuesta})

            # Limitamos el historial a 10 elementos.
            if len(historial_corto) > 10:
                historial_corto.pop(0)
                historial_corto.pop(0)

            # 5. ACTUALIZAR MEMORIA LARGA (INTELIGENTE)
            # Ya no buscamos palabras clave. Preguntamos al LLM si esto es importante.
            if debe_guardar_memoria(usuario, respuesta):
                guardar_en_memoria_larga(usuario, respuesta)
                print("💡 [Sistema]: He considerado que esta información es importante y la he guardado.")

        except Exception as e:
            print(f"\n❌ Error: {e}")


# Este bloque hace que el chat se inicie solo si ejecutamos directamente este archivo.
# Si el script se importa desde otro módulo, este bloque no se ejecuta.
if __name__ == "__main__":
    iniciar_chat()