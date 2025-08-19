import pandas as pd
import difflib

# Cargar datos de LaLiga (scraping)
df_laliga = pd.read_csv("data_laliga.csv")

# Cargar tu plantilla
df_mi = pd.read_csv("mi_plantilla.csv")

# Lista para guardar coincidencias
jugadores_encontrados = []

# Normalizar función para comparar nombres
def buscar_jugador(nombre):
    # Buscar coincidencia más cercana
    coincidencias = difflib.get_close_matches(nombre, df_laliga["Nombre"], n=1, cutoff=0.6)
    return coincidencias[0] if coincidencias else None

# Comparar jugadores
for _, jugador in df_mi.iterrows():
    nombre_normalizado = buscar_jugador(jugador["Nombre"])
    if nombre_normalizado:
        datos_jugador = df_laliga[df_laliga["Nombre"] == nombre_normalizado].iloc[0]
        jugadores_encontrados.append({
            "Mi_nombre": jugador["Nombre"],
            "Nombre_web": nombre_normalizado,
            "Equipo": datos_jugador["Equipo"],
            "Probabilidad": datos_jugador["Probabilidad"],
            "Posicion": jugador["Posicion"],
            "Precio": jugador["Precio"]
        })
    else:
        print(f"[NO ENCONTRADO] {jugador['Nombre']}")

# Ordenar jugadores_encontrados por posición: POR, DEF, CEN/MED, DEL
orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "MED": 2, "DEL": 3}
jugadores_encontrados = sorted(jugadores_encontrados, key=lambda x: orden_pos.get(x["Posicion"].upper(), 99))

# Guardar resultados
df_final = pd.DataFrame(jugadores_encontrados)
df_final.to_csv("mi_plantilla_filtrada.csv", index=False, encoding="utf-8")
print("[OK] Tu plantilla filtrada se ha guardado en mi_plantilla_filtrada.csv")