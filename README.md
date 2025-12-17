# ⚽ Fantasy XI Assistant v3
*Asistente inteligente para optimizar tu alineación de fútbol fantasy*

![Streamlit](https://img.shields.io/badge/Hecho_con-Streamlit-red?style=for-the-badge&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge)

Una aplicación web creada con Streamlit que te ayuda a calcular tu alineación ideal para juegos de fútbol fantasy (como Biwenger, LaLiga Fantasy, etc.), utilizando datos de probabilidad de titularidad obtenidos mediante scraping en tiempo real.

Esta versión (v3) ha sido refactorizada para tener una estructura de código modular, limpia y escalable.

---

### 🚀 [**>> ACCEDE A LA APLICACIÓN AQUÍ <<**](https://xi-fantasy.streamlit.app/) 🚀

---

## ✨ Características Principales

*   **📊 Datos en Tiempo Real:** Obtiene las probabilidades de titularidad de los jugadores de LaLiga mediante web scraping al momento.
*   **✍️ Entrada de Plantilla Flexible:** Introduce tu equipo de tres formas distintas:
    *   Uno a uno con autocompletado y guardado en local.
    *   Pegando una lista desde el portapapeles.
    *   Subiendo un archivo CSV o Excel.
*   **🧠 Motor de Cálculo Inteligente:** Selecciona el mejor XI posible basándose en las probabilidades y en la formación táctica que definas.
*   **🏟️ Visualización Espectacular:** Muestra la alineación recomendada en un campo de fútbol visualmente atractivo y moderno.
*   **⚙️ Totalmente Configurable:** Ajusta los mínimos y máximos por posición (DEF, CEN, DEL) y la sensibilidad del buscador de nombres.
*   **📄 Exportación a PDF:** Descarga tu XI ideal en un documento PDF limpio y listo para compartir.

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
    El punto de entrada principal de la aplicación se encuentra en la carpeta `v3_fantasy_helper`.
    ```bash
    streamlit run v3_fantasy_helper/fantasy_auto2.py.py
    ```

La aplicación se abrirá automáticamente en tu navegador.

## 🏗️ Estructura del Proyecto (v3)

La versión 3 se ha reestructurado para mejorar la mantenibilidad y claridad del código. La lógica principal reside en `v3_fantasy_helper/` y sigue esta organización:

```
v3_fantasy_helper/
├── fantasy_auto2.py.py         # Script principal, maneja la UI de Streamlit
└── src/                        # Directorio con la lógica de negocio
    ├── __init__.py
    ├── core.py                 # Algoritmos de matching y selección del XI
    ├── data_utils.py           # Funciones de limpieza y parseo de datos
    ├── scraper.py              # Lógica de web scraping
    └── output_generators.py    # Generadores de PDF y HTML
```

## 🛠️ Tecnologías Utilizadas

*   **Frontend:** [Streamlit](https://streamlit.io/)
*   **Scraping:** [Requests](https://requests.readthedocs.io/en/latest/) y [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
*   **Análisis de Datos:** [Pandas](https://pandas.pydata.org/)
*   **Exportación a PDF:** [fpdf2](https://github.com/py-pdf/fpdf2)
*   **Persistencia en Navegador:** [streamlit-local-storage](https://pypi.org/project/streamlit-local-storage/)
