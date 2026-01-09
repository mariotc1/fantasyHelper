# LIBRERIAS EXTERNAS (streamlit para UI, json para manejo de datos, time para pausas)
import streamlit as st
import json
import time
import logging
import traceback
from datetime import datetime

# FUNCIONES INTERNAS
def log_debug_info(message, data=None):
    """
    Función de logging para diagnóstico en tiempo real
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    device_info = f"Device: {st.session_state.get('device_info', 'Unknown')}"
    
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "device_info": device_info,
        "data": data
    }
    
    # Guardar en session state para diagnóstico
    if "debug_log" not in st.session_state:
        st.session_state.debug_log = []
    
    st.session_state.debug_log.append(log_entry)
    
    # Mantener solo los últimos 50 eventos
    if len(st.session_state.debug_log) > 50:
        st.session_state.debug_log = st.session_state.debug_log[-50:]
    
    # Mostrar en consola del navegador si estamos en modo debug
    if st.session_state.get("debug_mode", False):
        st.info(f"🔍 DEBUG [{timestamp}] {message}")
        if data:
            st.json(data)

def detect_device_info():
    """
    Detecta información del dispositivo para diagnóstico
    """
    if "device_info" not in st.session_state:
        # Intentar detectar el tipo de dispositivo
        user_agent = st.session_state.get("user_agent", "Unknown")
        
        if "Android" in user_agent:
            st.session_state.device_info = "Android Mobile"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            st.session_state.device_info = "iOS Device"
        elif "Mac" in user_agent:
            st.session_state.device_info = "Mac Desktop"
        elif "Windows" in user_agent:
            st.session_state.device_info = "Windows Desktop"
        else:
            st.session_state.device_info = "Unknown Device"
    
    return st.session_state.device_info

def is_android_device():
    """
    Verifica si el dispositivo actual es Android para aplicar soluciones específicas
    """
    device_info = detect_device_info()
    return device_info == "Android Mobile"

def android_safe_storage_get(key, fallback=None):
    """
    Función específica para Android que prioriza session state sobre localStorage
    """
    # En Android, priorizar siempre session state como fallback principal
    if hasattr(st.session_state, f'{key}_fallback'):
        log_debug_info(f"Android: usando session state fallback para {key}")
        return st.session_state[f'{key}_fallback']
    
    # Si no hay fallback, intentar localStorage
    try:
        value = st.session_state.get(f'local_storage_{key}', fallback)
        log_debug_info(f"Android: usando localStorage emulado para {key}")
        return value
    except:
        log_debug_info(f"Android: sin datos para {key}, usando fallback")
        return fallback

def android_safe_storage_set(key, value):
    """
    Función específica para Android que guarda en múltiples lugares
    """
    try:
        # Guardar en session state
        st.session_state[f'{key}_fallback'] = value
        st.session_state[f'local_storage_{key}'] = value
        
        log_debug_info(f"Android: guardado en session state para {key}")
        return True
    except Exception as e:
        log_debug_info(f"Android: error en guardado", {"key": key, "error": str(e)})
        return False

def safe_get_item(localS, key, fallback=None):
    """
    Obtiene un elemento de localStorage de forma segura con manejo de errores
    y fallback para dispositivos Android.
    """
    device_info = detect_device_info()
    log_debug_info(f"Intentando obtener {key} desde localStorage", {"device": device_info})
    
    # Si es Android, usar el método específico para Android
    if is_android_device():
        return android_safe_storage_get(key, fallback)
    
    try:
        # Intentar obtener el valor normalmente
        value = localS.getItem(key)
        log_debug_info(f"localStorage.getItem() resultado", {"key": key, "value": value, "length": len(value) if value else 0})
        
        if value is not None:
            return value
        
        # Fallback para dispositivos Android: intentar con session storage
        if hasattr(st.session_state, f'{key}_fallback'):
            fallback_value = st.session_state[f'{key}_fallback']
            log_debug_info(f"Usando fallback desde session state", {"key": key, "fallback_value": fallback_value})
            return fallback_value
            
        log_debug_info(f"No se encontró {key}, usando fallback None")
        return fallback
    except Exception as e:
        # Registrar error y usar fallback
        error_msg = f"Error al obtener {key} de localStorage: {str(e)}"
        log_debug_info(error_msg, {"error": str(e), "traceback": traceback.format_exc()})
        
        if hasattr(st.session_state, f'{key}_fallback'):
            fallback_value = st.session_state[f'{key}_fallback']
            log_debug_info(f"Usando fallback después de error", {"key": key, "fallback_value": fallback_value})
            return fallback_value
        
        return fallback

def safe_set_item(localS, key, value):
    """
    Guarda un elemento en localStorage de forma segura con manejo de errores
    y fallback para dispositivos Android.
    """
    device_info = detect_device_info()
    log_debug_info(f"Intentando guardar {key} en localStorage", {"device": device_info, "value_length": len(value) if value else 0})
    
    # Si es Android, usar el método específico para Android
    if is_android_device():
        return android_safe_storage_set(key, value)
    
    try:
        # Intentar guardar en localStorage
        localS.setItem(key, value)
        log_debug_info(f"localStorage.setItem() exitoso", {"key": key, "value_saved": True})
        
        # También guardar en session state como fallback
        st.session_state[f'{key}_fallback'] = value
        log_debug_info(f"Guardado también en fallback", {"key": key})
        
        return True
    except Exception as e:
        # Registrar error y usar solo fallback
        error_msg = f"Error al guardar {key} en localStorage: {str(e)}"
        log_debug_info(error_msg, {"error": str(e), "traceback": traceback.format_exc()})
        
        st.session_state[f'{key}_fallback'] = value
        log_debug_info(f"Guardado solo en fallback debido a error", {"key": key})
        
        return False

def initialize_session_state(localS):
    """
    Carga la plantilla desde localStorage si no está en el estado de la sesión,
    y también inicializa el estado de seguimiento de cambios.
    """
    log_debug_info("=== INICIALIZANDO SESIÓN ===")
    
    if "plantilla_bloques" not in st.session_state:
        plantilla_guardada_str = safe_get_item(localS, "fantasy_plantilla")
        log_debug_info("Cargando plantilla desde localStorage", {"raw_string": plantilla_guardada_str})
        
        try:
            st.session_state.plantilla_bloques = json.loads(plantilla_guardada_str) if plantilla_guardada_str else []
            log_debug_info("Parseo JSON exitoso", {"players_count": len(st.session_state.plantilla_bloques)})
        except (json.JSONDecodeError, TypeError) as e:
            error_msg = f"Error parseando JSON: {str(e)}"
            log_debug_info(error_msg, {"raw_data": plantilla_guardada_str})
            st.error("⚠️ No se pudo cargar tu plantilla guardada porque los datos estaban corruptos. Empezando con una plantilla vacía.", icon="🚨")
            st.session_state.plantilla_bloques = []

        
        pos_order = {"POR": 0, "DEF": 1, "CEN": 2, "DEL": 3}
        st.session_state.plantilla_bloques.sort(key=lambda p: pos_order.get(p.get("Posicion"), 99))
        log_debug_info("Plantilla ordenada por posición", {"final_count": len(st.session_state.plantilla_bloques)})

        if plantilla_guardada_str:
            st.toast("¡Hemos cargado tu plantilla guardada!", icon="👍")
            log_debug_info("Toast de carga mostrada al usuario")
    else:
        log_debug_info("Plantilla ya existía en session_state", {"count": len(st.session_state.plantilla_bloques)})
    
    if "previous_plantilla" not in st.session_state:
        st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
        log_debug_info("previous_plantilla inicializado", {"count": len(st.session_state.previous_plantilla)})
    
    # Inicializar bandera para evitar guardados automáticos prematuros
    if "initialized" not in st.session_state:
        st.session_state.initialized = False
        log_debug_info("Bandera initialized establecida a False")
    
    log_debug_info("=== INICIALIZACIÓN COMPLETADA ===")


def autosave_plantilla(localS):
    """
    Compara la plantilla actual con la guardada previamente y, si hay cambios,
    la guarda en localStorage y actualiza el estado.
    """
    log_debug_info("=== INICIANDO AUTOSAVE ===")
    
    # Evitar guardados automáticos prematuros antes de la inicialización completa
    if not st.session_state.get("initialized", False):
        log_debug_info("No inicializado, estableciendo flag y saliendo")
        st.session_state.initialized = True
        return
    
    current_count = len(st.session_state.plantilla_bloques)
    previous_count = len(st.session_state.previous_plantilla)
    log_debug_info("Comparando plantillas", {"current": current_count, "previous": previous_count})
    
    # Solo proceder si hay datos válidos en la plantilla actual
    if not st.session_state.plantilla_bloques:
        log_debug_info("Plantilla vacía, no guardando")
        return
    
    current_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.plantilla_bloques], key=lambda x: x['Nombre'])
    previous_norm = sorted([{'Nombre': p['Nombre'], 'Posicion': p['Posicion']} for p in st.session_state.previous_plantilla], key=lambda x: x['Nombre'])
    
    has_changes = current_norm != previous_norm
    log_debug_info("Comparación de cambios", {"has_changes": has_changes, "current_normalized": current_norm, "previous_normalized": previous_norm})

    if has_changes:
        try:
            with st.spinner("Guardando..."):
                log_debug_info("Iniciando proceso de guardado")
                
                # Validación adicional antes de guardar
                is_valid = st.session_state.plantilla_bloques and all(p.get('Nombre') and p.get('Posicion') for p in st.session_state.plantilla_bloques)
                log_debug_info("Validación de datos", {"is_valid": is_valid, "plantilla": st.session_state.plantilla_bloques})
                
                if is_valid:
                    json_data = json.dumps(st.session_state.plantilla_bloques)
                    log_debug_info("JSON generado para guardar", {"length": len(json_data), "preview": json_data[:200]})
                    
                    success = safe_set_item(localS, "fantasy_plantilla", json_data)
                    st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
                    
                    log_debug_info("Resultado del guardado", {"success": success})
                    
                    if success:
                        st.toast("Cambios guardados automáticamente!", icon="💾")
                    else:
                        st.toast("Cambios guardados en modo seguro (dispositivo Android)", icon="📱")
                    
                    time.sleep(0.5)
                    log_debug_info("Ejecutando st.rerun()")
                    st.rerun()
                else:
                    log_debug_info("Datos inválidos, no guardando", {"plantilla": st.session_state.plantilla_bloques})
                    st.error("⚠️ No se pueden guardar datos inválidos", icon="🚨")
        except Exception as e:
            error_msg = f"Error crítico al guardar: {str(e)}"
            log_debug_info(error_msg, {"error": str(e), "traceback": traceback.format_exc()})
            st.error(error_msg, icon="🚨")
            # Intentar guardado de emergencia en session state
            st.session_state.emergency_plantilla = st.session_state.plantilla_bloques.copy()
            log_debug_info("Guardado de emergencia realizado")
    else:
        log_debug_info("No hay cambios, no guardando")
    
    log_debug_info("=== AUTOSAVE COMPLETADO ===")

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
    log_debug_info("=== INICIANDO RECUPERACIÓN DE EMERGENCIA ===")
    recovery_sources = []
    
    # 1. Revisar fallback en session state
    if hasattr(st.session_state, 'fantasy_plantilla_fallback'):
        try:
            fallback_data = json.loads(st.session_state.fantasy_plantilla_fallback)
            if fallback_data:
                recovery_sources.append(("Session State Fallback", fallback_data))
                log_debug_info("Fallback encontrado", {"count": len(fallback_data)})
        except Exception as e:
            log_debug_info("Error parseando fallback", {"error": str(e)})
    
    # 2. Revisar emergency backup
    if hasattr(st.session_state, 'emergency_plantilla'):
        if st.session_state.emergency_plantilla:
            recovery_sources.append(("Emergency Backup", st.session_state.emergency_plantilla))
            log_debug_info("Emergency backup encontrado", {"count": len(st.session_state.emergency_plantilla)})
    
    # 3. Intentar recuperar localStorage directamente
    try:
        direct_data = localS.getItem("fantasy_plantilla")
        if direct_data:
            direct_parsed = json.loads(direct_data)
            if direct_parsed:
                recovery_sources.append(("Direct localStorage", direct_parsed))
                log_debug_info("Datos directos de localStorage encontrados", {"count": len(direct_parsed)})
    except Exception as e:
        log_debug_info("Error leyendo localStorage directamente", {"error": str(e)})
    
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
                log_debug_info("Recuperación exitosa", {"source": source_name, "count": len(data)})
                st.rerun()
        
        st.info("💡 Si ninguna opción funciona, por favor introduce tu plantilla manualmente.")
        return True
    else:
        log_debug_info("No se encontraron fuentes de recuperación")
    
    return False

def force_manual_save(localS):
    """
    Función de guardado manual forzado para pruebas y diagnóstico
    """
    log_debug_info("=== GUARDADO MANUAL FORZADO ===")
    
    if st.session_state.plantilla_bloques:
        try:
            json_data = json.dumps(st.session_state.plantilla_bloques)
            success = safe_set_item(localS, "fantasy_plantilla", json_data)
            st.session_state.previous_plantilla = st.session_state.plantilla_bloques.copy()
            
            if success:
                st.success("✅ Guardado manual forzado exitoso", icon="💾")
            else:
                st.warning("⚠️ Guardado manual forzado con fallback", icon="📱")
            
            log_debug_info("Guardado manual completado", {"success": success, "players": len(st.session_state.plantilla_bloques)})
        except Exception as e:
            st.error(f"❌ Error en guardado manual: {str(e)}", icon="🚨")
            log_debug_info("Error en guardado manual", {"error": str(e), "traceback": traceback.format_exc()})
    else:
        st.info("No hay jugadores para guardar")
        log_debug_info("Intento de guardado manual con plantilla vacía")