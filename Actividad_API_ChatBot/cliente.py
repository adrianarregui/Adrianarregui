# ==============================================================================
# FICHERO: cliente.py (LA INTERFAZ VISUAL CON TTKBOOTSTRAP - VERSIÓN DASHBOARD)
# ------------------------------------------------------------------------------
# ¿Qué es?: Es la pantalla gráfica avanzada con la que interactúa el trabajador.
# Actúa como el "escaparate" o "volante" de tu aplicación (lo que el usuario ve).
# 1. Dibuja toda la ventana de diseño oscuro (el chat, la caja de texto, los botones).
# 2. Recoge la frase que el trabajador escribe y pulsa "Enviar".
# 3. Manda esa frase por la red (HTTP) hacia tu api.py.
# 4. Cuando la api le devuelve la respuesta, la escribe en la pantalla del chat.
# 5. Enciende o apaga las luces del panel derecho (Diagnóstico) dependiendo de
#    los filtros que la IA le haya chivado que ha usado.
# ==============================================================================
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import scrolledtext # Para un scroll automático más fluido
import requests

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA CONEXIÓN
# ------------------------------------------------------------------------------
API_URL = "http://127.0.0.1:8000/chat/"

# ------------------------------------------------------------------------------
# 2. LÓGICA DEL CHAT Y ACTUALIZACIÓN DE UI
# ------------------------------------------------------------------------------
def actualizar_indicadores_ia(filtros):
    """Actualiza las etiquetas del panel lateral según lo detectado por la IA."""
    # Actualizamos los textos de las etiquetas laterales con los datos del CORE
    lbl_prod.config(text=f"📦 Prod: {filtros.get('producto') or '---'}", 
                   bootstyle="info" if filtros.get('producto') else "default")
    
    lbl_pas.config(text=f"📍 Pasillo: {filtros.get('pasillo') or '---'}", 
                  bootstyle="warning" if filtros.get('pasillo') else "default")
    
    # Semáforo de stock: Cambiamos el estilo si el filtro está activo (True)
    lbl_bajo.config(bootstyle="danger" if filtros.get('bajo_stock') else "default")
    lbl_agot.config(bootstyle="secondary" if filtros.get('agotado') else "default")
    lbl_mucho.config(bootstyle="success" if filtros.get('mucho_stock') else "default")

def enviar_mensaje(event=None): # Añadimos event=None para que funcione con la tecla Enter
    """Extrae el texto del usuario y gestiona la comunicación con la API."""
    texto_usuario = entrada_texto.get()
    
    if not texto_usuario.strip():
        return 
    
    # Habilitamos la edición para insertar y luego bloqueamos para que sea solo lectura
    chat_box.configure(state='normal')
    chat_box.insert(tk.END, f"➤ Tú: {texto_usuario}\n", "usuario")
    
    entrada_texto.delete(0, tk.END) 
    
    try:
        # Petición a la API (POST)
        respuesta = requests.post(API_URL, json={"texto": texto_usuario})
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            # Mostramos la respuesta del bot
            chat_box.insert(tk.END, f"🤖 Bot: {datos['respuesta']}\n", "bot")
            
            # Extraemos filtros y actualizamos el panel lateral de diagnóstico
            filtros = datos.get('detalles_ia', {})
            actualizar_indicadores_ia(filtros)
            
            # Mostramos los filtros que el CORE detectó (Transparencia)
            info_ia = f"   [IA Filtros -> Bajo: {filtros.get('bajo_stock')} | Agotado: {filtros.get('agotado')} | Mucho: {filtros.get('mucho_stock')}]\n\n"
            chat_box.insert(tk.END, info_ia, "ia_info")
            
        else:
            chat_box.insert(tk.END, f"❌ Bot: Error en el servidor (Código {respuesta.status_code})\n\n", "error")
            
    except requests.exceptions.ConnectionError:
        chat_box.insert(tk.END, f"⚠️ Bot: Error fatal. ¿Está encendida la API en la terminal?\n\n", "error")
    
    # Bloquear de nuevo el chat para evitar que el usuario borre el historial
    chat_box.configure(state='disabled')
    chat_box.see(tk.END)

# ------------------------------------------------------------------------------
# 3. DISEÑO DE LA INTERFAZ GRÁFICA (Dashboard con Panedwindow)
# ------------------------------------------------------------------------------

# 3.1. Ventana Principal
# Usamos 'darkly' para un acabado más profesional de centro de control
app = ttk.Window(themename="darkly") 
app.title("Warehouse Intelligence AI - Dashboard de Inventario")
app.geometry("950x650")

# Contenedor principal con margen
main_frame = ttk.Frame(app, padding=15)
main_frame.pack(fill=BOTH, expand=True)

# 3.2. Cabecera (Título)
titulo_label = ttk.Label(main_frame, text="SISTEMA DE GESTIÓN INTELIGENTE", font=("Segoe UI", 20, "bold"), bootstyle="info")
titulo_label.pack(pady=(0, 20))

# 3.3. Cuerpo dividido (Panedwindow)
# Crea la división ajustable entre el chat y el panel de diagnóstico
cuerpo = ttk.Panedwindow(main_frame, orient=HORIZONTAL)
cuerpo.pack(fill=BOTH, expand=True)

# --- PANEL IZQUIERDO: CHAT ---
frame_chat = ttk.Labelframe(cuerpo, text=" Asistente Virtual ", padding=10)
cuerpo.add(frame_chat, weight=3)

# Área de Chat (Historial)
chat_box = scrolledtext.ScrolledText(frame_chat, font=("Segoe UI", 11), bg="#2b3e50", fg="white", borderwidth=0)
chat_box.pack(fill=BOTH, expand=True)

# Configuración de estilos mediante Tags
chat_box.tag_config("usuario", foreground="#00bc8c", font=("Segoe UI", 11, "bold")) # Verde Esmeralda
chat_box.tag_config("bot", foreground="#f39c12") # Naranja
chat_box.tag_config("ia_info", foreground="#95a5a6", font=("Consolas", 9, "italic")) # Gris
chat_box.tag_config("error", foreground="#e74c3c") # Rojo

# --- PANEL DERECHO: DIAGNÓSTICO IA ---
frame_ia = ttk.Labelframe(cuerpo, text=" Diagnóstico de Filtros ", padding=15)
cuerpo.add(frame_ia, weight=1)

lbl_prod = ttk.Label(frame_ia, text="📦 Prod: ---", font=("Segoe UI", 10))
lbl_prod.pack(anchor=W, pady=5)

lbl_pas = ttk.Label(frame_ia, text="📍 Pasillo: ---", font=("Segoe UI", 10))
lbl_pas.pack(anchor=W, pady=5)

ttk.Separator(frame_ia).pack(fill=X, pady=15)

# Indicadores de stock que cambian de color (Semáforo visual)
lbl_bajo = ttk.Label(frame_ia, text="⚠️ Bajo Stock", font=("Segoe UI", 10))
lbl_bajo.pack(anchor=W, pady=5)

lbl_agot = ttk.Label(frame_ia, text="🚫 Agotado", font=("Segoe UI", 10))
lbl_agot.pack(anchor=W, pady=5)

lbl_mucho = ttk.Label(frame_ia, text="✅ Mucho Stock", font=("Segoe UI", 10))
lbl_mucho.pack(anchor=W, pady=5)

# 3.4. Marco Inferior (Entrada + Botón)
frame_inferior = ttk.Frame(main_frame, padding=(0, 20, 0, 0))
frame_inferior.pack(fill=X)

entrada_texto = ttk.Entry(frame_inferior, font=("Segoe UI", 12), bootstyle="info")
entrada_texto.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

# Vincular la tecla Enter para que llame a enviar_mensaje()
entrada_texto.bind("<Return>", enviar_mensaje)

# Botón con estilo 'info' de ttkbootstrap
btn_enviar = ttk.Button(frame_inferior, text="CONSULTAR IA", command=enviar_mensaje, bootstyle="info", width=15)
btn_enviar.pack(side=RIGHT)

# Mensaje de Bienvenida inicial
chat_box.configure(state='normal')
chat_box.insert(tk.END, "🤖 Bot: Terminal conectada. Listo para procesar consultas de inventario.\n\n")
chat_box.configure(state='disabled')

# ------------------------------------------------------------------------------
# 4. ARRANCAR LA APLICACIÓN
# ------------------------------------------------------------------------------
app.mainloop()