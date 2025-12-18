import time
import base64
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_local_storage import LocalStorage

# Importaciones de los módulos refactorizados
from src.scraper import scrape_laliga
from src.data_utils import parsear_plantilla_pegada, df_desde_csv_subido
from src.core import emparejar_con_datos, seleccionar_mejor_xi, buscar_nombre_mas_cercano
from src.output_generators import generar_pdf_xi, generar_html_alineacion_completa, generar_bytes_imagen

# --- CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide", initial_sidebar_state="expanded")

# Google Analytics
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

# Estilos CSS
st.markdown("""
<style>
    .stButton>button {
        border-radius: 20px; border: 1px solid #4F8BF9; color: #4F8BF9;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border: 1px solid #0B5ED7; color: #0B5ED7; transform: scale(1.02);
    }
    .stButton[aria-label="Calcular mi XI ideal"]>button {
        color: white; background-color: #4F8BF9; border-radius: 20px; border: none;
        font-weight: bold; font-size: 1.1em; transition: all 0.3s ease-in-out;
    }
    .stButton[aria-label="Calcular mi XI ideal"]>button:hover {
        background-color: #0B5ED7; color: white; transform: scale(1.02);
        box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="metric-container"] {
        background-color: rgba(230, 240, 255, 0.5); border-radius: 10px; padding: 15px;
    }
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #ffffff; text-align: center; padding: 8px;
        z-index: 9999; border-top: 1px solid #e0e0e0;
    }
    @media (prefers-color-scheme: dark) {
        .footer { background-color: #0e1117; border-top: 1px solid #262730; }
        div[data-testid="metric-container"] { background-color: rgba(38, 39, 48, 0.8); }
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN ---
localS = LocalStorage()
st.title("Fantasy XI Assistant")
st.caption("Calcula tu alineación ideal con datos de probabilidad en tiempo real")

# Carga de datos principales
df_laliga = scrape_laliga()
if df_laliga.empty:
    st.error("🔴 No se pudieron cargar los datos de los jugadores de LaLiga. La aplicación no puede continuar.")
    st.stop()
nombres_laliga = sorted(df_laliga["Nombre"].unique())


# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://play-lh.googleusercontent.com/xx7OVI90d-d6pvQlqmAAeUo4SzvLsrp9uss8XPO1ZwILEeTCpjYFVRuL550bUqlicy0=w240-h480-rw", width=80)
    st.header("Configuración del XI")

    st.subheader("Sensibilidad")
    cutoff = st.slider("Matching de nombres", 0.3, 1.0, 0.6, 0.05, help="Un valor más bajo puede encontrar más coincidencias si los nombres no son exactos, pero puede cometer errores.")

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
    if (min_def + min_cen + min_del + 1) > 11: st.error("La suma de mínimos es > 11. Formación imposible.")
    
    st.subheader("Ajustes Fijos")
    c1, c2 = st.columns(2)
    c1.number_input("Nº POR", 1, 1, 1, disabled=True) 
    c2.number_input("Total en XI", 11, 11, 11, disabled=True)
    num_por, total = 1, 11

    with st.expander("Ver todos los datos de LaLiga"):
        st.caption(f"Datos cargados: {len(df_laliga)} registros únicos.")
        st.dataframe(df_laliga, use_container_width=True)


# --- PESTAÑAS PRINCIPALES ---
tab1, tab2 = st.tabs(["1️⃣ Introduce tu Plantilla", "2️⃣ Tu XI Ideal y Banquillo"])
df_plantilla = pd.DataFrame()

with tab1:
    st.header("Añade los jugadores de tu equipo")
    st.info("Puedes añadir tus jugadores de 3 maneras. Elige la que prefieras:", icon="👇")
    
    input_method_tab1, input_method_tab2, input_method_tab3 = st.tabs(["✍️ Uno a uno", "📋 Pegar lista", "📁 Subir archivo"])

    # Método 1: Uno a uno
    with input_method_tab1:
        st.caption("Añade o elimina jugadores. Tus cambios se guardarán en el navegador para la próxima visita")

        if "plantilla_bloques" not in st.session_state:
            plantilla_guardada_str = localS.getItem("fantasy_plantilla")
            st.session_state.plantilla_bloques = json.loads(plantilla_guardada_str) if plantilla_guardada_str else [{"id": i, "Nombre": "", "Posicion": ""} for i in range(11)]
            if plantilla_guardada_str: st.toast("¡Hemos cargado tu plantilla guardada!", icon="👍")

        POS_OPTIONS = ["Elige una posición...", "POR", "DEF", "CEN", "DEL"]
        NAME_OPTIONS = ["Selecciona un jugador..."] + nombres_laliga
        
        for i, bloque in enumerate(st.session_state.plantilla_bloques):
            with st.container(border=True):
                c1, c2 = st.columns([0.85, 0.15])
                idx_nombre = NAME_OPTIONS.index(bloque["Nombre"]) if bloque["Nombre"] in NAME_OPTIONS else 0
                idx_pos = POS_OPTIONS.index(bloque["Posicion"]) if bloque["Posicion"] in POS_OPTIONS else 0
                
                c1.selectbox(f"Nombre_{i}", NAME_OPTIONS, index=idx_nombre, key=f"nombre_{bloque['id']}", label_visibility="collapsed")
                c1.selectbox(f"Pos_{i}", POS_OPTIONS, index=idx_pos, key=f"pos_{bloque['id']}", label_visibility="collapsed")
                
                if c2.button("❌", key=f"del_{bloque['id']}", help="Quitar este jugador"):
                    st.session_state.plantilla_bloques.pop(i)
                    st.rerun()

        if st.button("➕ Añadir jugador"):
            st.session_state.plantilla_bloques.append({"id": int(time.time() * 1000), "Nombre": "", "Posicion": ""})
            st.rerun()

        st.divider()

        plantilla_actual = [{"id": b['id'], "Nombre": st.session_state[f"nombre_{b['id']}"], "Posicion": st.session_state[f"pos_{b['id']}"]} for b in st.session_state.plantilla_bloques]
        plantilla_actual_filtrada = [b for b in plantilla_actual if b.get("Nombre", "Selecciona...") != "Selecciona un jugador..." and b.get("Posicion", "Elige...") != "Elige una posición..."]
        
        plantilla_guardada_str = localS.getItem("fantasy_plantilla")
        plantilla_guardada = json.loads(plantilla_guardada_str) if plantilla_guardada_str else []
        hay_cambios = plantilla_actual_filtrada != plantilla_guardada

        c1, c2 = st.columns(2)
        if c1.button("💾 Guardar cambios", type="primary", disabled=not hay_cambios):
            localS.setItem("fantasy_plantilla", json.dumps(plantilla_actual_filtrada))
            st.success("¡Plantilla guardada con éxito!"); time.sleep(1); st.rerun()

        if c2.button("🗑️ Borrar plantilla guardada"):
            localS.setItem("fantasy_plantilla", None)
            st.session_state.plantilla_bloques = [{"id": i, "Nombre": "", "Posicion": ""} for i in range(11)]
            st.info("Plantilla guardada eliminada."); st.rerun()
        
        if hay_cambios: st.warning("Tienes cambios sin guardar", icon="⚠️")
        elif plantilla_guardada: st.success("Plantilla sincronizada", icon="✅")
        
        df_plantilla_manual = pd.DataFrame(plantilla_actual_filtrada)
        if not df_plantilla_manual.empty:
            df_plantilla = df_plantilla_manual.drop(columns=['id']).drop_duplicates(subset=["Nombre"])

    # Método 2: Pegar lista
    with input_method_tab2:
        texto_plantilla = st.text_area("Pega tu plantilla aquí (Ej: `Courtois, POR`)", height=250, help="Formato: Nombre, Posición. Un jugador por línea.")
        if texto_plantilla: df_plantilla = parsear_plantilla_pegada(texto_plantilla)

    # Método 3: Subir archivo
    with input_method_tab3:
        archivo_subido = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])
        if archivo_subido:
            df_subido = df_desde_csv_subido(archivo_subido)
            if "Nombre" in df_subido and "Posicion" in df_subido: df_plantilla = df_subido
            else: st.warning("El archivo debe contener las columnas 'Nombre' y 'Posicion'.")

    # Muestra la plantilla cargada
    if not df_plantilla.empty:
        if df_plantilla['Nombre'].duplicated().any():
            st.warning("⚠️ Se han detectado y eliminado jugadores duplicados.", icon="❗")
            df_plantilla = df_plantilla.drop_duplicates(subset=['Nombre'], keep='first')
        
        st.success(f"✅ Plantilla cargada con **{len(df_plantilla)}** jugadores")
        st.dataframe(df_plantilla, use_container_width=True)
        if len(df_plantilla) < 11: st.error(f"🚨 Necesitas al menos 11 jugadores. Tienes {len(df_plantilla)}.", icon="❌")
    else:
        st.info("Esperando a que introduzcas tu plantilla en una de las pestañas de arriba.")


# --- PESTAÑA 2: XI IDEAL Y BANQUILLO ---
with tab2:
    if df_plantilla.empty or len(df_plantilla) < 11:
        st.warning("⬅️ Primero debes introducir una plantilla con al menos 11 jugadores en la pestaña anterior.")
        st.stop()

    if st.button("Calcular mi XI ideal", type="primary", use_container_width=True):
        with st.spinner("Buscando coincidencias y optimizando tu alineación..."):
            df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_laliga, cutoff)

        if df_encontrados.empty:
            st.error("No se pudo emparejar ningún jugador. Revisa los nombres o baja la 'Sensibilidad' en la barra lateral.")
        else:
            xi_lista = seleccionar_mejor_xi(df_encontrados, min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total)
            if not xi_lista or len(xi_lista) < 11:
                st.error("No se pudo construir un XI con las restricciones tácticas. Intenta flexibilizar los mínimos/máximos.")
            else:
                st.session_state.df_xi = pd.DataFrame(xi_lista)
                st.session_state.banca = df_encontrados[~df_encontrados["Mi_nombre"].isin(st.session_state.df_xi["Mi_nombre"])].sort_values("Probabilidad_num", ascending=False)
                st.session_state.no_encontrados = no_encontrados
                st.session_state.df_encontrados = df_encontrados

    if "df_xi" in st.session_state:
        df_xi = st.session_state.df_xi
        banca = st.session_state.banca
        df_encontrados = st.session_state.df_encontrados
        
        st.header("Tu XI Ideal Recomendado")
        c1, c2 = st.columns(2)
        c1.metric("Jugadores Encontrados", f"{len(df_encontrados)} / {len(df_plantilla)}")
        c2.metric("Probabilidad Media del XI", f"{df_xi['Probabilidad_num'].mean():.1f}%")

        with st.spinner("Generando imagen y enlaces de descarga..."):
            # 1. Generar todos los artefactos
            pdf_bytes = generar_pdf_xi(df_xi)
            image_bytes = generar_bytes_imagen(df_xi, banca)
            
            # 2. Codificar a Base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # 3. Preparar enlaces de compartir
        url_app = "https://xi-fantasy.streamlit.app/"
        texto_twitter = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 ¿Puedes superarlo? 😏 {url_app} #FantasyLaLiga #LALIGAFANTASY"
        texto_whatsapp = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 Échale un ojo: {url_app}"
        link_twitter = f"https://x.com/intent/tweet?text={texto_twitter.replace(' ', '%20')}"
        link_whatsapp = f"https://api.whatsapp.com/send?text={texto_whatsapp.replace(' ', '%20')}"
        
        # 4. Calcular altura dinámica y renderizar el componente HTML unificado
        num_suplentes = len(banca)
        altura_base = 700
        if num_suplentes > 0:
            filas_suplentes = -(-num_suplentes // 5)
            altura_adicional = 100 + (filas_suplentes * 150)
            altura_total = altura_base + altura_adicional
        else:
            altura_total = altura_base

        components.html(
            generar_html_alineacion_completa(df_xi, banca, pdf_base64, image_base64, link_twitter, link_whatsapp), 
            height=altura_total, 
            scrolling=False
        )

        # 5. Mostrar jugadores no encontrados
        if st.session_state.no_encontrados:
            with st.expander("⚠️ Algunos jugadores no fueron encontrados", expanded=True):
                st.warning("No se encontraron coincidencias para: " + ", ".join(sorted(set(st.session_state.no_encontrados))))
                sugerencias = [f"Para '{n}', ¿quizás quisiste decir **{sug}**?" for n in st.session_state.no_encontrados if (sug := buscar_nombre_mas_cercano(n, df_laliga['Nombre'], 0.5))]
                if sugerencias: st.info("💡 Sugerencias:\n- " + "\n- ".join(sugerencias))

# --- FOOTER ---
st.markdown("<div class='footer'><p style='font-size: 14px; color: gray;'>Tip: Usa el asistente el día antes de la jornada para obtener las mejores probabilidades</p></div>", unsafe_allow_html=True)