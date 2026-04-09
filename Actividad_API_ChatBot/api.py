# ==============================================================================
# FICHERO: api.py (EL SERVIDOR Y PUENTE DE COMUNICACIÓN)
# ------------------------------------------------------------------------------
# ¿QUÉ HACE ESTE ARCHIVO DE MANERA SENCILLA?
# Actúa como el "camarero" o "puente" entre tu pantalla visual y tu base de datos.
# 1. Escucha lo que el usuario escribe en la interfaz gráfica (cliente.py).
# 2. Le pasa esa frase a 'core.py' para que le diga qué buscar (extrae los filtros).
# 3. Con esos filtros, va a tu base de datos (MySQL) y busca los productos exactos.
# 4. Guarda un registro de tu pregunta en la tabla 'historial_consultas'.
# 5. Empaqueta los productos encontrados y se los devuelve a la pantalla para que los leas.
# ==============================================================================

# 1. Importación de librerías
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import List
import uvicorn
import json
import core


#-------------------------------------
# 2. Configuración de la base de datos
URL_BASE_DATOS = "mysql+pymysql://root:@localhost:3306/chatbot_almacen"

try:
    # Intentamos encender el motor que conecta con MySQL
    motor = create_engine(URL_BASE_DATOS)
except Exception as e:
    print(f"Error al conectar: {e}")

# Creamos una "fábrica" de conexiones. Cada vez que alguien pregunte algo, usaremos una.
FabricaSesion = sessionmaker(bind=motor)


# Funcion que abre la puerta de la base de datos cuando llega una pregunta, y la cierra al terminar.
def obtener_db():
    db = FabricaSesion()
    try:
        yield db 
    finally:
        db.close()


#-------------------------------------------
# 3. Definición de los modelos de validación

# Le decimos a la API qué forma tiene que tener el mensaje que envía el usuario
class MensajeUsuario(BaseModel):
    texto: str

# Le decimos a la API qué forma tienen los productos que vamos a devolver
class ItemInventario(BaseModel):
    nombre: str
    cantidad: int
    pasillo: str
    
    
#-------------------------------
# 4. Creación de la APP

# Iniciamos FastAPI y le ponemos nombre
app_almacen = FastAPI(
    title="API ChatBot de Inventario",
    description="Consultas en lenguaje natural convertidas a filtros de DB",
    version="2.0.1"
)

# Evita que los navegadores bloqueen la conexión entre mi cliente visual y este servidor
app_almacen.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


#-------------------------------
# 5. Endpoints (puertas de entrada)

# Puerta 1: Si alguien entra a "/inventario/", le devolvemos TODOS los productos.
@app_almacen.get("/inventario/", response_model=List[ItemInventario])
def listar_inventario(db: Session = Depends(obtener_db)):
    try:
        # Consulta SQL simple: Trae todo
        sql = text("SELECT p.nombre, p.cantidad, u.pasillo FROM productos p JOIN ubicaciones u ON p.ubicacion_id = u.id")
        resultado = db.execute(sql)
        
        # Convertimos el resultado en una lista que la web pueda entender
        return [dict(fila._mapping) for fila in resultado]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {e}")


# Puerta 2: El CHAT. Aquí es donde llega el texto que escribes en la pantalla negra.
@app_almacen.post("/chat/")
def procesar_chat(mensaje: MensajeUsuario, db: Session = Depends(obtener_db)):
    
    # 1. Obtenemos el diccionario de filtros desde el CORE
    filtros = core.analizar_mensaje(mensaje.texto)
    
    # ---------------------------------------------------------
    # 2. GUARDAR EL HISTORIAL EN LA BASE DE DATOS
    # ---------------------------------------------------------
    
    try:
        # Convertimos el diccionario de palabras clave a texto (JSON) para que quepa en la columna de MySQL
        filtros_json = json.dumps(filtros)
        
        # Preparamos la instrucción SQL para insertar una nueva fila
        sql_log = text("INSERT INTO historial_consultas (pregunta, filtros_ia) VALUES (:p, :f)")
        # Ejecutamos la instrucción metiendo el texto del usuario y los filtros
        db.execute(sql_log, {"p": mensaje.texto, "f": filtros_json})
        
        # Sincronizamos y confirmamos
        db.flush() 
        db.commit() 
        print(f"✅ Log guardado: {mensaje.texto}") # Aviso de éxito en tu terminal
    except Exception as e:
        db.rollback()
        print(f"❌ ERROR CRÍTICO AL GUARDAR: {e}") # Aquí verás por qué falla realmente

    # 2. CONTROL DE ENTENDIMIENTO
    if not any([filtros.get("producto"), filtros.get("pasillo"), 
                filtros.get("bajo_stock"), filtros.get("agotado"), 
                filtros.get("mucho_stock")]):
        return {
            "respuesta": "No he entendido bien tu consulta. Prueba a preguntar por un producto, un pasillo o alertas de stock.",
            "detalles_ia": filtros,
            "datos_crudos": []
        }
    
    # 3. Construcción dinámica de la consulta SQL de productos
    query_base = """
        SELECT p.nombre, p.cantidad, u.pasillo 
        FROM productos p
        JOIN ubicaciones u ON p.ubicacion_id = u.id
        WHERE 1=1
    """
    parametros = {}

    # Si detectamos un producto, añadimos esa condición a la búsqueda
    if filtros.get("producto"):
        query_base += " AND LOWER(p.nombre) LIKE :prod"
        parametros["prod"] = f"%{filtros['producto']}%"

    # Si detectamos intención de bajo stock, añadimos esa regla
    if filtros.get("bajo_stock"):
        query_base += " AND p.cantidad > 0 AND p.cantidad < 10"
    
    # Si detectamos mucho stock
    if filtros.get("mucho_stock"):
        query_base += " AND p.cantidad > 10"
    
    # Si preguntan por agotados (0 unidades)
    if filtros.get("agotado"):
        query_base += " AND p.cantidad = 0"

    # Si detectamos un pasillo, lo añadimos
    if filtros.get("pasillo"):
        query_base += " AND u.pasillo LIKE :pas"
        # Buscamos 'Pasillo' seguido de cualquier cosa que contenga la letra detectada
        # Esto unirá "Pasillo" con la letra "A" o "B" que detecte la IA
        parametros["pas"] = f"Pasillo {filtros['pasillo']}%"

    try:
        # 4. Ejecutamos la consulta de búsqueda de productos
        resultado = db.execute(text(query_base), parametros).fetchall()
        lista_productos = [dict(f._mapping) for f in resultado]

        # 5. Construimos la respuesta de texto
        if not resultado:
            respuesta_final = "No he encontrado productos con esos filtros."
        else:
            nombres = [f"{f.nombre} ({f.cantidad} uds en {f.pasillo})" for f in resultado]
            respuesta_final = f"He encontrado: {', '.join(nombres)}"

        return {
            "respuesta": respuesta_final,
            "detalles_ia": filtros,
            "datos_crudos": lista_productos
        }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al filtrar inventario: {e}")
    
# -------------------------------
# 6. Arranque
if __name__ == "__main__":
    uvicorn.run("api:app_almacen", host="127.0.0.1", port=8000, reload=True)