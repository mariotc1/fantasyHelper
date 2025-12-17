import time, re, difflib, requests, json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from bs4 import BeautifulSoup
from fpdf import FPDF
from streamlit_local_storage import LocalStorage

# Configuración de la página
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-0VYQV3HLQ0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-0VYQV3HLQ0');
</script>
""", unsafe_allow_html=True)
# incicializo el objeto de LocalStorage para poder guardar y leer datos del navegador
localS = LocalStorage()

# Estilos CSS para mejorar la UI
st.markdown("""
<style>
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #4F8BF9;
        color: #4F8BF9;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border: 1px solid #0B5ED7;
        color: #0B5ED7;
        transform: scale(1.02);
    }

    .stButton[aria-label="Calcular mi XI ideal"]>button {
        color: white;
        background-color: #4F8BF9;
        border-radius: 20px;
        border: none;
        font-weight: bold;
        font-size: 1.1em;
        transition: all 0.3s ease-in-out; /* Transición suave */
    }
    .stButton[aria-label="Calcular mi XI ideal"]>button:hover {
        background-color: #0B5ED7; /* Fondo azul más oscuro */
        color: white; /* Texto se mantiene blanco */
        transform: scale(1.02); /* Efecto de crecimiento sutil */
        box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2); /* Sombra para efecto 'pop' */
    }

    div[data-testid="metric-container"] {
        background-color: rgba(230, 240, 255, 0.5);
        border-radius: 10px;
        padding: 15px;
    }

    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #ffffff; text-align: center; padding: 8px;
        z-index: 9999; border-top: 1px solid #e0e0e0;
    }

    @media (prefers-color-scheme: dark) {
        .footer {
            background-color: #0e1117;
            border-top: 1px solid #262730;
        }
        div[data-testid="metric-container"] {
            background-color: rgba(38, 39, 48, 0.8);
        }
    }
</style>
""", unsafe_allow_html=True)


# FUNCIONES DE UTILIDAD
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

        # Expresión regular más flexible y robusta: Grupo 1: Nombre, Grupo 2: Posición y opcionalmente Grupo 3: Precio
        # Permite comas, puntos y comas, o solo espacios como separadores
        match = re.match(r"^(.*?)(?:[;,]|\s+)\s*(POR|DEF|CEN|DEL|GK|DF|MC|DC|FW)\s*(?:[;,]|\s+)?(.*)$", linea, re.IGNORECASE)

        if match:
            nombre = match.group(1).strip()
            pos = match.group(2).strip()
            precio_str = match.group(3).strip() if match.group(3) else None
            filas.append({"Nombre": nombre, "Posicion": pos, "Precio": precio_str})
        else:
            # Si la regex falla, intentamos un método más simple por si acaso
            trozos = linea.split()
            if len(trozos) >= 2:
                pos = trozos[-1]
                nombre = " ".join(trozos[:-1])
                # Validamos si la supuesta posición es válida
                if normaliza_pos(pos) in ["POR", "DEF", "CEN", "DEL"]:
                     filas.append({"Nombre": nombre, "Posicion": pos, "Precio": None})
    
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas)
    df["Posicion"] = df["Posicion"].apply(normaliza_pos)
    df = df.drop_duplicates(subset=["Nombre"])
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
    
    if "Nombre" in df.columns:
        df = df.drop_duplicates(subset=["Nombre"])
    return df


# PROCESO DE SCRAPING DE DATOS DE LA LIGA
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

@st.cache_data(ttl=15*60, show_spinner="Cargando datos de jugadores de LaLiga (puede tardar unos segundos)...")
def scrape_laliga():
    all_rows = []
    for equipo, url in EQUIPOS_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            candidates = soup.select(".jugador, .player, .player-card, .lista-jugadores .row, .media")
            
            for node in candidates:
                nombre, prob = None, None
                for sel in [".nombre", ".name", ".player-name", ".media-body strong", "strong"]:
                    tag = node.select_one(sel)
                    if tag and tag.get_text(strip=True): nombre = tag.get_text(strip=True); break
                if not nombre:
                    txt = node.get_text(" ", strip=True)
                    if txt and len(txt.split()) <= 6: nombre = txt.split(" Prob")[0].strip()
                for sel in [".probabilidad", ".prob", ".badge", ".player-prob", ".label"]:
                    tag = node.select_one(sel)
                    if tag and "%" in tag.get_text(): prob = tag.get_text(strip=True); break
                if not prob:
                    m = re.search(r"(\d{1,3}\s?%)", node.get_text(" ", strip=True))
                    if m: prob = m.group(1)
                if nombre and prob:
                    if "JugadorJugadorJugador" in nombre or "Prob.Prob" in prob: continue
                    all_rows.append({"Equipo": equipo, "Nombre": nombre, "Probabilidad": prob})
            time.sleep(0.2)
        
        except requests.exceptions.RequestException as e:
            st.toast(f"Error al cargar datos de {equipo}: {e}", icon="⚠️")
            continue
    
    df = pd.DataFrame(all_rows).drop_duplicates()
    if df.empty: return df
    df["Probabilidad_num"] = df["Probabilidad"].apply(limpiar_porcentaje)
    df = df.dropna(subset=["Probabilidad_num"])
    
    df = df.drop_duplicates(subset=['Nombre', 'Equipo']).sort_values("Probabilidad_num", ascending=False)
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


# FUNCIONES DE GENERACIÓN DE PDF Y HTML DE CAMPO
def generar_pdf_xi(df_xi) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", "B", size=18)
    pdf.cell(0, 12, "Fantasy XI - Tu Alineacion Ideal", ln=True, align="C")
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


def generar_html_campo(df_xi) -> str:
    # 1. Organizar datos
    posiciones = {"POR": [], "DEF": [], "CEN": [], "DEL": []}
    for _, jugador in df_xi.iterrows():
        pos = jugador.get("Posicion")
        if pos in posiciones:
            posiciones[pos].append(jugador)
    
    # Formación (ej: 3-5-2)
    formacion_str = f"{len(posiciones['DEF'])} - {len(posiciones['CEN'])} - {len(posiciones['DEL'])}"

    # 2. Construir HTML de las líneas
    lineas_html = ""
    # Orden visual: DEL arriba -> POR abajo
    for pos_key in ["DEL", "CEN", "DEF", "POR"]:
        jugadores = posiciones[pos_key]
        num_jugadores = len(jugadores)
        
        # Ajuste inteligente: si son muchos (5), reducimos un poco el margen lateral
        # si es 1 (portero), centrado total.
        justify = "space-around" if num_jugadores > 1 else "center"
        
        linea_html = f'<div class="line" style="justify-content: {justify};">'
        
        for jugador in jugadores:
            prob = jugador['Probabilidad_num']
            # Lógica de colores semáforo (Estilo App moderna: colores pastel + texto fuerte)
            if prob >= 80:
                color_bg, color_txt, border_col = "#dcfce7", "#166534", "#22c55e" # Verde
            elif prob >= 60:
                color_bg, color_txt, border_col = "#fef9c3", "#854d0e", "#eab308" # Amarillo
            else:
                color_bg, color_txt, border_col = "#fee2e2", "#991b1b", "#ef4444" # Rojo

            # Acortar nombres muy largos para que no rompan la tarjeta
            nombre_display = jugador['Mi_nombre']
            if len(nombre_display) > 12:
                parts = nombre_display.split()
                # Si tiene apellido, usamos la inicial del nombre + apellido, o solo el apellido si es muy largo
                if len(parts) > 1:
                    nombre_display = f"{parts[0][0]}. {parts[-1]}"
                else:
                    nombre_display = nombre_display[:10] + "."

            card_html = f"""
            <div class="card-container">
                <div class="player-card">
                    <div class="card-header">
                        <span class="pos-pill">{jugador['Posicion']}</span>
                        <span class="prob-pill" style="background:{color_bg}; color:{color_txt};">{int(prob)}%</span>
                    </div>
                    <div class="card-body">
                        <div class="p-name">{nombre_display}</div>
                        <div class="p-team">{jugador['Equipo']}</div>
                    </div>
                    <div class="health-bar" style="background:{border_col}; width:{prob}%;"></div>
                </div>
            </div>
            """
            linea_html += card_html
        
        linea_html += "</div>"
        lineas_html += linea_html

    # 3. HTML Completo con CSS "Mobile First"
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            
            :root {{
                --grass-dark: #2f7a38;
                --grass-light: #3a8a44;
                --line-white: rgba(255,255,255,0.7);
            }}

            * {{ box-sizing: border-box; }}
            
            body {{ 
                margin: 0; padding: 0; 
                font-family: 'Inter', sans-serif; 
                background: transparent;
                display: flex; justify-content: center;
                /* Evitar scroll horizontal en iframes pequeños */
                overflow-x: hidden; 
            }}

            /* Contenedor principal: Simula la pantalla del móvil */
            .pitch-wrapper {{
                width: 100%;
                max-width: 500px; /* Ancho máximo de móvil estándar */
                /* IMPORTANTE: Aspect Ratio para mantener proporción de campo SIEMPRE */
                aspect-ratio: 2/3.1; 
                position: relative;
                margin: 0 auto;
            }}

            /* El Campo */
            .pitch {{
                width: 100%; height: 100%;
                background-color: var(--grass-dark);
                /* Patrón de césped moderno y sutil */
                background-image: 
                    repeating-linear-gradient(0deg, transparent, transparent 10%, rgba(0,0,0,0.05) 10%, rgba(0,0,0,0.05) 20%);
                border: 2px solid white;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
                display: flex; flex-direction: column;
                position: relative; overflow: hidden;
            }}

            /* Líneas del campo (Dibujo CSS puro) */
            .line-half {{ position: absolute; top: 50%; width: 100%; height: 2px; background: var(--line-white); }}
            .circle-center {{ 
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                width: 20%; aspect-ratio: 1/1; border: 2px solid var(--line-white); border-radius: 50%; 
            }}
            .area {{
                position: absolute; left: 50%; transform: translateX(-50%);
                width: 40%; height: 6%; border: 2px solid var(--line-white);
            }}
            .area.top {{ top: 0; border-top: 0; }}
            .area.bot {{ bottom: 0; border-bottom: 0; }}

            /* Etiqueta de Formación */
            .formation-badge {{
                position: absolute; top: 12px; right: 12px;
                background: rgba(0,0,0,0.6); color: white;
                padding: 4px 10px; border-radius: 20px;
                font-size: 12px; font-weight: 800; z-index: 5;
                backdrop-filter: blur(4px);
            }}

            /* Layout de Jugadores */
            .line {{
                flex: 1; /* CADA LÍNEA OCUPA EL MISMO ESPACIO VERTICAL */
                display: flex; align-items: center;
                width: 100%; padding: 0 4px; z-index: 2;
            }}

            .card-container {{
                /* Ancho dinámico según número de jugadores */
                width: 19%; 
                display: flex; justify-content: center;
            }}

            /* Tarjeta del Jugador - ESTILO APP */
            .player-card {{
                background: white;
                width: 100%; max-width: 85px; /* Tope para que no sean gigantes */
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                overflow: hidden;
                display: flex; flex-direction: column;
                transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }}
            
            /* Efecto click/touch */
            .player-card:active {{ transform: scale(0.95); }}

            .card-header {{
                display: flex; justify-content: space-between; align-items: center;
                padding: 3px 4px;
                font-size: 9px; font-weight: 700; color: #555;
            }}

            .card-body {{
                text-align: center; padding: 2px 2px 6px 2px;
                flex-grow: 1; display: flex; flex-direction: column; justify-content: center;
            }}

            .p-name {{
                font-size: clamp(10px, 2.5vw, 12px); /* FUENTE DINÁMICA */
                font-weight: 800; color: #1e293b;
                line-height: 1.1; margin-bottom: 2px;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }}

            .p-team {{
                font-size: 8px; color: #64748b; font-weight: 500;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }}

            .health-bar {{ height: 3px; align-self: flex-start; }}

            /* AJUSTES PARA PC (Pantallas grandes) */
            @media (min-width: 768px) {{
                .pitch-wrapper {{
                    max-width: 700px; /* Campo más ancho en PC */
                    aspect-ratio: unset; /* Quitamos ratio forzado */
                    height: 680px; /* Altura fija cómoda para ver en monitor */
                }}
                .player-card {{ max-width: 110px; }}
                .p-name {{ font-size: 13px; }}
                .p-team {{ font-size: 10px; }}
                .card-header {{ font-size: 10px; padding: 5px; }}
            }}
        </style>
    </head>
    <body>
        <div class="pitch-wrapper">
            <div class="pitch">
                <div class="formation-badge">{formacion_str}</div>
                <!-- Dibujo del campo -->
                <div class="area top"></div>
                <div class="area bot"></div>
                <div class="line-half"></div>
                <div class="circle-center"></div>
                
                <!-- Jugadores -->
                {lineas_html}
            </div>
        </div>
    </body>
    </html>
    """
    return full_html


# UI DE LA WEB
st.title("Fantasy XI Assistant")
st.caption("Calcula tu alineación ideal con datos de probabilidad en tiempo real")

df_laliga = scrape_laliga()
if df_laliga.empty:
    st.error("🔴 No se pudieron cargar los datos de los jugadores de LaLiga. La aplicación no puede continuar.")
    st.stop()
nombres_laliga = sorted(df_laliga["Nombre"].unique())

with st.sidebar:
    st.image("https://play-lh.googleusercontent.com/xx7OVI90d-d6pvQlqmAAeUo4SzvLsrp9uss8XPO1ZwILEeTCpjYFVRuL550bUqlicy0=w240-h480-rw", width=80)
    st.header("Configuración del XI")

    st.subheader("Sensibilidad")
    cutoff = st.slider("Matching de nombres", 0.3, 1.0, 0.6, 0.05,
                       help="Un valor más bajo puede encontrar más coincidencias si los nombres no son exactos, pero puede cometer errores.")

    st.subheader("Táctica (Formación)")
    c1, c2 = st.columns(2)
    min_def = c1.number_input("Mín. DEF", 2, 5, 3)
    max_def = c2.number_input("Máx. DEF", 3, 6, 5)
    min_cen = c1.number_input("Mín. CEN", 2, 5, 3)
    max_cen = c2.number_input("Máx. CEN", 3, 6, 5)
    min_del = c1.number_input("Mín. DEL", 1, 4, 1)
    max_del = c2.number_input("Máx. DEL", 1, 4, 3)
    
    if min_def > max_def: st.warning("Mín. DEF no puede ser mayor que Máx. DEF.")
    if min_cen > max_cen: st.warning("Mín. CEN no puede ser mayor que Máx. CEN.")
    if min_del > max_del: st.warning("Mín. DEL no puede ser mayor que Máx. DEL.")
    if (min_def + min_cen + min_del + 1) > 11:
        st.error("La suma de mínimos es > 11. Formación imposible.")
    
    st.subheader("Ajustes Fijos")
    c1, c2 = st.columns(2)
    
    c1.number_input("Nº POR", 1, 1, 1, disabled=True) 
    c2.number_input("Total en XI", 11, 11, 11, disabled=True)

    num_por = 1
    total = 11

    with st.expander("Ver todos los datos de LaLiga"):
        st.caption(f"Datos cargados: {len(df_laliga)} registros únicos.")
        st.dataframe(df_laliga, use_container_width=True)


tab1, tab2 = st.tabs(["1️⃣ Introduce tu Plantilla", "2️⃣ Tu XI Ideal y Banquillo"])

with tab1:
    st.header("Añade los jugadores de tu equipo")
    df_plantilla = pd.DataFrame()

    st.info("Puedes añadir tus jugadores de 3 maneras. Elige la que prefieras:", icon="👇")
    input_method_tab1, input_method_tab2, input_method_tab3 = st.tabs(["✍️ Uno a uno", "📋 Pegar lista", "📁 Subir archivo"])

    with input_method_tab1:
        st.caption("Añade o elimina jugadores. Tus cambios se guardarán en el navegador para la próxima visita")

        # defino la estructura de la página
        if "plantilla_bloques" not in st.session_state:
            plantilla_guardada_str = localS.getItem("fantasy_plantilla")
            if plantilla_guardada_str:
                st.session_state.plantilla_bloques = json.loads(plantilla_guardada_str)
                st.toast("¡Hemos cargado tu plantilla guardada!", icon="👍")
            else:
                st.session_state.plantilla_bloques = [{"id": i, "Nombre": "", "Posicion": ""} for i in range(11)]

        # añado los widgets y guardo su estado para ver luego si hay cambios
        POSICIONES_CON_PLACEHOLDER = ["Elige una posición...", "POR", "DEF", "CEN", "DEL"]
        NOMBRES_CON_PLACEHOLDER = ["Selecciona un jugador..."] + nombres_laliga
        
        for i, bloque in enumerate(st.session_state.plantilla_bloques):
            with st.container(border=True):
                c1, c2 = st.columns([0.85, 0.15])
                with c1:
                    # añado el widget y su valor lo almaceno en session_state en su key
                    idx_nombre = NOMBRES_CON_PLACEHOLDER.index(bloque["Nombre"]) if bloque["Nombre"] in NOMBRES_CON_PLACEHOLDER else 0
                    st.selectbox(f"Nombre Jugador {i+1}", NOMBRES_CON_PLACEHOLDER, 
                                          index=idx_nombre, key=f"nombre_{bloque['id']}", 
                                          label_visibility="collapsed")
                    
                    idx_pos = POSICIONES_CON_PLACEHOLDER.index(bloque["Posicion"]) if bloque["Posicion"] in POSICIONES_CON_PLACEHOLDER else 0
                    st.selectbox(f"Posición Jugador {i+1}", POSICIONES_CON_PLACEHOLDER, 
                                       index=idx_pos, key=f"pos_{bloque['id']}", 
                                       label_visibility="collapsed")
                with c2:
                    st.markdown("<br/>", unsafe_allow_html=True) 
                    if st.button("❌", key=f"del_{bloque['id']}", help="Quitar este jugador de la lista"):
                        st.session_state.plantilla_bloques.pop(i)
                        st.rerun()

        if st.button("➕ Añadir jugador"):
            new_id = int(time.time() * 1000)
            st.session_state.plantilla_bloques.append({"id": new_id, "Nombre": "", "Posicion": ""})
            st.rerun()

        st.divider()

        plantilla_actual = []
        for bloque in st.session_state.plantilla_bloques:
            nombre = st.session_state[f"nombre_{bloque['id']}"]
            posicion = st.session_state[f"pos_{bloque['id']}"]
            plantilla_actual.append({
                "id": bloque['id'],
                "Nombre": nombre if nombre != "Selecciona un jugador..." else "",
                "Posicion": posicion if posicion != "Elige una posición..." else ""
            })

        # comparo con lo que hay guardado en el navegador
        plantilla_guardada_str = localS.getItem("fantasy_plantilla")
        plantilla_guardada = json.loads(plantilla_guardada_str) if plantilla_guardada_str else []
        
        # filtro las listas para una ccompararlas
        plantilla_actual_filtrada = [b for b in plantilla_actual if b.get("Nombre") and b.get("Posicion")]
        hay_cambios_sin_guardar = plantilla_actual_filtrada != plantilla_guardada

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Guardar cambios", type="primary", disabled=not hay_cambios_sin_guardar):
                localS.setItem("fantasy_plantilla", json.dumps(plantilla_actual_filtrada))
                st.success("¡Plantilla guardada con éxito!")
                time.sleep(1) # pausa para que el usuario vea el mensaje
                st.rerun()

        with c2:
            if st.button("🗑️ Borrar plantilla guardada"):
                localS.setItem("fantasy_plantilla", None)
                
                # reseteo el estado de la UI
                st.session_state.plantilla_bloques = [{"id": i, "Nombre": "", "Posicion": ""} for i in range(11)]
                # reseteo la snapshot para que la UI se actualice
                if "plantilla_al_cargar" in st.session_state:
                    st.session_state.plantilla_al_cargar = list(st.session_state.plantilla_bloques)

                st.info("Plantilla guardada eliminada.")
                st.rerun()
        
        if hay_cambios_sin_guardar:
            st.warning("Tienes cambios sin guardar", icon="⚠️")
        else:
             if plantilla_guardada:
                st.success("Plantilla sincronizada", icon="✅")
        
        df_plantilla_manual = pd.DataFrame(plantilla_actual_filtrada)
        if not df_plantilla_manual.empty:
            df_plantilla = df_plantilla_manual.drop(columns=['id']).drop_duplicates(subset=["Nombre"])


    with input_method_tab2:
        texto_plantilla = st.text_area("Pega tu plantilla aquí (Ej: `Courtois, POR`)", height=250,
                                        help="Formato: Nombre, Posición, Precio (opcional). Un jugador por línea.")
        if texto_plantilla:
            df_plantilla = parsear_plantilla_pegada(texto_plantilla)

    with input_method_tab3:
        archivo_subido = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])
        if archivo_subido:
            df_plantilla_archivo = df_desde_csv_subido(archivo_subido)
            if "Nombre" in df_plantilla_archivo and "Posicion" in df_plantilla_archivo:
                df_plantilla = df_plantilla_archivo
            else:
                st.warning("El archivo debe contener las columnas 'Nombre' y 'Posicion'.")

    if not df_plantilla.empty:
        if df_plantilla['Nombre'].duplicated().any():
            st.warning("⚠️ Se han detectado y eliminado jugadores duplicados en tu plantilla", icon="❗")
            df_plantilla = df_plantilla.drop_duplicates(subset=['Nombre'], keep='first')
        
        st.success(f"✅ Plantilla cargada con **{len(df_plantilla)}** jugadores")
        st.dataframe(df_plantilla, use_container_width=True)

        if len(df_plantilla) < 11:
            st.error(f"🚨 Necesitas al menos 11 jugadores en tu plantilla para formar un XI. Actualmente tienes {len(df_plantilla)}.", icon="❌")
    else:
        st.info("Esperando a que introduzcas tu plantilla en una de las pestañas de arriba.")


with tab2:
    if df_plantilla.empty:
        st.warning("⬅️ Primero debes introducir tu plantilla en la pestaña anterior.")
        st.stop()
    
    if len(df_plantilla) < 11:
        st.error("🚨 Tu plantilla tiene menos de 11 jugadores. Ve a la pestaña anterior para añadir más.")
        st.stop()

    if st.button("Calcular mi XI ideal", type="primary", use_container_width=True):
        with st.spinner("Buscando coincidencias y optimizando tu alineación..."):
            df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_laliga, cutoff)

        if df_encontrados.empty:
            st.error("No se pudo emparejar ningún jugador. Revisa los nombres o prueba a bajar la 'Sensibilidad' en la barra lateral.")
        else:
            mejor_xi_lista = seleccionar_mejor_xi(df_encontrados, min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total)
            
            if not mejor_xi_lista or len(mejor_xi_lista) < 11:
                st.error("No se pudo construir un XI con las restricciones tácticas indicadas. Intenta flexibilizar los mínimos/máximos en la barra lateral.")
            else:
                st.session_state.df_xi = pd.DataFrame(mejor_xi_lista)
                st.session_state.banca = df_encontrados[~df_encontrados["Mi_nombre"].isin(st.session_state.df_xi["Mi_nombre"])].sort_values("Probabilidad_num", ascending=False)
                st.session_state.no_encontrados = no_encontrados
                st.session_state.df_encontrados = df_encontrados

    if "df_xi" in st.session_state:
        df_xi = st.session_state.df_xi
        df_encontrados = st.session_state.df_encontrados
        media_prob = df_xi["Probabilidad_num"].mean()

        st.header("Tu XI Ideal Recomendado")
        c1, c2 = st.columns(2)
        c1.metric("Jugadores Encontrados", f"{len(df_encontrados)} / {len(df_plantilla)}")
        c2.metric("Probabilidad Media del XI", f"{media_prob:.1f}%")

        html_campo = generar_html_campo(df_xi)
        components.html(html_campo, height=750, scrolling=False)

        # Botones para compartir en redes sociales
        st.divider()
        st.subheader("¡Comparte tu XI con tus rivales!")
        
        # Texto a compartir
        url_app = "https://xi-fantasy.streamlit.app/"
        texto_twitter = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 ¿Crees que puedes superarlo? 😏 {url_app} #FantasyLaLiga #Biwenger #Comunio"
        texto_whatsapp = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 Échale un ojo y dime qué te parece: {url_app}"

        # Enlaces para compartir
        link_twitter = f"https://twitter.com/intent/tweet?text={texto_twitter.replace(' ', '%20')}"
        link_whatsapp = f"https://api.whatsapp.com/send?text={texto_whatsapp.replace(' ', '%20')}"

        # Botones usando markdown para que se vean mejor
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<a href="{link_twitter}" target="_blank" style="text-decoration: none;"><button style="width:100%; height:50px; border-radius:10px; background-color:#1DA1F2; color:white; border:none; font-weight:bold;">Compartir en Twitter</button></a>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<a href="{link_whatsapp}" target="_blank" style="text-decoration: none;"><button style="width:100%; height:50px; border-radius:10px; background-color:#25D366; color:white; border:none; font-weight:bold;">Compartir en WhatsApp</button></a>', unsafe_allow_html=True)
        st.divider()

        st.header("Banquillo Recomendado")
        st.caption("Ordenado por probabilidad de jugar")
        banca = st.session_state.banca
        if banca.empty:
            st.caption("No hay jugadores en el banquillo.")
        else:
            st.dataframe(banca[["Posicion", "Mi_nombre", "Equipo", "Probabilidad"]], use_container_width=True)

        st.header("Exportar XI a PDF")
        pdf_bytes = generar_pdf_xi(df_xi)
        st.download_button("Descargar XI en PDF", data=pdf_bytes, file_name="mi_fantasy_xi.pdf", mime="application/pdf")

        no_encontrados = st.session_state.no_encontrados
        if no_encontrados:
            with st.expander("⚠️ Algunos jugadores no fueron encontrados", expanded=True):
                st.warning("No se encontraron coincidencias para: " + ", ".join(sorted(set(no_encontrados))))
                sugerencias = []
                for nombre in no_encontrados:
                    sug = buscar_nombre_mas_cercano(nombre, df_laliga['Nombre'], cutoff=0.5)
                    if sug: sugerencias.append(f"Para '{nombre}', ¿quizás quisiste decir **{sug}**?")
                if sugerencias:
                    st.info("💡 Sugerencias:\n- " + "\n- ".join(sugerencias))
                st.info("Consejo: Revisa si el nombre está bien escrito o intenta bajar la 'Sensibilidad de matching' en la barra lateral.")

st.markdown(
    """<div class="footer"><p style='font-size: 14px; color: gray;'>
    Tip: Usa el asistente el día antes de la jornada para obtener las mejores probabilidades
    </p></div>""",
    unsafe_allow_html=True
)