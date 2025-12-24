# LIBRERIAS EXTERNAS (streamlit para UI, pandas para datos, base64 para codificación)
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64

# FUNCIONES INTERNAS
from src.core import emparejar_con_datos, seleccionar_mejor_xi, buscar_nombre_mas_cercano
from src.output_generators import generar_pdf_xi, generar_html_alineacion_completa

# FUNCIONES PRINCIPALES DE RENDERIZADO DE LA PESTAÑA DE RESULTADOS
def render_results_tab(df_plantilla, df_laliga, cutoff, tactica):
    """
    Renderiza la pestaña "Tu XI Ideal y Banquillo".
    """
    min_def, max_def, min_cen, max_cen, min_del, max_del, num_por, total = tactica

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
            pdf_bytes = generar_pdf_xi(df_xi)
            pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        url_app = "https://xi-fantasy.streamlit.app/"
        texto_twitter = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 ¿Puedes superarlo? 😏 {url_app} #FantasyLaLiga #LALIGAFANTASY"
        texto_whatsapp = f"¡Este es mi XI ideal para la jornada, calculado con el Asistente Fantasy! 🔥 Échale un ojo: {url_app}"
        link_twitter = f"https://x.com/intent/tweet?text={texto_twitter.replace(' ', '%20')}"
        link_whatsapp = f"https://api.whatsapp.com/send?text={texto_whatsapp.replace(' ', '%20')}"

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

        if st.session_state.no_encontrados:
            with st.expander("⚠️ Algunos jugadores no fueron encontrados", expanded=True):
                st.warning("No se encontraron coincidencias para: " + ", ".join(sorted(set(st.session_state.no_encontrados))))
                sugerencias = [f"Para '{n}', ¿quizás quisiste decir **{sug}**?" for n in st.session_state.no_encontrados if (sug := buscar_nombre_mas_cercano(n, df_laliga['Nombre'], 0.5))]
                if sugerencias: st.info("💡 Sugerencias:\n- " + "\n- ".join(sugerencias))