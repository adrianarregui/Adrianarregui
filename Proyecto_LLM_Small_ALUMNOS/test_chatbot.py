import chatbot

print("\n--- ROUTER TEST ---")
print("Ruta para consumo B:", chatbot.enrutador_llm('¿Cuál es el consumo del Edificio B?'))

print("\n--- SQL TEST ---")
print("Capacidad Edificio A:", chatbot.consultar_base_datos('¿Donde se ubica el Edificio A?'))

print("\n--- RAG TEST ---")
print("Resistencia estructural:", chatbot.consultar_normativa('¿Cuáles son los niveles de redundancia de suministro en España?'))
