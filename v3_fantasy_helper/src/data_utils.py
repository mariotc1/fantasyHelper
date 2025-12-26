# IMPORTACIONES DE LIBRERÍAS EXTERNAS (re para expresiones regulares, pandas para manejo de datos)
import re
import pandas as pd

# FUNCIONES AUXILIARES

# Convierte un texto de porcentaje (ej: '95%') a un número flotante
def limpiar_porcentaje(x):
    if pd.isna(x): return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(x))
    if not m: return None
    return float(m.group(1).replace(",", "."))

# Normaliza una posición de jugador a un valor estándar
def normaliza_pos(p):
    if not isinstance(p, str): return None
    p = p.strip().upper()
    if p in ("POR", "GK", "PT"): return "POR"
    if p in ("DEF", "DF", "D"): return "DEF"
    if p in ("CEN", "MED", "MC", "M", "MID"): return "CEN"
    if p in ("DEL", "DC", "FW", "ST", "F"): return "DEL"
    return None # Devuelve None si no es una posición reconocida

# Parsea un texto multilínea con datos de jugadores y lo convierte en un DataFrame
def parsear_plantilla_pegada(texto):
    filas = []
    # Lista extendida de posibles posiciones para la expresión regular
    pos_regex = "POR|GK|PT|DEF|DF|D|CEN|MED|MC|M|MID|DEL|DC|FW|ST|F"

    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea: continue

        # Expresión regular para capturar nombre, posición y precio
        match = re.match(rf"^(.*?)(?:[;,]|\s+)\s*({pos_regex})\s*(?:[;,]|\s+)?(.*)$", linea, re.IGNORECASE)

        if match:
            nombre = match.group(1).strip()
            pos = match.group(2).strip()
            precio_str = match.group(3).strip() if match.group(3) else None
            filas.append({"Nombre": nombre, "Posicion": pos, "Precio": precio_str})
        else:
            trozos = linea.split()
            if len(trozos) >= 2:
                pos = trozos[-1]
                nombre = " ".join(trozos[:-1])
                if normaliza_pos(pos): # Usamos la función para verificar si es una posición válida
                     filas.append({"Nombre": nombre, "Posicion": pos, "Precio": None})
    
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas)
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.drop_duplicates(subset=["Nombre"])
    return df

# Lee un archivo CSV o Excel subido y lo convierte en un DataFrame, renombrando columnas comunes
def df_desde_csv_subido(file):
    try:
        df = pd.read_csv(file)
    except Exception:
        file.seek(0)
        df = pd.read_excel(file)
    
    col_map = {c.lower(): c for c in df.columns}
    rename = {}
    
    for target in ["Nombre", "Posicion", "Precio"]:
        match = [col_map[k] for k in col_map if k in (target.lower(), f"mi_{target.lower()}")]
        if match: rename[match[0]] = target
    df = df.rename(columns=rename)
    
    if "Nombre" in df.columns:
        df = df.drop_duplicates(subset=["Nombre"])
    return df