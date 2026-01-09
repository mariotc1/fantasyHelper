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

# PANEL DE DIAGNÓSTICO (solo visible en desarrollo o cuando se activa)
if st.sidebar.checkbox("🔧 Modo Debug/Diagnóstico", help="Activa el diagnóstico para detectar problemas en Android"):
    st.session_state.debug_mode = True
    
    # Mostrar información del dispositivo
    from src.state_manager import detect_device_info, log_debug_info
    device_info = detect_device_info()
    st.sidebar.success(f"📱 Dispositivo detectado: {device_info}")
    
    # Botón para ver log de debug
    if st.sidebar.button("📋 Ver Log de Debug"):
        if "debug_log" in st.session_state and st.session_state.debug_log:
            st.sidebar.write("**Log de eventos:**")
            for i, entry in enumerate(st.session_state.debug_log[-20:]):  # Últimos 20 eventos
                with st.sidebar.expander(f"{entry['timestamp']} - {entry['message']}"):
                    if entry.get('data'):
                        st.json(entry['data'])
        else:
            st.sidebar.write("No hay eventos en el log")
    
    # Botón para forzar diagnóstico completo
    if st.sidebar.button("🔍 Diagnóstico Completo"):
        from src.state_manager import safe_get_item
        test_result = safe_get_item(localS, "fantasy_plantilla", "TEST_FALLBACK")
        st.sidebar.json({
            "localStorage_test": test_result,
            "session_state_plantilla": len(st.session_state.get("plantilla_bloques", [])),
            "device_info": device_info
        })
    
    # Botón de guardado manual forzado
    if st.sidebar.button("💾 Guardar Manual Forzado", help="Fuerza el guardado de la plantilla actual"):
        from src.state_manager import force_manual_save
        force_manual_save(localS)
        
else:
    st.session_state.debug_mode = False

# BOTÓN DE GUARDADO MANUAL PARA TODOS LOS USUARIOS (visible si hay jugadores)
if st.session_state.get("plantilla_bloques") and len(st.session_state.plantilla_bloques) > 0:
    if st.sidebar.button("📱 Guardar Cambios Ahora", help="Guarda manualmente tu plantilla (para Android)"):
        from src.state_manager import force_manual_save
        force_manual_save(localS)


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