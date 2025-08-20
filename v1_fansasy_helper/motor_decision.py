import pandas as pd

# Parámetros de formación
MIN_DEF, MAX_DEF = 3, 5
MIN_CEN, MAX_CEN = 3, 5
MIN_DEL, MAX_DEL = 1, 3
NUM_POR = 1
NUM_JUGADORES = 11

# Cargar plantilla filtrada
df = pd.read_csv("mi_plantilla_filtrada.csv")

# Convertir % a número
df["Probabilidad_num"] = df["Probabilidad"].str.replace("%", "").astype(float)

# Función para elegir mejores jugadores
def seleccionar_mejor_xi(df):
    # Separar por posición
    porteros = df[df["Posicion"].str.upper() == "POR"].sort_values("Probabilidad_num", ascending=False)
    defensas = df[df["Posicion"].str.upper() == "DEF"].sort_values("Probabilidad_num", ascending=False)
    centros = df[df["Posicion"].str.upper().isin(["CEN", "MED"])].sort_values("Probabilidad_num", ascending=False)
    delanteros = df[df["Posicion"].str.upper() == "DEL"].sort_values("Probabilidad_num", ascending=False)

    # Elegir los mejores según mínimos
    eleccion = []
    eleccion.extend(porteros.head(NUM_POR).to_dict("records"))
    eleccion.extend(defensas.head(MIN_DEF).to_dict("records"))
    eleccion.extend(centros.head(MIN_CEN).to_dict("records"))
    eleccion.extend(delanteros.head(MIN_DEL).to_dict("records"))

    # Calcular cuántos faltan para llegar a 11
    faltan = NUM_JUGADORES - len(eleccion)

    # Unir todos los que quedan y elegir los mejores para completar
    restantes = pd.concat([
        defensas.iloc[MIN_DEF:],
        centros.iloc[MIN_CEN:],
        delanteros.iloc[MIN_DEL:]
    ]).sort_values("Probabilidad_num", ascending=False)

    eleccion.extend(restantes.head(faltan).to_dict("records"))

    orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "MED": 2, "DEL": 3}
    eleccion = sorted(eleccion, key=lambda x: orden_pos.get(x["Posicion"].upper(), 99))

    return eleccion

# Ejecutar selección
mejor_xi = seleccionar_mejor_xi(df)

orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "MED": 2, "DEL": 3}
mejor_xi = sorted(mejor_xi, key=lambda x: orden_pos.get(x["Posicion"].upper(), 99))

# Mostrar en consola
print("\n MEJOR XI RECOMENDADO ")
for jugador in mejor_xi:
    print(f"{jugador['Posicion']} - {jugador['Mi_nombre']} ({jugador['Equipo']}) - {jugador['Probabilidad']}")

# Guardar en CSV
pd.DataFrame(mejor_xi).to_csv("mi_mejor_xi.csv", index=False, encoding="utf-8")
print("\n[OK] Mejor XI guardado en mi_mejor_xi.csv")