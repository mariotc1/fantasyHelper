# LIBRERÍAS EXTERNAS (difflib para comparación de cadenas, pandas para manejo de datos)
import difflib
import pandas as pd

# LIBRERÍAS INTERNAS
from .data_utils import normaliza_pos

# FUNCIONES PRINCIPALES

# Busca el nombre más similar en una Serie de pandas usando difflib
def buscar_nombre_mas_cercano(nombre, serie_nombres, cutoff=0.6):
    if not isinstance(nombre, str) or serie_nombres.empty: return None
    cand = difflib.get_close_matches(nombre, serie_nombres.tolist(), n=1, cutoff=cutoff)
    return cand[0] if cand else None

# Empareja el DataFrame de la plantilla del usuario con los datos de LaLiga
def emparejar_con_datos(plantilla_df, datos_df, cutoff=0.6):
    encontrados = []
    no_encontrados = []
    
    for _, row in plantilla_df.iterrows():
        nombre_usuario = str(row.get("Nombre", "")).strip()
        pos = normaliza_pos(row.get("Posicion"))
        precio = row.get("Precio", None)
        
        if not nombre_usuario or not pos: continue
        
        match = buscar_nombre_mas_cercano(nombre_usuario, datos_df["Nombre"], cutoff=cutoff)
        
        if match:
            dj = datos_df[datos_df["Nombre"] == match].iloc[0]
            encontrados.append({
                "Mi_nombre": nombre_usuario,
                "Nombre_web": match,
                "Equipo": dj["Equipo"],
                "Probabilidad": dj["Probabilidad"],
                "Probabilidad_num": dj["Probabilidad_num"],
                "Posicion": pos,
                "Precio": precio,
                "Imagen_URL": dj.get("Imagen_URL"),
                "Perfil_URL": dj.get("Perfil_URL")
            })
        else:
            no_encontrados.append(nombre_usuario)
            
    return pd.DataFrame(encontrados), no_encontrados

# Selecciona el mejor XI posible basándose en la probabilidad y las restricciones tácticas
def seleccionar_mejor_xi(df, min_def=3, max_def=5, min_cen=3, max_cen=5, min_del=1, max_del=3, num_por=1, total=11):
    if df.empty: return [], "El dataframe de jugadores está vacío."
    
    df = df.copy()
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.dropna(subset=["Posicion", "Probabilidad_num"])
    
    # Separar jugadores por posición
    por = df[df["Posicion"] == "POR"].sort_values("Probabilidad_num", ascending=False)
    defn = df[df["Posicion"] == "DEF"].sort_values("Probabilidad_num", ascending=False)
    cen = df[df["Posicion"] == "CEN"].sort_values("Probabilidad_num", ascending=False)
    deln = df[df["Posicion"] == "DEL"].sort_values("Probabilidad_num", ascending=False)
    
    # Validaciones previas para una mejor experiencia de usuario
    if len(por) < num_por: return [], f"No tienes suficientes porteros (necesitas {num_por} y tienes {len(por)})."
    if len(defn) < min_def: return [], f"No tienes suficientes defensas (necesitas {min_def} y tienes {len(defn)})."
    if len(cen) < min_cen: return [], f"No tienes suficientes centrocampistas (necesitas {min_cen} y tienes {len(cen)})."
    if len(deln) < min_del: return [], f"No tienes suficientes delanteros (necesitas {min_del} y tienes {len(deln)})."

    # Seleccionar jugadores mínimos obligatorios
    eleccion = []
    eleccion.extend(por.head(num_por).to_dict("records"))
    eleccion.extend(defn.head(min_def).to_dict("records"))
    eleccion.extend(cen.head(min_cen).to_dict("records"))
    eleccion.extend(deln.head(min_del).to_dict("records"))
    
    # Seleccionar el resto de los mejores jugadores hasta completar 11
    faltan = total - len(eleccion)
    restos = pd.concat([
        defn.iloc[min_def:max_def],
        cen.iloc[min_cen:max_cen],
        deln.iloc[min_del:max_del]
    ]).sort_values("Probabilidad_num", ascending=False)
    
    if faltan > 0 and not restos.empty:
        eleccion.extend(restos.head(faltan).to_dict("records"))
        
    # Ordenar el XI final por posición para visualización
    orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
    eleccion = sorted(eleccion, key=lambda x: orden_pos.get(x.get("Posicion", ""), 99))
    
    final_xi = eleccion[:total]
    if len(final_xi) < total:
        return [], f"No se pudo completar un XI de {total} jugadores con tu plantilla y táctica. Solo se pudieron seleccionar {len(final_xi)}."

    return final_xi, None