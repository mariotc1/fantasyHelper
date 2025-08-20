import time, re, difflib, requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
from fpdf import FPDF

# Configuración de la página
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide", initial_sidebar_state="expanded")

# Estilos CSS para la web
st.markdown("""
<style>
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #4F8BF9;
        color: #4F8BF9;
    }
    .stButton>button:hover {
        border: 1px solid #0B5ED7;
        color: #0B5ED7;
    }
    
    .stButton[aria-label="🔍 Calcular mi XI ideal"]>button {
        color: white;
        background-color: #4F8BF9;
        border-radius: 20px;
        border: none;
        font-weight: bold;
    }
    .stButton[aria-label="🔍 Calcular mi XI ideal"]>button:hover {
        background-color: #0B5ED7;
    }
    div[data-testid="metric-container"] {
        background-color: rgba(230, 240, 255, 0.5);
        border-radius: 10px;
        padding: 15px;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        text-align: center;
        padding: 8px;
        z-index: 9999;
        border-top: 1px solid #ccc;
    }
    @media (prefers-color-scheme: dark) {
        .footer {
            background-color: #0e1117;
        }
        div[data-testid="metric-container"] {
            background-color: rgba(38, 39, 48, 0.8);
        }
    }
</style>
""", unsafe_allow_html=True)


# Funciones de utilidad
def limpiar_porcentaje(x):
    if pd.isna(x): return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", str(x))
    if not m: return None
    return float(m.group(1).replace(",", "."))

def normaliza_pos(p):
    if not isinstance(p, str): return None
    p = p.strip().upper()
    if p in ("POR", "GK", "PT"): return "POR"
    if p in ("DEF", "DF", "D"): return "DEF"
    if p in ("CEN", "MED", "MC", "M"): return "CEN"
    if p in ("DEL", "DC", "FW", "ST"): return "DEL"
    return p

def parsear_plantilla_pegada(texto):
    filas = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea: continue
        partes = [p.strip() for p in re.split(r"[,;]", linea)]
        if len(partes) < 2:
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
    if df.empty: return df
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    return df

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
    return df


# Proceso de scraping de datos de LaLiga
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
    "Villarreal": "https://www.futbolfantasy.com/laliga/equipos/villarreal"
    }

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"}

@st.cache_data(ttl=15*60, show_spinner="Cargando datos de jugadores de LaLiga...")
def scrape_laliga():
    all_rows = []
    for equipo, url in EQUIPOS_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.text, "lxml")
            candidates = soup.select(".jugador, .player, .player-card, .lista-jugadores .row, .media")
            for node in candidates:
                nombre, prob = None, None
                for sel in [".nombre", ".name", ".player-name", ".media-body strong", "strong"]:
                    tag = node.select_one(sel)
                    if tag and tag.get_text(strip=True):
                        nombre = tag.get_text(strip=True); break
                if not nombre:
                    txt = node.get_text(" ", strip=True)
                    if txt and len(txt.split()) <= 6: nombre = txt.split(" Prob")[0].strip()
                for sel in [".probabilidad", ".prob", ".badge", ".player-prob", ".label"]:
                    tag = node.select_one(sel)
                    if tag and "%" in tag.get_text():
                        prob = tag.get_text(strip=True); break
                if not prob:
                    m = re.search(r"(\d{1,3}\s?%)", node.get_text(" ", strip=True))
                    if m: prob = m.group(1)
                if nombre and prob:
                    if "JugadorJugadorJugador" in nombre or "Prob.Prob" in prob: continue
                    all_rows.append({"Equipo": equipo, "Nombre": nombre, "Probabilidad": prob})
            time.sleep(0.5)
        except Exception: continue
    df = pd.DataFrame(all_rows).drop_duplicates()
    if df.empty: return df
    df["Probabilidad_num"] = df["Probabilidad"].apply(limpiar_porcentaje)
    df = df.dropna(subset=["Probabilidad_num"])
    return df.reset_index(drop=True)


# Lógica de matching y XI
def buscar_nombre_mas_cercano(nombre, serie_nombres, cutoff=0.6):
    if not isinstance(nombre, str) or serie_nombres.empty: return None
    cand = difflib.get_close_matches(nombre, serie_nombres.tolist(), n=1, cutoff=cutoff)
    return cand[0] if cand else None

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
                "Mi_nombre": nombre_usuario, "Nombre_web": match, "Equipo": dj["Equipo"],
                "Probabilidad": dj["Probabilidad"], "Probabilidad_num": dj["Probabilidad_num"],
                "Posicion": pos, "Precio": precio
            })
        else: no_encontrados.append(nombre_usuario)
    return pd.DataFrame(encontrados), no_encontrados

def seleccionar_mejor_xi(df, min_def=3, max_def=5, min_cen=3, max_cen=5, min_del=1, max_del=3, num_por=1, total=11):
    if df.empty: return []
    df = df.copy()
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.dropna(subset=["Posicion", "Probabilidad_num"])
    por = df[df["Posicion"] == "POR"].sort_values("Probabilidad_num", ascending=False)
    defn = df[df["Posicion"] == "DEF"].sort_values("Probabilidad_num", ascending=False)
    cen = df[df["Posicion"] == "CEN"].sort_values("Probabilidad_num", ascending=False)
    deln = df[df["Posicion"] == "DEL"].sort_values("Probabilidad_num", ascending=False)
    eleccion = []
    eleccion.extend(por.head(num_por).to_dict("records"))
    eleccion.extend(defn.head(min_def).to_dict("records"))
    eleccion.extend(cen.head(min_cen).to_dict("records"))
    eleccion.extend(deln.head(min_del).to_dict("records"))
    faltan = total - len(eleccion)
    restos = pd.concat([
        defn.iloc[min_def:max_def], cen.iloc[min_cen:max_cen], deln.iloc[min_del:max_del]
    ]).sort_values("Probabilidad_num", ascending=False)
    if faltan > 0 and not restos.empty:
        eleccion.extend(restos.head(faltan).to_dict("records"))
    orden_pos = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
    eleccion = sorted(eleccion, key=lambda x: orden_pos.get(x.get("Posicion", ""), 99))
    return eleccion[:total]


# Exportar el XI a PDF
def generar_pdf_xi(df_xi) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", size=18)
    pdf.cell(0, 12, "Fantasy XI - Tu Alineación Ideal", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", size=12)
    for _, row in df_xi.iterrows():
        linea = f"{row['Posicion']} - {row['Mi_nombre']} ({row['Equipo']}) - Prob: {row['Probabilidad']}"
        pdf.multi_cell(0, 10, linea, border=1, align="L")
        pdf.ln(2)
    try:
        media = df_xi["Probabilidad_num"].mean()
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Media de probabilidad del XI: {media:.1f}%", ln=True, align="C")
    except Exception: pass
    return pdf.output(dest='S').encode('latin1')

# Función para mostrar el XI en un campo de fútbol
def generar_html_campo(df_xi) -> str:
    """
    Genera un string HTML completo con el campo de fútbol y los jugadores.
    Esta versión es más robusta al usar un documento HTML autocontenido.
    """
    # Organizar jugadores por posición
    posiciones = {"POR": [], "DEF": [], "CEN": [], "DEL": []}
    for _, jugador in df_xi.iterrows():
        pos = jugador.get("Posicion")
        if pos in posiciones:
            posiciones[pos].append(jugador)

    # Construir el HTML para cada línea de jugadores
    lineas_html = ""
    for pos_key in ["DEL", "CEN", "DEF", "POR"]:
        linea_actual_html = "<div class='line'>"
        for jugador in posiciones[pos_key]:
            prob_num = jugador['Probabilidad_num']
            if prob_num >= 85: bgcolor = "#90EE90"  # Verde claro (casi seguro)
            elif prob_num >= 65: bgcolor = "#FFFFE0"  # Amarillo claro (probable)
            else: bgcolor = "#FFCCCB" # Rojo claro (duda)

            linea_actual_html += f"""
            <div class="player-card" style="background-color: {bgcolor};">
                <div class="player-name">{jugador['Mi_nombre']}</div>
                <div class="player-details">{jugador['Equipo']}</div>
                <div class="player-details"><b>{jugador['Probabilidad']}</b></div>
            </div>
            """
        linea_actual_html += "</div>"
        lineas_html += linea_actual_html

    # Documento HTML completo con CSS incrustado
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .pitch {{
                background-color: #277c34; /* Verde césped más vivo */
                background-image:
                    linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
                background-size: 30px 30px;
                border: 2px solid white;
                height: 700px;
                width: 100%;
                position: relative;
                display: flex;
                flex-direction: column;
                justify-content: space-around;
                padding: 20px 0;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                box-sizing: border-box; /* Asegura que el padding no afecte el tamaño total */
            }}
            .line {{
                display: flex;
                justify-content: space-around;
                align-items: center;
                width: 100%;
            }}
            .player-card {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 8px;
                border-radius: 8px;
                color: #1a1a1a;
                text-align: center;
                width: 120px;
                min-height: 70px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.4);
                border: 1px solid rgba(0,0,0,0.2);
                transition: transform 0.2s ease-in-out;
            }}
            .player-card:hover {{
                transform: scale(1.08); /* Efecto al pasar el ratón */
            }}
            .player-name {{ font-weight: bold; font-size: 14px; margin-bottom: 2px; }}
            .player-details {{ font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="pitch">
            {lineas_html}
        </div>
    </body>
    </html>
    """
    return full_html


# UI de la web
# Título y subtítulo
st.title("Fantasy XI Assistant")
st.caption("Calcula tu alineación ideal con datos de probabilidad en tiempo real")

# Carga de datos al inicio
df_laliga = scrape_laliga()
if df_laliga.empty:
    st.error("No se pudieron cargar los datos de los jugadores de LaLiga. La aplicación no puede continuar.")
    st.stop()
nombres_laliga = sorted(df_laliga["Nombre"].unique())


# Barra lateral de configuración
with st.sidebar:
    st.image("https://play-lh.googleusercontent.com/xx7OVI90d-d6pvQlqmAAeUo4SzvLsrp9uss8XPO1ZwILEeTCpjYFVRuL550bUqlicy0=w240-h480-rw", width=80)
    st.header("Configuración para crear el XI")

    cutoff = st.slider("Sensibilidad de matching de nombres", 0.3, 1.0, 0.6, 0.05,
                       help="Un valor más bajo puede encontrar más coincidencias si los nombres no son exactos, pero puede cometer errores.")

    st.subheader("Táctica (Formación)")
    c1, c2 = st.columns(2)
    min_def = c1.number_input("Mín. DEF", 2, 5, 3)
    max_def = c2.number_input("Máx. DEF", 3, 6, 5)
    min_cen = c1.number_input("Mín. CEN", 2, 5, 3)
    max_cen = c2.number_input("Máx. CEN", 3, 6, 5)
    min_del = c1.number_input("Mín. DEL", 1, 4, 1)
    max_del = c2.number_input("Máx. DEL", 1, 4, 3)

    st.subheader("Otros ajustes")
    c1, c2 = st.columns(2)
    num_por = c1.number_input("Nº POR", 1, 2, 1)
    total = c2.number_input("Total en XI", 11, 11, 11, disabled=True)

    with st.expander("Ver todos los datos de LaLiga"):
        st.caption(f"Datos cargados: {len(df_laliga)} registros.")
        st.dataframe(df_laliga, use_container_width=True)


# Pesta principal con tabs
tab1, tab2 = st.tabs(["1️⃣ Introduce tu Plantilla", "2️⃣ Tu XI Ideal y Banquillo"])

with tab1:
    st.subheader("Añade los jugadores de tu equipo")
    df_plantilla = pd.DataFrame()

    # Múltiples métodos de entrada de la plantilla del usuario
    st.caption("Puedes añadir tus jugadores de tres maneras diferentes. Elige la que prefieras:")
    input_method_tab1, input_method_tab2, input_method_tab3 = st.tabs(["✍️ Uno a uno", "📋 Pegar lista", "📁 Subir archivo"])

    with input_method_tab1:
        st.info("Usa los selectores para añadir tus jugadores. Puedes añadir hasta 25.")
        if "plantilla_bloques" not in st.session_state:
            st.session_state.plantilla_bloques = [{"Nombre": "", "Posicion": ""} for _ in range(15)]

        def add_bloque():
            st.session_state.plantilla_bloques.append({"Nombre": "", "Posicion": ""})

        POSICIONES = ["POR", "DEF", "CEN", "DEL"]
        for idx, bloque in enumerate(st.session_state.plantilla_bloques):
            c1, c2 = st.columns([3, 1])
            nombre = c1.selectbox(f"Nombre jugador {idx+1}", [""] + nombres_laliga,
                                  index=nombres_laliga.index(bloque["Nombre"]) + 1 if bloque["Nombre"] in nombres_laliga else 0,
                                  key=f"nombre_{idx}")
            pos = c2.selectbox(f"Posición {idx+1}", [""] + POSICIONES,
                               index=POSICIONES.index(bloque["Posicion"]) + 1 if bloque["Posicion"] in POSICIONES else 0,
                               key=f"pos_{idx}")
            st.session_state.plantilla_bloques[idx] = {"Nombre": nombre, "Posicion": pos}

        st.button("+ Añadir jugador", on_click=add_bloque, disabled=len(st.session_state.plantilla_bloques) >= 25)
        df_plantilla_manual = pd.DataFrame([b for b in st.session_state.plantilla_bloques if b["Nombre"] and b["Posicion"]])
        if not df_plantilla_manual.empty:
            df_plantilla = df_plantilla_manual

    with input_method_tab2:
        texto_plantilla = st.text_area("Pega tu plantilla aquí (Ej: Courtois,POR)", height=250,
                                        help="Formato: Nombre, Posición, Precio (opcional). Separado por comas o punto y coma.")
        if texto_plantilla:
            df_plantilla_pegada = parsear_plantilla_pegada(texto_plantilla)
            if not df_plantilla_pegada.empty:
                df_plantilla = df_plantilla_pegada

    with input_method_tab3:
        archivo_subido = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])
        if archivo_subido:
            df_plantilla_archivo = df_desde_csv_subido(archivo_subido)
            if "Nombre" in df_plantilla_archivo and "Posicion" in df_plantilla_archivo:
                df_plantilla = df_plantilla_archivo
            else:
                st.warning("El archivo debe contener las columnas 'Nombre' y 'Posicion'.")

    # Mostrar la plantilla cargada
    if not df_plantilla.empty:
        st.success(f"✅ Plantilla cargada con **{len(df_plantilla)}** jugadores.")
        st.dataframe(df_plantilla, use_container_width=True)
    else:
        st.info("Esperando a que introduzcas tu plantilla en una de las pestañas de arriba.")


with tab2:
    if df_plantilla.empty:
        st.warning("⬅️ Primero debes introducir tu plantilla en la pestaña anterior.")
        st.stop()

    if st.button("🔍 Calcular mi XI ideal", type="primary", use_container_width=True):
        with st.spinner("Buscando coincidencias y optimizando tu alineación..."):
            df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_laliga, cutoff)

        if df_encontrados.empty:
            st.error("No se pudo emparejar ningún jugador. Revisa los nombres o prueba a bajar la 'Sensibilidad' en la barra lateral.")
        else:
            # Motor
            mejor_xi_lista = seleccionar_mejor_xi(
                df_encontrados, min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total
            )

            if not mejor_xi_lista:
                st.error("No se pudo construir un XI con las restricciones tácticas indicadas. Intenta flexibilizar los mínimos/máximos en la barra lateral.")
            else:
                df_xi = pd.DataFrame(mejor_xi_lista)
                media_prob = df_xi["Probabilidad_num"].mean()

                st.subheader("✅ Tu XI Ideal Recomendado")
                c1, c2 = st.columns(2)
                c1.metric("Jugadores Encontrados", f"{len(df_encontrados)}/{len(df_plantilla)}")
                c2.metric("Probabilidad Media del XI", f"{media_prob:.1f}%")

                # MODIFICADO: Usamos components.html para una visualización robusta
                html_campo = generar_html_campo(df_xi)
                components.html(html_campo, height=720, scrolling=False)
                st.caption("Los colores indican la probabilidad de titularidad: 🟩 Muy Alta | 🟨 Probable | 🟥 Duda")

                # Banquillo
                st.subheader("🧩 Banquillo Recomendado (ordenado por probabilidad)")
                banca = df_encontrados[~df_encontrados["Mi_nombre"].isin(df_xi["Mi_nombre"])].sort_values("Probabilidad_num", ascending=False)
                if banca.empty:
                    st.caption("No hay jugadores en el banquillo.")
                else:
                    st.dataframe(banca[["Posicion", "Mi_nombre", "Equipo", "Probabilidad"]], use_container_width=True)

                # Exportar a PDF (NUEVO: movido aquí)
                st.subheader("📄 Exportar a PDF tu XI ideal")
                pdf_bytes = generar_pdf_xi(df_xi)
                st.download_button("Descargar XI en PDF", data=pdf_bytes, file_name="mi_fantasy_xi.pdf", mime="application/pdf")

                if no_encontrados:
                    with st.expander("⚠️ Algunos jugadores no fueron encontrados"):
                        st.warning("No se encontraron coincidencias para: " + ", ".join(sorted(set(no_encontrados))))
                        st.info("Consejo: Revisa si el nombre está bien escrito o intenta bajar la 'Sensibilidad de matching' en la barra lateral.")

# Footer fijo
st.markdown(
    """
    <div class="footer">
        <p style='font-size: 14px; color: gray;'>
        Tip: Usa el asistente el día antes de la jornada para obtener las mejores probabilidades
        </p>
    </div>
    """,
    unsafe_allow_html=True
)