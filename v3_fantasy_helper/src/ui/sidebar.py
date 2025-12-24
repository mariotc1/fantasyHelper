# LIBRERIAS EXTERNAS (streamlit para UI)
import streamlit as st

def render_sidebar(df_laliga):
    """
    Renderiza la barra lateral de configuración y devuelve los parámetros
    seleccionados por el usuario.
    """
    with st.sidebar:
        st.image("https://play-lh.googleusercontent.com/xx7OVI90d-d6pvQlqmAAeUo4SzvLsrp9uss8XPO1ZwILEeTCpjYFVRuL550bUqlicy0=w240-h480-rw", width=80)
        st.header("Configuración del XI")

        # Parámetros de matching
        st.subheader("Sensibilidad")
        cutoff = st.slider("Matching de nombres", 0.3, 1.0, 0.6, 0.05, 
                           help="Un valor más bajo puede encontrar más coincidencias si los nombres no son exactos, pero puede cometer errores.")

        # Parámetros tácticos
        st.subheader("Táctica (Formación)")

        c1, c2 = st.columns(2)
        min_def = c1.number_input("Mín. DEF", 2, 5, 3)
        max_def = c2.number_input("Máx. DEF", 3, 6, 5)
        min_cen = c1.number_input("Mín. CEN", 2, 5, 3)
        max_cen = c2.number_input("Máx. CEN", 3, 6, 5)
        min_del = c1.number_input("Mín. DEL", 1, 4, 1)
        max_del = c2.number_input("Máx. DEL", 1, 4, 3)
        
        # Validaciones básicas
        if min_def > max_def: st.warning("Mín. DEF no puede ser mayor que Máx. DEF.")
        if min_cen > max_cen: st.warning("Mín. CEN no puede ser mayor que Máx. CEN.")
        if min_del > max_del: st.warning("Mín. DEL no puede ser mayor que Máx. DEL.")
        if (min_def + min_cen + min_del + 1) > 11: st.error("La suma de mínimos es > 11. Formación imposible.")

        # Parámetros fijos
        st.subheader("Ajustes Fijos")
        c1, c2 = st.columns(2)
        c1.number_input("Nº POR", 1, 1, 1, disabled=True) 
        c2.number_input("Total en XI", 11, 11, 11, disabled=True)
        num_por, total = 1, 11

        with st.expander("Ver todos los datos de LaLiga"):
            st.caption(f"Datos cargados: {len(df_laliga)} registros únicos.")
            st.dataframe(df_laliga, use_container_width=True)
            
    return cutoff, min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total