# IMPORTACIONES DE LIBRERÍAS EXTERNAS
import time, base64, json, os
import pandas as pd
import streamlit as st
from streamlit_local_storage import LocalStorage

# IMPORTACIONES DE FUNCIONES INTERNAS
from src.scraper import scrape_laliga
from src.state_manager import initialize_session_state, autosave_plantilla, emergency_data_recovery
from src.ui.sidebar import render_sidebar
from src.ui.input_tabs import render_input_tabs
from src.ui.results_tab import render_results_tab

# CONFIGURACIÓN DE PÁGINA Y ESTILOS
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide", initial_sidebar_state="expanded")


# CARGA EL FICHERO LOCAL Y LO INYECTA EN EL HTML DE LA APP
def inject_local_file(file_path, as_style=False):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if as_style:
                st.markdown(f"<style>{content}</style>", unsafe_allow_html=True)
            else:
                st.markdown(content, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Error: No se encontró el fichero {file_path}")


# CONSTRUIR RUTAS A ASSETS DE FORMA ROBUSTA
script_dir = os.path.dirname(os.path.abspath(__file__))
ga_path = os.path.join(script_dir, "assets", "google_analytics.html")
css_path = os.path.join(script_dir, "assets", "styles.css")


# INYECTAR GOOGLE ANALYTICS Y CSS
inject_local_file(ga_path)
inject_local_file(css_path, as_style=True)


# INICIALIZACIÓN Y TÍTULO
localS = LocalStorage()
st.title("Fantasy XI Assistant")
st.caption("Calcula tu alineación ideal con datos de probabilidad en tiempo real")


# FLUJO PRINCIPAL DE LA APLICACIÓN 

# 1. CARGA DE DATOS PRINCIPALES
df_laliga = scrape_laliga()

if df_laliga.empty:
    st.error("🔴 No se pudieron cargar los datos de los jugadores de LaLiga. La aplicación no puede continuar.")
    st.stop()
nombres_laliga = sorted(df_laliga["Nombre"].unique())


# 2. INICIALIZACIÓN Y GESTIÓN DE ESTADO
initialize_session_state(localS)

# 2.1. RECUPERACIÓN DE EMERGENCIA PARA DISPOSITIVOS ANDROID
if not st.session_state.plantilla_bloques:
    if emergency_data_recovery(localS):
        st.stop()  # Detener si se encontraron datos para recuperar

autosave_plantilla(localS)


# 3. RENDERIZAR LA BARRA LATERAL Y OBTENER CONFIGURACIÓN
params = render_sidebar(df_laliga)
cutoff, min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total = params
tactica = (min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total)


# 4. RENDERIZAR PESTAÑAS PRINCIPALES
tab1, tab2 = st.tabs(["1️⃣ Introduce tu Plantilla", "2️⃣ Tu XI Ideal y Banquillo"])
df_plantilla = pd.DataFrame()

with tab1:
    # RENDERIZAR PESTAÑA DE ENTRADA Y OBTENER PLANTILLA
    df_plantilla = render_input_tabs(nombres_laliga, df_laliga, cutoff)

with tab2:
    # RENDERIZAR PESTAÑA DE RESULTADOS Y MOSTRAR RESULTADOS
    render_results_tab(df_plantilla, df_laliga, cutoff, tactica)


# FOOTER
st.markdown("<div class='footer'><p style='font-size: 14px; color: gray;'>Tip: Usa el asistente el día antes de la jornada para obtener las mejores probabilidades</p></div>", unsafe_allow_html=True)