# LIBRERIAS EXTERNAS (streamlit para UI, json para manejo de datos, time para pausas)
import streamlit as st
import json
import time

# FUNCIONES INTERNAS
def initialize_session_state(localS):
    """
    Carga la plantilla desde localStorage si no está en el estado de la sesión,
    y también inicializa el estado de seguimiento de cambios.
    """
    if "plantilla_bloques" not in st.session_state:
        plantilla_guardada_str = localS.getItem("fantasy_plantilla")
        try:
            st.session_state.plantilla_bloques = json.loads(plantilla_guardada_str) if plantilla_guardada_str else []
        except (json.JSONDecodeError, TypeError):
            st.error("⚠️ No se pudo cargar tu plantilla guardada porque los datos estaban corruptos. Empezando con una plantilla vacía.", icon="🚨")
            st.session_state.plantilla_bloques = []

        
        pos_order = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
        st.session_state.plantilla_bloques.sort(key=lambda p: pos_order.get(p.get("Posicion"), 99))

        if plantilla_guardada_str:
            st.toast("¡Hemos cargado tu plantilla guardada!", icon="👍")
    
    if "previous_plantilla" not in st.session_state:
        st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()


def autosave_plantilla(localS):
    """
    Compara la plantilla actual con la guardada previamente y, si hay cambios,
    la guarda en localStorage y actualiza el estado.
    """
    current_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.plantilla_bloques], key=lambda x: x['Nombre'])
    previous_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.previous_plantilla], key=lambda x: x['Nombre'])

    if current_norm != previous_norm:
        with st.spinner("Guardando..."):
            localS.setItem("fantasy_plantilla", json.dumps(st.session_state.plantilla_bloques))
            st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
            st.toast("Cambios guardados automáticamente!", icon="💾")
            time.sleep(0.5)
            st.rerun()


def handle_player_deletion_from_url():
    """
    Comprueba los query params de la URL para iniciar el proceso de eliminación
    de un jugador y actualiza el estado de la sesión para mostrar el diálogo.
    """
    if st.query_params.get("action") == "delete_player":
        player_id_to_delete = st.query_params.get("player_id")
        if player_id_to_delete:
            try:
                st.session_state.show_confirm_delete_player = True
                st.session_state.player_to_delete_id = int(player_id_to_delete)
                st.query_params.clear()
                st.rerun()
            except (ValueError, TypeError):
                # Si el player_id no es un entero válido, simplemente lo ignoramos.
                st.query_params.clear()
                st.rerun()


def confirm_player_delete_dialog():
    """
    Muestra un diálogo de confirmación para eliminar a un jugador. Si el usuario
    confirma, elimina el jugador de la plantilla en el estado de la sesión.
    """
    if "show_confirm_delete_player" not in st.session_state:
        st.session_state.show_confirm_delete_player = False

    if st.session_state.show_confirm_delete_player:
        player_id_to_delete = st.session_state.get("player_to_delete_id")
        player_to_delete = next((p for p in st.session_state.plantilla_bloques if p.get('id') == player_id_to_delete), None)

        @st.dialog("Confirmar eliminación")
        def confirm_dialog_ui():
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
            confirm_dialog_ui()
        else: # Failsafe
            st.session_state.show_confirm_delete_player = False
            if "player_to_delete_id" in st.session_state:
                del st.session_state.player_to_delete_id