# LIBRERIAS EXTERNAS (streamlit para UI, pandas para datos, time para timestamps, base64 para codificación)
import streamlit as st
import pandas as pd
import time

# FUNCIONES INTERNAS
from src.data_utils import parsear_plantilla_pegada, df_desde_csv_subido
from src.core import emparejar_con_datos, buscar_nombre_mas_cercano
from src.state_manager import handle_player_deletion_from_url, confirm_player_delete_dialog

# FUNCIONES PRINCIPALES DE RENDERIZADO DE LA PESTAÑA DE ENTRADA
def render_input_tabs(nombres_laliga, df_laliga, cutoff):
    """
    Renderiza la pestaña "Introduce tu Plantilla" con sus tres métodos de entrada.
    Devuelve el DataFrame de la plantilla del usuario.
    """
    st.header("Añade los jugadores de tu equipo")
    st.info("Puedes añadir tus jugadores de 3 maneras. Elige la que prefieras:", icon="👇")

    input_method_tab1, input_method_tab2, input_method_tab3 = st.tabs(["✍️ Uno a uno", "📋 Pegar lista", "📁 Subir archivo"])
    
    df_plantilla = pd.DataFrame()

    # MÉTODO 1: UNO A UNO
    with input_method_tab1:
        df_plantilla = render_manual_input_method(nombres_laliga, df_laliga)

    # MÉTODO 2: Pegar lista
    with input_method_tab2:
        texto_plantilla = st.text_area("Pega tu plantilla aquí (Ej: `Courtois, POR`)", height=250, help="Formato: Nombre, Posición. Un jugador por línea.")
        if texto_plantilla:
            df_plantilla = parsear_plantilla_pegada(texto_plantilla)

    # MÉTODO 3: SUBIR ARCHIVO
    with input_method_tab3:
        archivo_subido = st.file_uploader("Sube un archivo CSV o Excel", type=["csv", "xlsx"])
        if archivo_subido:
            df_subido = df_desde_csv_subido(archivo_subido)
            if "Nombre" in df_subido and "Posicion" in df_subido:
                df_plantilla = df_subido
            else:
                st.warning("El archivo debe contener las columnas 'Nombre' y 'Posicion'.")

    # PROCESAMIENTO COMÚN para métodos 2 y 3
    if not df_plantilla.empty and (input_method_tab2 or input_method_tab3):
        process_and_display_pasted_or_uploaded(df_plantilla, df_laliga, cutoff)

    # Comprobación general del número de jugadores
    if not df_plantilla.empty and len(df_plantilla) < 11:
        st.error(f"🚨 Necesitas al menos 11 jugadores para calcular un XI. Tienes {len(df_plantilla)}.", icon="❌")
    elif df_plantilla.empty and not input_method_tab1:
         st.info("Esperando a que introduzcas tu plantilla en una de las pestañas de arriba.")

    return df_plantilla


def render_manual_input_method(nombres_laliga, df_laliga):
    """
    Renderiza la UI y gestiona la lógica para el método de entrada "Uno a uno".
    """
    st.caption("Añade jugadores a tu lista. Los cambios se guardan automáticamente.")

    handle_player_deletion_from_url()
    confirm_player_delete_dialog()

    # Formulario para añadir jugador
    with st.form(key="add_player_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([0.6, 0.3, 0.1])
        nombre_placeholder, pos_placeholder = "Selecciona un jugador...", "Posición"
        nuevo_nombre = c1.selectbox("Nombre", [nombre_placeholder] + nombres_laliga, label_visibility="collapsed")
        nueva_pos = c2.selectbox("Pos", [pos_placeholder, "POR", "DEF", "CEN", "DEL"], label_visibility="collapsed")
        
        if c3.form_submit_button("➕", help="Añadir jugador a la lista"):
            if nuevo_nombre != nombre_placeholder and nueva_pos != pos_placeholder:
                if any(p['Nombre'] == nuevo_nombre for p in st.session_state.plantilla_bloques):
                    st.toast(f"{nuevo_nombre} ya está en tu plantilla.", icon="⚠️")
                else:
                    nuevo_jugador = {"id": int(time.time() * 1000), "Nombre": nuevo_nombre, "Posicion": nueva_pos}
                    st.session_state.plantilla_bloques.append(nuevo_jugador)
                    pos_order = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
                    st.session_state.plantilla_bloques.sort(key=lambda p: pos_order.get(p.get("Posicion"), 99))
                    st.rerun()

    # Renderizar la plantilla actual
    if st.session_state.plantilla_bloques:
        st.success("✅ Plantilla guardada automáticamente")
        st.divider()
        st.header("Mi plantilla")
        render_player_cards(st.session_state.plantilla_bloques, df_laliga)
        
        df_plantilla = pd.DataFrame(st.session_state.plantilla_bloques)
        if not df_plantilla.empty:
            return df_plantilla.drop(columns=['id']).drop_duplicates(subset=["Nombre"])
    else:
        st.info("Añade tu primer jugador usando el formulario de arriba.")
    
    return pd.DataFrame()


def render_player_cards(plantilla_bloques, df_laliga):
    """
    Renderiza las tarjetas de jugador para la lista de plantilla manual.
    """
    # Asegurar que no hay duplicados por nombre antes de crear el dict
    df_laliga = df_laliga.drop_duplicates(subset=['Nombre'], keep='first')
    df_laliga_data = df_laliga.set_index('Nombre').to_dict('index')
    pos_order = ["POR", "DEF", "CEN", "DEL"]
    pos_names = {"POR": "Porteros", "DEF": "Defensas", "CEN": "Centrocampistas", "DEL": "Delanteros"}
    pos_colors = {
        "POR": ("rgba(234, 179, 8, 0.15)", "#FBBF24"), "DEF": ("rgba(59, 130, 246, 0.15)", "#60A5FA"),
        "CEN": ("rgba(16, 185, 129, 0.15)", "#34D399"), "DEL": ("rgba(239, 68, 68, 0.15)", "#F87171"),
    }

    grouped_players = {pos: [p for p in plantilla_bloques if p.get("Posicion") == pos] for pos in pos_order}

    for pos in pos_order:
        if players_in_pos := grouped_players[pos]:
            st.subheader(pos_names[pos])
            cards_html_list = []
            for jugador in players_in_pos:
                nombre_jugador = jugador.get('Nombre', 'N/A')
                posicion = jugador.get('Posicion', 'N/A')
                laliga_info = df_laliga_data.get(nombre_jugador, {})
                
                nombre_display = nombre_jugador
                if len(nombre_display) > 12:
                    parts = nombre_display.split()
                    nombre_display = f"{parts[0][0]}. {parts[-1]}" if len(parts) > 1 else nombre_display[:11] + "."

                delete_href = f"?action=delete_player&player_id={jugador['id']}"
                bg_color, text_color = pos_colors.get(posicion, ("#374151", "#9CA3AF"))
                
                card_html = (
                    f'<div class="card-container-plantilla">'
                        f'<a href="{delete_href}" target="_self" class="delete-icon-plantilla" title="Eliminar a {nombre_jugador}">'
                            f'<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>'
                        f'</a>'
                        f'<div class="player-card-plantilla">'
                            f'<div class="player-image-small"><img src="{laliga_info.get("Imagen_URL", "https://static.futbolfantasy.com/images/default-black.jpg")}" alt="{nombre_display}" onerror="this.onerror=null;this.src=\'https://static.futbolfantasy.com/images/default-black.jpg\';"></div>'
                            f'<div class="card-body"><div class="p-name">{nombre_display}</div><div class="p-team">{laliga_info.get("Equipo", "")}</div></div>'
                            f'<div class="pos-pill-footer" style="background-color: {bg_color}; color: {text_color};">{posicion}</div>'
                        f'</div>'
                    f'</div>'
                )
                cards_html_list.append(card_html)
            
            st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:flex-start; padding: 10px 0;">{" ".join(cards_html_list)}</div>', unsafe_allow_html=True)


def process_and_display_pasted_or_uploaded(df_plantilla, df_laliga, cutoff):
    """
    Procesa y muestra los resultados para los métodos de pegar o subir archivo.
    """
    if df_plantilla['Nombre'].duplicated().any():
        st.warning("⚠️ Se han detectado y eliminado jugadores duplicados.", icon="❗")
        df_plantilla = df_plantilla.drop_duplicates(subset=['Nombre'], keep='first')

    st.divider()
    st.success(f"✅ Plantilla cargada con **{len(df_plantilla)}** jugadores. Comprueba las coincidencias a continuación:")
    
    df_encontrados, no_encontrados = emparejar_con_datos(df_plantilla, df_laliga, cutoff)

    if not df_encontrados.empty:
        st.dataframe(df_encontrados[['Mi_nombre', 'Posicion', 'Equipo', 'Probabilidad']], use_container_width=True)

    if no_encontrados:
        st.warning(f"⚠️ **{len(no_encontrados)} Jugadores no encontrados:** " + ", ".join(sorted(set(no_encontrados))))
        sugerencias = [f"Para '{n}', ¿quizás quisiste decir **{sug}**?" for n in no_encontrados if (sug := buscar_nombre_mas_cercano(n, df_laliga['Nombre'], 0.5))]
        if sugerencias: st.info("💡 Sugerencias:\n- " + "\n- ".join(sugerencias))

    if df_encontrados.empty and not df_plantilla.empty:
        st.error("No se pudo encontrar ningún jugador. Revisa los nombres o ajusta la 'Sensibilidad' en la barra lateral.")