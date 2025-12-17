import re
import pandas as pd

def limpiar_porcentaje(x):
    """Convierte un texto de porcentaje (ej: '95%') a un número flotante."""
    if pd.isna(x): return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(x))
    if not m: return None
    return float(m.group(1).replace(",", "."))

def normaliza_pos(p):
    """Normaliza la abreviatura de una posición de jugador a un valor estándar."""
    if not isinstance(p, str): return None
    p = p.strip().upper()
    if p in ("POR", "GK", "PT"): return "POR"
    if p in ("DEF", "DF", "D"): return "DEF"
    if p in ("CEN", "MED", "MC", "M"): return "CEN"
    if p in ("DEL", "DC", "FW", "ST"): return "DEL"
    return p

def parsear_plantilla_pegada(texto):
    """Parsea un texto multilínea con datos de jugadores y lo convierte en un DataFrame."""
    filas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea: continue

        # Expresión regular más flexible
        match = re.match(r"^(.*?)(?:[;,]|\s+)\s*(POR|DEF|CEN|DEL|GK|DF|MC|DC|FW)\s*(?:[;,]|\s+)?(.*)$", linea, re.IGNORECASE)

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
                if normaliza_pos(pos) in ["POR", "DEF", "CEN", "DEL"]:
                     filas.append({"Nombre": nombre, "Posicion": pos, "Precio": None})
    
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas)
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.drop_duplicates(subset=["Nombre"])
    return df

def df_desde_csv_subido(file):
    """Lee un archivo CSV o Excel subido y lo convierte en un DataFrame, renombrando columnas comunes."""
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
