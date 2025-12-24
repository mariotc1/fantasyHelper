# ⚽ Fantasy XI Assistant
_Tu Asistente Inteligente para una Alineación de Fantasy Imbatible_

<div>

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Hecho_con-Streamlit-red?style=for-the-badge&logo=streamlit)
![Open Source](https://img.shields.io/badge/Open_Source-❤️-purple?style=for-the-badge)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge)

</div>

---

<div align="center">

**Una aplicación web que lleva tu equipo de fútbol fantasy al siguiente nivel.**
Calcula tu alineación ideal basándose en probabilidades de titularidad en tiempo real, ayudándote a tomar decisiones basadas en datos, no solo en intuición.

### 🚀 [**>> PRUEBA LA APLICACIÓN EN VIVO AQUÍ <<**](https://xi-fantasy.streamlit.app/) 🚀

</div>

    
<p align="center">
    <img src="demo.gif" alt="Demostración de Fantasy XI Assistant" width="750"/>
</p>

## 🌟 Sobre el Proyecto

¿Cansado de dudar hasta el último minuto sobre a quién alinear en tu equipo de Biwenger, LaLiga Fantasy o cualquier otro juego similar? **Fantasy XI Assistant** es la herramienta definitiva que elimina las conjeturas. 

La aplicación realiza web scraping sobre [FutbolFantasy](https://www.futbolfantasy.com/), una de las fuentes más fiables, para obtener las probabilidades de que cada jugador de LaLiga sea titular en la próxima jornada. Con esos datos, y según tus preferencias tácticas, un motor de optimización calcula el mejor once inicial posible que puedes presentar con los jugadores de tu plantilla.

## ✨ Características Principales

*   **📊 Datos Frescos, Decisiones Inteligentes:** Obtiene las probabilidades de titularidad más recientes para que tus decisiones siempre se basen en la información más actual.
*   **✍️ Múltiples Formas de Añadir tu Plantilla:**
    *   **Uno a uno:** Con autocompletado y guardado automático en tu navegador.
    *   **Pegado Rápido:** Copia y pega tu plantilla directamente.
    *   **Subida de Archivos:** Compatible con ficheros `.csv` y `.xlsx`.
*   **🧠 Motor de Optimización Táctica:**
    *   Define tu sistema de juego (mínimos y máximos de defensas, centrocampistas y delanteros).
    *   El algoritmo selecciona el 11 titular que maximiza la probabilidad total de jugar.
*   **🏟️ Visualización Profesional:** Olvídate de aburridas listas. Tu alineación se presenta en un espectacular campo de fútbol interactivo en 3D.
*   **🔗 Comparte tu Éxito:** Descarga tu alineación en un **PDF** limpio o compártela directamente en **Twitter (X)** y **WhatsApp**.
*   **🤖 Matching Inteligente de Nombres:** ¿Has escrito mal un nombre? No pasa nada. El sistema es capaz de encontrar la coincidencia más probable.

## 🛠️ Stack Tecnológico

Este proyecto ha sido construido con un conjunto de herramientas modernas y eficientes de Python:

*   **Framework Web:** [Streamlit](https://streamlit.io/)
*   **Análisis y Manipulación de Datos:** [Pandas](https://pandas.pydata.org/)
*   **Web Scraping:** [Requests](https://requests.readthedocs.io/en/latest/) & [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
*   **Generación de PDF:** [fpdf2](https://github.com/py-pdf/fpdf2)
*   **Persistencia en Navegador:** [streamlit-local-storage](https://pypi.org/project/streamlit-local-storage/)

## 🚀 Puesta en Marcha Local

Sigue estos pasos para ejecutar el proyecto en tu propia máquina:

1.  **Clona el Repositorio**
    ```bash
    git clone https://github.com/mariotc1/fantasyHelper.git
    cd fantasyHelper
    ```

2.  **Crea y Activa un Entorno Virtual** (Recomendado)
    ```bash
    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instala las Dependencias**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecuta la Aplicación**
    Navega hasta la carpeta raíz del proyecto y ejecuta el siguiente comando:
    ```bash
    streamlit run v3_fantasy_helper/fantasy_auto2.py
    ```
    ¡La aplicación se abrirá automáticamente en tu navegador!

## 🏗️ Arquitectura del Proyecto

Esta aplicación sigue una arquitectura limpia y modular para facilitar su mantenimiento y escalabilidad. La lógica de negocio está completamente separada de la capa de presentación (UI).

```
v3_fantasy_helper/
├── app.py                 # (fantasy_auto2.py) Punto de entrada y orquestador de la app.
├── assets/                # Ficheros estáticos (CSS, scripts de analíticas).
│   ├── styles.css
│   └── google_analytics.html
└── src/
    ├── __init__.py
    ├── core.py            # Lógica de negocio principal (matching de nombres, selección del XI).
    ├── data_utils.py      # Utilidades para parsear y limpiar datos de entrada.
    ├── output_generators.py # Módulos para crear los artefactos de salida (PDF, HTML del campo).
    ├── scraper.py         # Lógica de web scraping para obtener datos de FutbolFantasy.
    ├── state_manager.py   # Gestiona el estado de la sesión y la persistencia en local storage.
    └── ui/                  # Módulos dedicados a construir los componentes de la UI.
        ├── __init__.py
        ├── sidebar.py
        ├── input_tabs.py
        └── results_tab.py
```
Esta estructura basada en la **Separación de Responsabilidades** asegura que cada parte del código tiene un único propósito, haciendo que el proyecto sea más robusto y fácil de extender con nuevas funcionalidades.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para nuevas características, mejoras en el código o has encontrado un bug, por favor, siéntete libre de:

1.  Hacer un **Fork** del proyecto.
2.  Crear una nueva **Branch** (`git checkout -b feature/AmazingFeature`).
3.  Hacer tus cambios y hacer **Commit** (`git commit -m 'Add some AmazingFeature'`).
4.  Hacer **Push** a la Branch (`git push origin feature/AmazingFeature`).
5.  Abrir una **Pull Request**.

También puedes abrir una `issue` con la etiqueta que corresponda.

## 📄 Licencia

Este proyecto está distribuido bajo la Licencia MIT. Consulta el fichero `LICENSE` para más información.

---

<div align="center">
    Creado con ❤️ por un aficionado al fantasy
</div>