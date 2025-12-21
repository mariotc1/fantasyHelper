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

from src.output_generators import generar_pdf_xi, generar_html_alineacion_completa



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

    /* === BOTONES GLOBALES Y ESTÉTICA === */
    .stButton>button {
        border-radius: 20px;
        transition: all 0.2s ease-in-out;
    }
    
    /* Botón Primario (Calcular XI, Guardar Cambios) */
    .stButton[aria-label="Calcular mi XI ideal"]>button,
    .stButton[aria-label="💾 Guardar cambios"]>button {
        color: white;
        background-color: #4F8BF9;
        border: 1px solid #4F8BF9;
        font-weight: bold;
    }
    
    .stButton[aria-label="💾 Guardar cambios"]>button:disabled {
        background-color: #374151;
        color: #6B7280;
        border: none;
    }

    /* Botón Destructivo (Borrar plantilla) */
    .stButton[aria-label="🗑️ Eliminar todos los jugadores"]>button {
        color: white;
        background-color: #D32F2F;
        border-color: #D32F2F;
    }
    .stButton[aria-label="🗑️ Eliminar todos los jugadores"]>button:hover {
        background-color: #C62828;
        border-color: #C62828;
    }

    /* Formulario Añadir Jugador */
    form[data-testid="stForm"] button {
        background-color: #166534;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 24px;
    }

    /* === OTROS ESTILOS === */
    div[data-testid="metric-container"] {
        background-color: rgba(230, 240, 255, 0.5);
        border-radius: 10px; padding: 15px;
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



    # Método 1: Uno a uno con la nueva UI profesional
    with input_method_tab1:
        st.caption("Añade jugadores a tu lista. Los cambios se guardan automáticamente.")

        # --- GESTIÓN DE ESTADO Y AUTOGUARDADO ---

        # 1. Cargar la plantilla desde localStorage si no está en el estado de la sesión.
        if "plantilla_bloques" not in st.session_state:
            plantilla_guardada_str = localS.getItem("fantasy_plantilla")
            st.session_state.plantilla_bloques = json.loads(plantilla_guardada_str) if plantilla_guardada_str else []
            
            # Ordenar la plantilla inicial
            pos_order = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
            st.session_state.plantilla_bloques.sort(key=lambda p: pos_order.get(p.get("Posicion"), 99))

            if plantilla_guardada_str:
                st.toast("¡Hemos cargado tu plantilla guardada!", icon="👍")
        
        # Inicializar el estado de 'previous_plantilla' para el seguimiento de cambios
        if "previous_plantilla" not in st.session_state:
            st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()

        # 2. Comprobar si hay cambios y autoguardar
        current_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.plantilla_bloques], key=lambda x: x['Nombre'])
        previous_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.previous_plantilla], key=lambda x: x['Nombre'])

        if current_norm != previous_norm:
            with st.spinner("Guardando..."):
                localS.setItem("fantasy_plantilla", json.dumps(st.session_state.plantilla_bloques))
                st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
                st.toast("Cambios guardados automáticamente!", icon="💾")
                time.sleep(0.5) # Pequeña pausa para que el usuario perciba el guardado
                st.rerun()

        # 3. Manejar acciones desde la URL (para el botón personalizado)
        if st.query_params.get("action") == "confirm_delete":
            st.session_state.show_confirm_dialog = True
            st.query_params.clear()
            st.rerun()

        # --- FORMULARIO PARA AÑADIR JUGADOR ---
        with st.form(key="add_player_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([0.6, 0.3, 0.1])
            nombre_placeholder = "Selecciona un jugador..."
            pos_placeholder = "Posición"
            nuevo_nombre = c1.selectbox("Nombre", [nombre_placeholder] + nombres_laliga, label_visibility="collapsed")
            nueva_pos = c2.selectbox("Pos", [pos_placeholder, "POR", "DEF", "CEN", "DEL"], label_visibility="collapsed")
            
            submitted = c3.form_submit_button("➕", help="Añadir jugador a la lista")

            if submitted and nuevo_nombre != nombre_placeholder and nueva_pos != pos_placeholder:
                if any(p['Nombre'] == nuevo_nombre for p in st.session_state.plantilla_bloques):
                    st.toast(f"{nuevo_nombre} ya está en tu plantilla.", icon="⚠️")
                else:
                    nuevo_jugador = {"id": int(time.time() * 1000), "Nombre": nuevo_nombre, "Posicion": nueva_pos}
                    st.session_state.plantilla_bloques.append(nuevo_jugador)
                    
                    pos_order = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
                    st.session_state.plantilla_bloques.sort(key=lambda p: pos_order.get(p.get("Posicion"), 99))
                    st.rerun()
        
        # Mensaje de estado de autoguardado nativo de Streamlit
        if st.session_state.plantilla_bloques:
            st.success("✅ Plantilla guardada automáticamente")

        st.divider()

        # Mostrar la lista de jugadores con el nuevo componente
        if st.session_state.plantilla_bloques:
            # Contenedor para aplicar estilos a las filas generadas por Streamlit
            with st.container():
                for i, bloque in enumerate(st.session_state.plantilla_bloques):
                    col1, col2 = st.columns([0.8, 0.2])
                    pos_class = f"pos-{bloque['Posicion'].lower()}"
                    
                    # Contenido del jugador (columna 1)
                    col1.markdown(f"""
                    <div class="player-row-st">
                        <span class="player-name-st">{bloque['Nombre']}</span>
                        <span class="position-chip-st {pos_class}">{bloque['Posicion']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botón de eliminar (columna 2)
                    if col2.button("Eliminar jugador", key=f"del_{bloque['id']}", help=f"Quitar a {bloque['Nombre']}"):
                        st.session_state.show_confirm_delete_player = True
                        st.session_state.player_to_delete_id = bloque['id']
                        st.rerun()

            df_plantilla = pd.DataFrame(st.session_state.plantilla_bloques)
            if not df_plantilla.empty:
                df_plantilla = df_plantilla.drop(columns=['id']).drop_duplicates(subset=["Nombre"])

            # --- Acción de Limpieza ---
            st.divider()
            c1, c2, c3 = st.columns([0.6, 0.4, 0.1]) # Columnas para centrar el botón
            with c2:
                if st.button("🗑️ Eliminar todos los jugadores", help="Quitar todos los jugadores de la plantilla", type="primary", use_container_width=True):
                    st.session_state.show_confirm_dialog = True
        else:
            st.info("Añade tu primer jugador usando el formulario de arriba.")

        # Lógica del diálogo de confirmación para eliminar todos los jugadores
        if "show_confirm_dialog" not in st.session_state:
            st.session_state.show_confirm_dialog = False

        if st.session_state.show_confirm_dialog:
            @st.dialog("Confirmar eliminación total")
            def confirm_delete_all():
                st.warning("¿Estás seguro de que quieres eliminar todos los jugadores de tu plantilla? Esta acción no se puede deshacer.", icon="⚠️")
                
                d_c1, d_c2 = st.columns(2)
                if d_c1.button("Sí, eliminar plantilla", type="primary"):
                    st.session_state.plantilla_bloques = []
                    st.session_state.show_confirm_dialog = False
                    st.rerun()

                if d_c2.button("Cancelar"):
                    st.session_state.show_confirm_dialog = False
                    st.rerun()
            
            confirm_delete_all()

        # Lógica del diálogo de confirmación para eliminar un jugador individual
        if "show_confirm_delete_player" not in st.session_state:
            st.session_state.show_confirm_delete_player = False

        if st.session_state.show_confirm_delete_player:
            player_id_to_delete = st.session_state.get("player_to_delete_id")
            player_to_delete = next((p for p in st.session_state.plantilla_bloques if p.get('id') == player_id_to_delete), None)

            @st.dialog("Confirmar eliminación")
            def confirm_player_delete():
                if player_to_delete:
                    st.warning(f"¿Estás seguro de que quieres eliminar a **{player_to_delete['Nombre']}** de tu plantilla?", icon="⚠️")
                else:
                    st.warning("¿Estás seguro de que quieres eliminar este jugador?", icon="⚠️")

                d_c1, d_c2 = st.columns(2)
                if d_c1.button("Sí, eliminar", type="primary"):
                    st.session_state.plantilla_bloques = [p for p in st.session_state.plantilla_bloques if p.get('id') != player_id_to_delete]
                    st.session_state.show_confirm_delete_player = False
                    del st.session_state.player_to_delete_id
                    st.rerun()

                if d_c2.button("Cancelar"):
                    st.session_state.show_confirm_delete_player = False
                    del st.session_state.player_to_delete_id
                    st.rerun()
            
            if player_to_delete:
                confirm_player_delete()
            else: # Failsafe por si el estado se vuelve inconsistente
                st.session_state.show_confirm_delete_player = False
                if "player_to_delete_id" in st.session_state:
                    del st.session_state.player_to_delete_id
        
        # CSS para 'theming' de los widgets de Streamlit
        st.markdown("""
        <style>
            /* Contenedor principal de la lista de jugadores */
            div[data-testid="stVerticalBlock"] > div.st-emotion-cache-1jicfl2 {
                background-color: #111827;
                border-radius: 8px;
                padding: 8px;
            }
            
            /* --- FORZAR FILA EN MÓVIL --- */
            /* Contenedor de CADA FILA de jugador (st.columns) */
            div.st-emotion-cache-1jicfl2 > div[data-testid="stHorizontalBlock"] {
                flex-direction: row !important; /* Evita que las columnas se apilen en móvil */
                align-items: center;
                border-bottom: 1px solid #374151;
                transition: background-color 0.2s ease-in-out;
            }
            div.st-emotion-cache-1jicfl2 > div[data-testid="stHorizontalBlock"]:hover {
                background-color: #1F2937;
            }
            div.st-emotion-cache-1jicfl2 > div[data-testid="stHorizontalBlock"]:last-child {
                border-bottom: none;
            }

            /* Contenedor del nombre y posición del jugador */
            .player-row-st {
                display: flex;
                flex-direction: row;
                align-items: center;
                gap: 16px;
                padding: 8px 0;
            }
            .player-name-st { font-size: 1rem; font-weight: 700; color: #F9FAFB; }
            .position-chip-st {
                font-size: 0.75rem; font-weight: 500; padding: 2px 8px; border-radius: 12px;
            }
            .pos-por { background-color: rgba(234, 179, 8, 0.1); color: #FBBF24; }
            .pos-def { background-color: rgba(59, 130, 246, 0.1); color: #60A5FA; }
            .pos-cen { background-color: rgba(16, 185, 129, 0.1); color: #34D399; }
            .pos-del { background-color: rgba(239, 68, 68, 0.1); color: #F87171; }

            /* Botón de eliminar (dentro de la fila del jugador) */
            div[data-testid="stButton"] > button[kind="secondary"] {
                background-color: rgba(239, 68, 68, 0.1) !important;
                color: #F87171 !important;
                border: none !important;
                padding: 2px 8px !important; /* Reducir padding para bajar altura */
                border-radius: 12px !important;
                font-size: 0.75rem !important;
                font-weight: 500 !important;
                line-height: 1.4 !important; /* Ajustar para centrado vertical */
                height: auto !important;
                transition: background-color 0.2s, transform 0.2s;
            }
            div[data-testid="stButton"] > button[kind="secondary"]:hover {
                background-color: rgba(239, 68, 68, 0.2) !important;
                transform: scale(1.05);
            }
            div[data-testid="stButton"] > button[kind="secondary"]:active {
                transform: scale(0.98);
            }
        </style>
        """, unsafe_allow_html=True)


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



    # Procesamiento y visualización común para métodos 2 y 3
    if not df_plantilla.empty and (input_method_tab2 or input_method_tab3):
        if df_plantilla['Nombre'].duplicated().any():
            st.warning("⚠️ Se han detectado y eliminado jugadores duplicados.", icon="❗")
            df_plantilla = df_plantilla.drop_duplicates(subset=['Nombre'], keep='first')

        st.success(f"✅ Plantilla cargada con **{len(df_plantilla)}** jugadores. Comprueba las coincidencias a continuación:")
        
        # Emparejar jugadores con datos de LaLiga
        df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_laliga, cutoff)

        if not df_encontrados.empty:
            st.dataframe(df_encontrados[['Mi_nombre', 'Posicion', 'Equipo', 'Probabilidad']], use_container_width=True)

        # Mostrar jugadores no encontrados si los hay
        if no_encontrados:
            st.warning(f"⚠️ **{len(no_encontrados)} Jugadores no encontrados:** " + ", ".join(sorted(set(no_encontrados))))
            sugerencias = [f"Para '{n}', ¿quizás quisiste decir **{sug}**?" for n in no_encontrados if (sug := buscar_nombre_mas_cercano(n, df_laliga['Nombre'], 0.5))]
            if sugerencias: st.info("💡 Sugerencias:\n- " + "\n- ".join(sugerencias))

        # Mensaje si ningún jugador fue encontrado
        if df_encontrados.empty and not df_plantilla.empty:
            st.error("No se pudo encontrar ningún jugador de tu plantilla. Revisa los nombres o ajusta la 'Sensibilidad de matching' en la barra lateral.")

    # Comprobación general del número de jugadores para todos los métodos
    if not df_plantilla.empty and len(df_plantilla) < 11:
        st.error(f"🚨 Necesitas al menos 11 jugadores para calcular un XI. Tienes {len(df_plantilla)}.", icon="❌")
    elif df_plantilla.empty and input_method_tab1:
        pass # No mostrar mensaje de error si la lista manual está vacía
    elif df_plantilla.empty:
        st.info("Esperando a que introduzcas tu plantilla en una de las pestañas de arriba.")


# --- PESTAÑAS 2: XI IDEAL Y BANQUILLO ---
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



        with st.spinner("Generando enlaces de descarga..."):

            # 1. Generar todos los artefactos

            pdf_bytes = generar_pdf_xi(df_xi)

            

            # 2. Codificar a Base64

            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")



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

            generar_html_alineacion_completa(df_xi, banca, pdf_base64, link_twitter, link_whatsapp),

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