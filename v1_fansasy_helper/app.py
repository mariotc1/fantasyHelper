import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from v1_fansasy_helper.motor_decision import seleccionar_mejor_xi

# Configuración de la página
st.set_page_config(page_title="Fantasy XI Assistant", layout="wide")

st.title("Fantasy XI Assistant")
st.markdown("Tu mejor alineación basada en probabilidades y posiciones.")

# Cargar datos
df = pd.read_csv("mi_plantilla_filtrada.csv")
df["Probabilidad_num"] = df["Probabilidad"].str.replace("%", "").astype(float)

# Ejecutar motor
mejor_xi = seleccionar_mejor_xi(df)
df_xi = pd.DataFrame(mejor_xi)

# Mostrar XI titular
st.subheader("Mejor XI recomendado")
st.dataframe(df_xi[["Posicion", "Mi_nombre", "Equipo", "Probabilidad"]]
             .style.applymap(lambda v: "background-color: #90ee90" if isinstance(v, str) and "%" in v and int(v.strip("%")) >= 80 
                              else "background-color: #ffcccb" if isinstance(v, str) and "%" in v and int(v.strip("%")) < 50 
                              else ""))

# Banquillo recomendado
st.subheader("Banquillo recomendado")
banca = df[~df["Mi_nombre"].isin(df_xi["Mi_nombre"])]
st.dataframe(banca[["Posicion", "Mi_nombre", "Equipo", "Probabilidad"]])

# Exportar a PDF
from fpdf import FPDF
def exportar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, "Mejor XI Recomendado", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    for _, row in df_xi.iterrows():
        pdf.cell(200, 8, f"{row['Posicion']} - {row['Mi_nombre']} ({row['Equipo']}) - {row['Probabilidad']}", ln=True)
    pdf.output("mejor_xi.pdf")

if st.button("Exportar XI a PDF"):
    exportar_pdf()
    st.success("PDF generado: mejor_xi.pdf")