# ==============================================================================
# FICHERO: core.py (EL CEREBRO DEL CHATBOT)
# ------------------------------------------------------------------------------
# ¿QUÉ HACE ESTE ARCHIVO DE MANERA SENCILLA?
# Actúa como el "traductor" de tu sistema. 
# 1. Coge la frase normal que escribe el usuario (Ej: "¿quedan baterías en el pasillo B?").
# 2. Busca palabras clave dentro de esa frase usando reglas de texto.
# 3. Convierte esas palabras en una lista de "filtros" o interruptores (Ej: producto="bateria", pasillo="B").
# 4. Le entrega esos filtros ordenados a la API para que ella haga la búsqueda real.
# ==============================================================================

# Importamos la librería 're' (Expresiones Regulares).
# Que sirve para buscar palabras dentro de frases de manera avanzada.
import re

# Función principal (Recibirá el mensaje del usuario)
def analizar_mensaje(mensaje):
    """
    Analiza la frase y devuelve una estructura de datos lista para
    convertirse en una consulta SQL con filtros.
    """
    
    # 1. Convertimos todo el mensaje a minúsculas. 
    # Para facilitar la busqueda
    mensaje = mensaje.lower()
    
    # Estructura de filtros por defecto (nada seleccionado)
    filtros = {
        "intencion": "consulta_general",
        "producto": None,
        "bajo_stock": False,
        "agotado": False,  # <-- NUEVO FILTRO PARA 0 UNIDADES
        "mucho_stock": False,  # <-- NUEVO FILTRO
        "pasillo": None
    }
    
    # 2. DETECTAR INTENCIÓN DE STOCK BAJO (Heurística de IA):
    # Si el usuario usa palabras de escasez, activamos el filtro de cantidad.
    # Ejemplo: "¿Qué productos se están agotando?"
    # Añadimos agotad: así detectará agotado, agotada, agotados, agotadas
    if re.search(r'(poco|bajo|escaso|quedan pocos|critico)', mensaje):
        filtros["intencion"] = "consulta_stock_bajo"
        filtros["bajo_stock"] = True
    
    if re.search(r'(agotad|cero|ningun|sin stock)', mensaje):
        filtros["intencion"] = "consulta_agotado"
        filtros["agotado"] = True
    
    # NUEVA REGLA: DETECTAR INTENCIÓN DE MUCHO STOCK (> 10 uds)
    if re.search(r'(mucho|bastante|sobrado|lleno|exceso)', mensaje):
        filtros["intencion"] = "consulta_stock_alto"
        filtros["mucho_stock"] = True
        
    # 3. EXTRAER EL PASILLO (Entidad de Ubicación):
    # Buscamos el patrón "pasillo X" o simplemente la letra/número si va tras "pasillo".
    # Ejemplo: "¿Hay baterias en el pasillo 1?"
    match_pasillo = re.search(r'pasillo\s+(\d+|[a-z])', mensaje)
    if match_pasillo:
        filtros["pasillo"] = match_pasillo.group(1).upper()
    
    # 4. EXTRAER EL PRODUCTO (Entidad de Inventario):
    # Lista basada en los productos reales de tu base de datos (Bateria, Filtro, etc.).
    productos_conocidos = ['bateria', 'filtro', 'neumatico', 'pastilla', 'aceite']
    
    for prod in productos_conocidos:
        # Si el nombre del producto está en la frase...
        if prod in mensaje:
            filtros["producto"] = prod
            break # Salimos al encontrar el primero
            
    # Finalmente, devolvemos el objeto de filtros completo.
    # Ejemplo de salida: {"intencion": "consulta_stock_bajo", "producto": "bateria", ...}
    return filtros