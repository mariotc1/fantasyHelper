# ⚽ Fantasy XI Assistant

![Streamlit](https://img.shields.io/badge/Hecho_con-Streamlit-red?style=for-the-badge&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge)

Una aplicación web creada con Streamlit que te ayuda a calcular tu alineación ideal para juegos de fútbol fantasy, utilizando datos de probabilidad de titularidad obtenidos mediante scraping en tiempo real.

---

### 🚀 [**>> ACCEDE A LA APLICACIÓN EN VIVO AQUÍ <<**](https://xi-fantasy.streamlit.app/) 🚀

---

## ✨ Características Principales

*   **📊 Datos en Tiempo Real:** Obtiene las probabilidades de titularidad de los jugadores de LaLiga mediante web scraping al momento.
*   **✍️ Entrada de Plantilla Flexible:** Introduce tu equipo de tres formas distintas:
    *   Uno a uno con autocompletado.
    *   Pegando una lista desde el portapapeles.
    *   Subiendo un archivo CSV o Excel.
*   **🧠 Motor de Cálculo Inteligente:** Selecciona el mejor XI posible basándose en las probabilidades y en la formación táctica que definas.
*   **🏟️ Visualización Espectacular:** Muestra la alineación recomendada en un campo de fútbol visualmente atractivo.
*   **⚙️ Totalmente Configurable:** Ajusta los mínimos y máximos por posición (DEF, CEN, DEL) y la sensibilidad del buscador de nombres.
*   **📄 Exportación a PDF:** Descarga tu XI ideal en un documento PDF limpio y listo para compartir.

## 🛠️ Tecnologías Utilizadas

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **Scraping:** [Requests](https://requests.readthedocs.io/en/latest/) y [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
*   **Análisis de Datos:** [Pandas](https://pandas.pydata.org/)
*   **Exportación a PDF:** [FPDF2](https://github.com/py-pdf/fpdf2/)

## 🔧 Cómo Ejecutarlo en Local

Si quieres ejecutar este proyecto en tu propia máquina, sigue estos pasos:

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/mariotc1/fantasyHelper.git
    cd fantasyHelper
    ```

2.  **Crea y activa un entorno virtual** (recomendado):
    ```bash
    # Para Mac/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecuta la aplicación:**
    ```bash
    streamlit run fantasy_auto.py
    ```

La aplicación se abrirá automáticamente en tu navegador!
