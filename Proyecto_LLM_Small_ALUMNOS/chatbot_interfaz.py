import tkinter as tk
from tkinter import scrolledtext
import threading
import chatbot


class NovaBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaBot - IngeNova Datacenters")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)

        # =========================
        # CABECERA
        # =========================
        self.frame_superior = tk.Frame(root, padx=10, pady=10)
        self.frame_superior.pack(fill="x")

        self.lbl_titulo = tk.Label(
            self.frame_superior,
            text="🚀 INGENOVA DATACENTERS - Asistente NovaBot",
            font=("Arial", 16, "bold")
        )
        self.lbl_titulo.pack(anchor="w")

        self.lbl_info = tk.Label(
            self.frame_superior,
            text="Haz una consulta sobre normativas, edificios o preguntas generales.",
            font=("Arial", 10)
        )
        self.lbl_info.pack(anchor="w", pady=(5, 0))

        # =========================
        # ÁREA DE CHAT
        # =========================
        self.area_chat = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Consolas", 11),
            state="disabled",
            padx=10,
            pady=10
        )
        self.area_chat.pack(fill="both", expand=True, padx=10, pady=10)

        # =========================
        # BARRA DE ESTADO
        # =========================
        self.estado_var = tk.StringVar()
        self.estado_var.set("Listo.")
        self.lbl_estado = tk.Label(
            root,
            textvariable=self.estado_var,
            anchor="w",
            bd=1,
            relief="sunken",
            padx=8
        )
        self.lbl_estado.pack(fill="x", side="bottom")

        # =========================
        # ZONA INFERIOR DE ENTRADA
        # =========================
        self.frame_inferior = tk.Frame(root, padx=10, pady=10)
        self.frame_inferior.pack(fill="x")

        self.entrada_usuario = tk.Entry(self.frame_inferior, font=("Arial", 11))
        self.entrada_usuario.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entrada_usuario.bind("<Return>", self.enviar_mensaje)

        self.btn_enviar = tk.Button(
            self.frame_inferior,
            text="Enviar",
            width=12,
            command=self.enviar_mensaje
        )
        self.btn_enviar.pack(side="left")

        self.btn_limpiar = tk.Button(
            self.frame_inferior,
            text="Limpiar chat",
            width=12,
            command=self.limpiar_chat
        )
        self.btn_limpiar.pack(side="left", padx=(10, 0))

        # Mensaje inicial
        self.escribir_chat(
            "NovaBot",
            "Hola, soy tu asistente de IngeNova.\n"
            "Puedo responder sobre:\n"
            "- Normativas y documentación (RAG)\n"
            "- Datos de edificios y datacenters (SQL)\n"
            "- Conversación general\n"
        )

        self.entrada_usuario.focus()

    # ==========================================================
    # FUNCIONES DE INTERFAZ
    # ==========================================================
    def escribir_chat(self, remitente, mensaje):
        """Escribe una línea en el área de chat."""
        self.area_chat.config(state="normal")
        self.area_chat.insert(tk.END, f"{remitente}: {mensaje}\n\n")
        self.area_chat.see(tk.END)
        self.area_chat.config(state="disabled")

    def limpiar_chat(self):
        """Limpia el contenido del chat."""
        self.area_chat.config(state="normal")
        self.area_chat.delete(1.0, tk.END)
        self.area_chat.config(state="disabled")

        self.escribir_chat(
            "NovaBot",
            "Chat reiniciado. Puedes volver a preguntar lo que necesites."
        )
        self.estado_var.set("Listo.")

    def bloquear_interfaz(self):
        """Desactiva entrada y botón mientras se procesa la consulta."""
        self.entrada_usuario.config(state="disabled")
        self.btn_enviar.config(state="disabled")

    def desbloquear_interfaz(self):
        """Reactiva entrada y botón."""
        self.entrada_usuario.config(state="normal")
        self.btn_enviar.config(state="normal")
        self.entrada_usuario.focus()

    # ==========================================================
    # ENVÍO DE MENSAJES
    # ==========================================================
    def enviar_mensaje(self, event=None):
        """Recoge el texto del usuario y lanza el procesamiento en un hilo."""
        pregunta = self.entrada_usuario.get().strip()

        if not pregunta:
            return

        # Mostrar mensaje del usuario
        self.escribir_chat("🧑‍💻 Ingeniero", pregunta)

        # Limpiar caja y bloquear interfaz
        self.entrada_usuario.delete(0, tk.END)
        self.bloquear_interfaz()
        self.estado_var.set("NovaBot está pensando...")

        # Procesar en segundo plano para no congelar la ventana
        hilo = threading.Thread(target=self.procesar_consulta, args=(pregunta,), daemon=True)
        hilo.start()

    # ==========================================================
    # LÓGICA DEL CHAT
    # ==========================================================
    def procesar_consulta(self, pregunta):
        """
        Decide qué herramienta usar y obtiene la respuesta.
        Esta función corre en un hilo aparte.
        """
        try:
            # 1. Enrutar intención
            herramienta = chatbot.enrutador_llm(pregunta)

            # Actualizar interfaz desde el hilo principal
            self.root.after(
                0,
                lambda: self.estado_var.set(f"Herramienta detectada: {herramienta}")
            )

            # 2. Ejecutar la herramienta adecuada
            if herramienta == "RAG":
                respuesta = chatbot.consultar_normativa(pregunta)
            elif herramienta == "SQL":
                respuesta = chatbot.consultar_base_datos(pregunta)
            else:
                respuesta = chatbot.respuesta_general(pregunta)

            mensaje_final = f"[Herramienta usada: {herramienta}]\n{respuesta}"

            self.root.after(0, lambda: self.escribir_chat("🤖 NovaBot", mensaje_final))
            self.root.after(0, lambda: self.estado_var.set("Respuesta generada correctamente."))

        except Exception as e:
            self.root.after(
                0,
                lambda: self.escribir_chat(
                    "❌ Error",
                    f"Se produjo un error al generar la respuesta:\n{e}"
                )
            )
            self.root.after(0, lambda: self.estado_var.set("Ha ocurrido un error."))

        finally:
            self.root.after(0, self.desbloquear_interfaz)


if __name__ == "__main__":
    ventana = tk.Tk()
    app = NovaBotGUI(ventana)
    ventana.mainloop()