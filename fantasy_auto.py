# Fantasy XI Assistant - Versión unificada "para tontos"
# Ejecuta: streamlit run fantasy_auto.py

import time,re, difflib, requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF


# Configuración de página
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide")
st.title("⚽ Fantasy XI Assistant")
st.caption("Calcula tu mejor XI con scraping en tiempo real")


# Utilidades
def limpiar_porcentaje(x):
    if pd.isna(x):
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(x))
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def normaliza_pos(p):
    if not isinstance(p, str):
        return None
    p = p.strip().upper()
    # Mapear variaciones a POR, DEF, CEN, DEL
    if p in ("POR", "GK", "PT"):
        return "POR"
    if p in ("DEF", "DF", "D"):
        return "DEF"
    if p in ("CEN", "MED", "MC", "M"):
        return "CEN"
    if p in ("DEL", "DC", "FW", "ST"):
        return "DEL"
    return p

def parsear_plantilla_pegada(texto):
    """
    Acepta texto pegado con líneas tipo:
      Nombre, Posicion, Precio
    Precio es opcional.
    """
    filas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        # separar por coma o punto y coma
        partes = [p.strip() for p in re.split(r"[;,]", linea)]
        if len(partes) < 2:
            # Intento: "Nombre Posicion" (última palabra posición)
            trozos = linea.split()
            if len(trozos) >= 2:
                pos = trozos[-1]
                nombre = " ".join(trozos[:-1])
                filas.append({"Nombre": nombre, "Posicion": pos, "Precio": None})
            continue
        nombre, pos = partes[0], partes[1]
        precio = partes[2] if len(partes) >= 3 else None
        filas.append({"Nombre": nombre, "Posicion": pos, "Precio": precio})
    df = pd.DataFrame(filas)
    if df.empty:
        return df
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    return df

def df_desde_csv_subido(file):
    try:
        df = pd.read_csv(file)
    except Exception:
        file.seek(0)
        df = pd.read_excel(file)
    # Intentar normalizar columnas frecuentes
    col_map = {c.lower(): c for c in df.columns}
    # Nombres esperados: Nombre, Posicion, Precio
    # Intentar renombrar
    rename = {}
    for target in ["Nombre", "Posicion", "Precio"]:
        # buscar por lower
        match = [col_map[k] for k in col_map if k in (target.lower(), f"mi_{target.lower()}")]
        if match:
            rename[match[0]] = target
    df = df.rename(columns=rename)
    return df


# Scraping
EQUIPOS_URLS = {
    "Alavés": "https://www.futbolfantasy.com/laliga/equipos/alaves",
    "Athletic Club": "https://www.futbolfantasy.com/laliga/equipos/athletic",
    "Atlético de Madrid": "https://www.futbolfantasy.com/laliga/equipos/atletico",
    "Barcelona": "https://www.futbolfantasy.com/laliga/equipos/barcelona",
    "Betis": "https://www.futbolfantasy.com/laliga/equipos/betis",
    "Celta": "https://www.futbolfantasy.com/laliga/equipos/celta",
    "Elche": "https://www.futbolfantasy.com/laliga/equipos/elche",
    "Espanyol": "https://www.futbolfantasy.com/laliga/equipos/espanyol",
    "Getafe": "https://www.futbolfantasy.com/laliga/equipos/getafe",
    "Girona": "https://www.futbolfantasy.com/laliga/equipos/girona",
    "Levante": "https://www.futbolfantasy.com/laliga/equipos/levante",
    "Mallorca": "https://www.futbolfantasy.com/laliga/equipos/mallorca",
    "Osasuna": "https://www.futbolfantasy.com/laliga/equipos/osasuna",
    "Rayo Vallecano": "https://www.futbolfantasy.com/laliga/equipos/rayo-vallecano",
    "Real Madrid": "https://www.futbolfantasy.com/laliga/equipos/real-madrid",
    "Real Oviedo": "https://www.futbolfantasy.com/laliga/equipos/real-oviedo",
    "Real Sociedad": "https://www.futbolfantasy.com/laliga/equipos/real-sociedad",
    "Sevilla": "https://www.futbolfantasy.com/laliga/equipos/sevilla",
    "Valencia": "https://www.futbolfantasy.com/laliga/equipos/valencia",
    "Villarreal": "https://www.futbolfantasy.com/laliga/equipos/villarreal",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36"
}

@st.cache_data(ttl=15*60, show_spinner=False)
def scrape_laliga():
    """
    Devuelve DataFrame con columnas: Equipo, Nombre, Probabilidad, Probabilidad_num
    Cacheado 15 minutos para evitar sobrecarga.
    """
    all_rows = []
    for equipo, url in EQUIPOS_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "lxml")
            # Selectores robustos: buscar tarjetas con posible estructura cambiante
            # Intentamos varios patrones
            candidates = soup.select(".jugador, .player, .player-card, .lista-jugadores .row, .media")
            if not candidates:
                # fallback: buscar por enlaces/nombres probables
                candidates = soup.find_all(["div", "li"], recursive=True)

            for node in candidates:
                # heurística para nombre
                nombre = None
                prob = None

                # búsquedas dirigidas
                for sel in [".nombre", ".name", ".player-name", ".media-body strong", "strong"]:
                    tag = node.select_one(sel)
                    if tag and tag.get_text(strip=True):
                        nombre = tag.get_text(strip=True)
                        break
                # si no, texto directo con mayúsculas/espacios
                if not nombre:
                    txt = node.get_text(" ", strip=True)
                    # Nombre probable: palabras con inicial mayúscula y espacio
                    if txt and len(txt.split()) <= 6:
                        nombre = txt.split(" Prob")[0].strip()

                # probabilidad
                for sel in [".probabilidad", ".prob", ".badge", ".player-prob", ".label"]:
                    tag = node.select_one(sel)
                    if tag and "%" in tag.get_text():
                        prob = tag.get_text(strip=True)
                        break
                if not prob:
                    txt = node.get_text(" ", strip=True)
                    m = re.search(r"(\d{1,3}\s?%)", txt)
                    if m:
                        prob = m.group(1)

                if nombre and prob:
                    # Filtros anti-ruido
                    if "JugadorJugadorJugador" in nombre or "Prob.Prob" in prob:
                        continue
                    all_rows.append({"Equipo": equipo, "Nombre": nombre, "Probabilidad": prob})
            time.sleep(0.6)  # ser educado con la fuente
        except Exception:
            continue

    df = pd.DataFrame(all_rows).drop_duplicates()
    if df.empty:
        return df

    df["Probabilidad_num"] = df["Probabilidad"].apply(limpiar_porcentaje)
    # descartar sin % válido
    df = df.dropna(subset=["Probabilidad_num"])
    return df.reset_index(drop=True)


# Matching de nombres
def buscar_nombre_mas_cercano(nombre, serie_nombres, cutoff=0.6):
    if not isinstance(nombre, str) or serie_nombres.empty:
        return None
    cand = difflib.get_close_matches(nombre, serie_nombres.tolist(), n=1, cutoff=cutoff)
    return cand[0] if cand else None

def emparejar_con_datos(plantilla_df, datos_df):
    """
    plantilla_df: columnas -> Nombre, Posicion, Precio
    datos_df: columnas -> Equipo, Nombre, Probabilidad, Probabilidad_num
    """
    encontrados = []
    no_encontrados = []

    for _, row in plantilla_df.iterrows():
        nombre_usuario = str(row.get("Nombre", "")).strip()
        pos = normaliza_pos(row.get("Posicion"))
        precio = row.get("Precio", None)

        if not nombre_usuario or not pos:
            continue

        match = buscar_nombre_mas_cercano(nombre_usuario, datos_df["Nombre"], cutoff=0.6)
        if match:
            dj = datos_df[datos_df["Nombre"] == match].iloc[0]
            encontrados.append({
                "Mi_nombre": nombre_usuario,
                "Nombre_web": match,
                "Equipo": dj["Equipo"],
                "Probabilidad": dj["Probabilidad"],
                "Probabilidad_num": dj["Probabilidad_num"],
                "Posicion": pos,
                "Precio": precio
            })
        else:
            no_encontrados.append(nombre_usuario)

    return pd.DataFrame(encontrados), no_encontrados


# Motor de decisión (flexible)
def seleccionar_mejor_xi(df,
                         min_def=3, max_def=5,
                         min_cen=3, max_cen=5,
                         min_del=1, max_del=3,
                         num_por=1, total=11):
    """
    df: columnas -> Posicion, Probabilidad_num, Mi_nombre, Equipo, Probabilidad
    Se cumple 1 POR, y el resto optimiza probabilidad respetando límites.
    """
    if df.empty:
        return []

    df = df.copy()
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.dropna(subset=["Posicion", "Probabilidad_num"])

    # Top por posición
    por = df[df["Posicion"] == "POR"].sort_values("Probabilidad_num", ascending=False)
    defn = df[df["Posicion"] == "DEF"].sort_values("Probabilidad_num", ascending=False)
    cen = df[df["Posicion"] == "CEN"].sort_values("Probabilidad_num", ascending=False)
    deln = df[df["Posicion"] == "DEL"].sort_values("Probabilidad_num", ascending=False)

    eleccion = []
    eleccion.extend(por.head(num_por).to_dict("records"))

    # mínimos
    eleccion.extend(defn.head(min_def).to_dict("records"))
    eleccion.extend(cen.head(min_cen).to_dict("records"))
    eleccion.extend(deln.head(min_del).to_dict("records"))

    # completar
    faltan = total - len(eleccion)
    restos = pd.concat([
        defn.iloc[min_def:max_def],
        cen.iloc[min_cen:max_cen],
        deln.iloc[min_del:max_del]
    ]).sort_values("Probabilidad_num", ascending=False)

    if faltan > 0 and not restos.empty:
        eleccion.extend(restos.head(faltan).to_dict("records"))

    # ordenar por posición
    orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
    eleccion = sorted(eleccion, key=lambda x: orden_pos.get(x.get("Posicion", ""), 99))
    return eleccion[:total]


# Exportar a PDF
def generar_pdf_xi(df_xi) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=16)
    pdf.cell(0, 10, "Mejor XI Recomendado", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    for _, row in df_xi.iterrows():
        linea = f"{row['Posicion']} - {row['Mi_nombre']} ({row['Equipo']}) - {row['Probabilidad']}"
        pdf.multi_cell(0, 8, linea)
    # Resumen
    try:
        media = df_xi["Probabilidad_num"].mean()
        pdf.ln(4)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Media de probabilidad: {media:.1f}%", ln=True)
    except Exception:
        pass
    # Exportar correctamente a bytes
    return pdf.output(dest='S').encode('latin1')

# UI
st.subheader("1) Introduce tu plantilla")

# Scrapea automáticamente al iniciar para obtener nombres
with st.spinner("Cargando lista de jugadores de LaLiga (puede tardar 10-20 segundos)..."):
    df_laliga = scrape_laliga()
if df_laliga.empty:
    st.warning("No se pudo obtener la lista de jugadores de LaLiga para autocompletar.")
    nombres_laliga = []
else:
    nombres_laliga = sorted(df_laliga["Nombre"].unique())

POSICIONES = ["POR", "DEF", "CEN", "DEL"]

# Estado para bloques de entrada de plantilla
if "plantilla_bloques" not in st.session_state:
    st.session_state.plantilla_bloques = [
        {"Nombre": "", "Posicion": "", "Precio": None} for _ in range(11)
    ]

def add_bloque():
    st.session_state.plantilla_bloques.append({"Nombre": "", "Posicion": "", "Precio": None})

st.write("Introduce tus jugadores uno a uno (puedes añadir más de 11 si lo necesitas):")
for idx, bloque in enumerate(st.session_state.plantilla_bloques):
    cols = st.columns([3, 1, 1])
    # Nombre
    nombre = cols[0].selectbox(
        f"Nombre jugador {idx+1}",
        [""] + nombres_laliga,
        index=nombres_laliga.index(bloque["Nombre"]) + 1 if bloque["Nombre"] in nombres_laliga else 0,
        key=f"nombre_{idx}",
    )
    # Posición
    pos = cols[1].selectbox(
        f"Posición {idx+1}",
        [""] + POSICIONES,
        index=POSICIONES.index(bloque["Posicion"]) + 1 if bloque["Posicion"] in POSICIONES else 0,
        key=f"pos_{idx}",
    )
    # Precio
    precio = cols[2].number_input(
        f"Precio {idx+1} (opcional)", min_value=0, value=int(bloque["Precio"]) if bloque["Precio"] is not None and str(bloque["Precio"]).isdigit() else 0,
        key=f"precio_{idx}",
        step=1,
    )
    # Actualiza el bloque
    st.session_state.plantilla_bloques[idx]["Nombre"] = nombre
    st.session_state.plantilla_bloques[idx]["Posicion"] = pos
    st.session_state.plantilla_bloques[idx]["Precio"] = precio if precio != 0 else None

st.button(
    "+ Añadir jugador", on_click=add_bloque,
    disabled=len(st.session_state.plantilla_bloques) >= 24)

# Construir DataFrame de plantilla a partir de bloques válidos
df_plantilla = pd.DataFrame([
    b for b in st.session_state.plantilla_bloques
    if b["Nombre"] and b["Posicion"]
])

if not df_plantilla.empty:
    st.success(f"Plantilla cargada con {len(df_plantilla)} jugadores.")
    st.dataframe(df_plantilla, use_container_width=True)
else:
    st.info("Introduce al menos un jugador y su posición.")

st.divider()

st.subheader("2) Datos de probabilidades obtenidos en tiempo real (puedes consultar todos los jugadores de LaLiga)")
# El scraping se hace automáticamente, no hay opción de subir CSV externo
with st.spinner("Scrapeando LaLiga (puede tardar ~10-20s la primera vez)…"):
    df_datos = scrape_laliga()
if df_datos.empty:
    st.warning("No se han podido obtener datos por scraping.")
else:
    st.caption(f"Datos cargados: {len(df_datos)} registros.")
    with st.expander("Ver muestra de datos obtenidos"):
        st.dataframe(df_datos.head(30), use_container_width=True)

st.divider()

st.subheader("3) Cálculo del XI ideal")
cols = st.columns(6)
min_def = cols[0].number_input("Mín. DEF", 0, 5, 3)
max_def = cols[1].number_input("Máx. DEF", 0, 5, 5)
min_cen = cols[2].number_input("Mín. CEN", 0, 5, 3)
max_cen = cols[3].number_input("Máx. CEN", 0, 5, 5)
min_del = cols[4].number_input("Mín. DEL", 0, 4, 1)
max_del = cols[5].number_input("Máx. DEL", 0, 4, 3)

colx = st.columns(3)
num_por = colx[0].number_input("Nº POR", 0, 2, 1)
total = colx[1].number_input("Total en XI", 1, 11, 11)
cutoff = colx[2].slider("Sensibilidad de matching de nombre", 0.0, 1.0, 0.6, 0.05)

btn = st.button("🔍 Calcular mi XI ideal", type="primary", disabled=df_plantilla.empty or df_datos.empty)

if btn:
    # Emparejar jugadores de tu plantilla con los del scraping
    with st.spinner("Emparejando jugadores y calculando XI…"):
        df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_datos)
        # Ajustar cutoff si el usuario lo cambia
        if cutoff != 0.6:
            df_encontrados = pd.DataFrame()
            no_encontrados = []
            for _, row in df_plantilla.iterrows():
                nombre_usuario = str(row.get("Nombre", "")).strip()
                pos = normaliza_pos(row.get("Posicion"))
                precio = row.get("Precio", None)
                if not nombre_usuario or not pos:
                    continue
                match = buscar_nombre_mas_cercano(nombre_usuario, df_datos["Nombre"], cutoff=cutoff)
                if match:
                    dj = df_datos[df_datos["Nombre"] == match].iloc[0]
                    df_encontrados = pd.concat([df_encontrados, pd.DataFrame([{
                        "Mi_nombre": nombre_usuario,
                        "Nombre_web": match,
                        "Equipo": dj["Equipo"],
                        "Probabilidad": dj["Probabilidad"],
                        "Probabilidad_num": dj["Probabilidad_num"],
                        "Posicion": pos,
                        "Precio": precio
                    }])], ignore_index=True)
                else:
                    no_encontrados.append(nombre_usuario)

        if df_encontrados.empty:
            st.error("No se pudo emparejar ningún jugador. Revisa nombres/posiciones o baja la sensibilidad.")
        else:
            # Motor
            mejor_xi = seleccionar_mejor_xi(
                df_encontrados,
                min_def=min_def, max_def=max_def,
                min_cen=min_cen, max_cen=max_cen,
                min_del=min_del, max_del=max_del,
                num_por=num_por, total=total
            )
            if not mejor_xi:
                st.error("No se pudo construir un XI con las restricciones indicadas.")
            else:
                df_xi = pd.DataFrame(mejor_xi)
                # Mostrar XI
                st.subheader("✅ Mejor XI recomendado")
                def color_prob(val):
                    try:
                        if isinstance(val, str) and "%" in val:
                            p = float(val.replace("%", "").replace(",", "."))
                        else:
                            p = float(val)
                    except Exception:
                        return ""
                    if p >= 80:
                        # Verde más oscuro, texto negro
                        return "background-color: #4CAF50; color: #000000"
                    if p < 50:
                        return "background-color: #ffd6d6"
                    return ""
                vista = df_xi[["Posicion", "Mi_nombre", "Equipo", "Probabilidad", "Probabilidad_num"]].copy()
                vista = vista.rename(columns={"Mi_nombre": "Nombre", "Probabilidad_num": "Prob_num"})
                st.dataframe(vista.style.applymap(color_prob, subset=["Probabilidad", "Prob_num"]), use_container_width=True)

                # Media de probabilidad
                try:
                    media = df_xi["Probabilidad_num"].mean()
                    st.metric("Media de probabilidad del XI", f"{media:.1f}%")
                except Exception:
                    pass

                # Banquillo
                st.subheader("🧩 Banquillo recomendado")
                banca = df_encontrados[~df_encontrados["Mi_nombre"].isin(df_xi["Mi_nombre"])]
                if banca.empty:
                    st.caption("Sin banquillo disponible con los datos cargados.")
                else:
                    st.dataframe(
                        banca[["Posicion", "Mi_nombre", "Equipo", "Probabilidad", "Probabilidad_num"]]
                        .sort_values("Probabilidad_num", ascending=False),
                        use_container_width=True
                    )

                # Descargar PDF
                st.subheader("📄 Exportar")
                pdf_bytes = generar_pdf_xi(df_xi)
                st.download_button(
                    "Descargar XI en PDF",
                    data=pdf_bytes,
                    file_name="mejor_xi.pdf",
                    mime="application/pdf"
                )

                # Avisos de no encontrados
                if no_encontrados:
                    st.warning("No se encontraron coincidencias para: " + ", ".join(sorted(set(no_encontrados))))

# Footer mini
st.markdown("---")
st.caption("Tip: puedes actualizar el motor de decisión en este mismo archivo y el despliegue en Streamlit Cloud se actualizará solo cuando hagas push a GitHub.")