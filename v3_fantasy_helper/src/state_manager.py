# LIBRERIAS EXTERNAS (streamlit para UI, json para manejo de datos, time para pausas)
import streamlit as st
import json
import time
import logging

# FUNCIONES INTERNAS
def safe_get_item(localS, key, fallback=None):
    """
    Obtiene un elemento de localStorage de forma segura con manejo de errores
    y fallback para dispositivos Android.
    """
    try:
        # Intentar obtener el valor normalmente
        value = localS.getItem(key)
        if value is not None:
            return value
        
        # Fallback para dispositivos Android: intentar con session storage
        if hasattr(st.session_state, f'{key}_fallback'):
            return st.session_state[f'{key}_fallback']
            
        return fallback
    except Exception as e:
        # Registrar error y usar fallback
        logging.error(f"Error al obtener {key} de localStorage: {str(e)}")
        if hasattr(st.session_state, f'{key}_fallback'):
            return st.session_state[f'{key}_fallback']
        return fallback

def safe_set_item(localS, key, value):
    """
    Guarda un elemento en localStorage de forma segura con manejo de errores
    y fallback para dispositivos Android.
    """
    try:
        # Intentar guardar en localStorage
        localS.setItem(key, value)
        
        # También guardar en session state como fallback
        st.session_state[f'{key}_fallback'] = value
        return True
    except Exception as e:
        # Registrar error y usar solo fallback
        logging.error(f"Error al guardar {key} en localStorage: {str(e)}")
        st.session_state[f'{key}_fallback'] = value
        return False

def initialize_session_state(localS):
    """
    Carga la plantilla desde localStorage si no está en el estado de la sesión,
    y también inicializa el estado de seguimiento de cambios.
    """
    if "plantilla_bloques" not in st.session_state:
        plantilla_guardada_str = safe_get_item(localS, "fantasy_plantilla")
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
    
    # Inicializar bandera para evitar guardados automáticos prematuros
    if "initialized" not in st.session_state:
        st.session_state.initialized = False


def autosave_plantilla(localS):
    """
    Compara la plantilla actual con la guardada previamente y, si hay cambios,
    la guarda en localStorage y actualiza el estado.
    """
    # Evitar guardados automáticos prematuros antes de la inicialización completa
    if not st.session_state.get("initialized", False):
        st.session_state.initialized = True
        return
    
    # Solo proceder si hay datos válidos en la plantilla actual
    if not st.session_state.plantilla_bloques:
        return
    
    current_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.plantilla_bloques], key=lambda x: x['Nombre'])
    previous_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.previous_plantilla], key=lambda x: x['Nombre'])

    if current_norm != previous_norm:
        try:
            with st.spinner("Guardando..."):
                # Validación adicional antes de guardar
                if st.session_state.plantilla_bloques and all(p.get('Nombre') and p.get('Posicion') for p in st.session_state.plantilla_bloques):
                    success = safe_set_item(localS, "fantasy_plantilla", json.dumps(st.session_state.plantilla_bloques))
                    st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
                    
                    if success:
                        st.toast("Cambios guardados automáticamente!", icon="💾")
                    else:
                        st.toast("Cambios guardados en modo seguro (dispositivo Android)", icon="📱")
                    
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("⚠️ No se pueden guardar datos inválidos", icon="🚨")
        except Exception as e:
            st.error(f"⚠️ Error crítico al guardar: {str(e)}", icon="🚨")
            # Intentar guardado de emergencia en session state
            st.session_state.emergency_plantilla = st.session_state.plantilla_bloques.copy()

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


def confirm_player_delete_dialog(localS=None):
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
                # Forzar guardado inmediato después de eliminación
                if localS:
                    try:
                        safe_set_item(localS, "fantasy_plantilla", json.dumps(st.session_state.plantilla_bloques))
                        st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
                        st.toast("Jugador eliminado y cambios guardados", icon="✅")
                    except Exception as e:
                        st.error(f"⚠️ Error al guardar después de eliminar: {str(e)}", icon="🚨")
                else:
                    st.toast("Jugador eliminado", icon="✅")
                
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

def emergency_data_recovery(localS):
    """
    Función de recuperación de emergencia para dispositivos Android
    que han perdido datos por problemas con localStorage.
    """
    recovery_sources = []
    
    # 1. Revisar fallback en session state
    if hasattr(st.session_state, 'fantasy_plantilla_fallback'):
        try:
            fallback_data = json.loads(st.session_state.fantasy_plantilla_fallback)
            if fallback_data:
                recovery_sources.append(("Session State Fallback", fallback_data))
        except:
            pass
    
    # 2. Revisar emergency backup
    if hasattr(st.session_state, 'emergency_plantilla'):
        if st.session_state.emergency_plantilla:
            recovery_sources.append(("Emergency Backup", st.session_state.emergency_plantilla))
    
    # 3. Intentar recuperar localStorage directamente
    try:
        direct_data = localS.getItem("fantasy_plantilla")
        if direct_data:
            direct_parsed = json.loads(direct_data)
            if direct_parsed:
                recovery_sources.append(("Direct localStorage", direct_parsed))
    except:
        pass
    
    # Si hay fuentes de recuperación, mostrar opciones al usuario
    if recovery_sources:
        st.warning("🔧 **Detectamos pérdida de datos. Se encontraron las siguientes fuentes de recuperación:**", icon="🛠️")
        
        for i, (source_name, data) in enumerate(recovery_sources):
            if st.button(f"Recuperar desde {source_name} ({len(data)} jugadores)", key=f"recover_{i}"):
                st.session_state.plantilla_bloques = data.copy()
                st.session_state.previous_plantilla = data.copy()
                st.session_state.initialized = True
                
                # Guardar inmediatamente
                safe_set_item(localS, "fantasy_plantilla", json.dumps(data))
                
                st.success(f"✅ ¡Recuperación exitosa desde {source_name}!", icon="🎉")
                st.rerun()
        
        st.info("💡 Si ninguna opción funciona, por favor introduce tu plantilla manualmente.")
        return True
    
    return False