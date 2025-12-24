# LIBRERIAS EXTERNAS (time y requests para scraping, pandas para manejo de datos, streamlit para UI, BeautifulSoup para parseo HTML)
import time, re, requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

# LIBRERIAS INTERNAS
from .data_utils import limpiar_porcentaje

# URLs de los equipos de LaLiga en FutbolFantasy
EQUIPOS_URLS = {
    "Alavés": "https://www.futbolfantasy.com/laliga/equipos/alaves",
    "Athletic Club": "https://www.futbolfantasy.com/laliga/equipos/athletic",
    "Atlético de Madrid": "https://www.futbolfantasy.com/laliga/equipos/atletico",
    "Barcelona": "https://www.futbolfantasy.com/laliga/equipos/barcelona",
    "Betis": "https://www.futbolfantasy.com/laliga/equipos/betis",
    "Celta": "https://www.futbolfantasy.com/laliga/equipos/celta",
    "Elche": "https://www.futbolfantasy.com/laliga/equipos/elche",
    "Espanyol": "https://www.futbolfantasy.com/laliga/equipos/espanyol",
    "Getafe": "https://www.futbolfantasy.com/laliga/equipos/getafe",
    "Girona": "https://www.futbolfantasy.com/laliga/equipos/girona",
    "Levante": "https://www.futbolfantasy.com/laliga/equipos/levante",
    "Mallorca": "https://www.futbolfantasy.com/laliga/equipos/mallorca",
    "Osasuna": "https://www.futbolfantasy.com/laliga/equipos/osasuna",
    "Rayo Vallecano": "https://www.futbolfantasy.com/laliga/equipos/rayo-vallecano",
    "Real Madrid": "https://www.futbolfantasy.com/laliga/equipos/real-madrid",
    "Real Oviedo": "https://www.futbolfantasy.com/laliga/equipos/real-oviedo",
    "Real Sociedad": "https://www.futbolfantasy.com/laliga/equipos/real-sociedad",
    "Sevilla": "https://www.futbolfantasy.com/laliga/equipos/sevilla",
    "Valencia": "https://www.futbolfantasy.com/laliga/equipos/valencia",
    "Villarreal": "https://www.futbolfantasy.com/laliga/equipos/villarreal"
}

# Cabecera de la petición HTTP
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"}

# Función de scraping con caché de Streamlit
@st.cache_data(ttl=15*60, show_spinner="Cargando datos de jugadores de LaLiga (puede tardar unos segundos)...")
# Realiza scraping de los datos de probabilidad de los jugadores de todos los equipos de LaLiga
def scrape_laliga():
    all_rows = []
    for equipo, url in EQUIPOS_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            candidates = soup.select(".jugador, .player, .player-card, .lista-jugadores .row, .media")
            
            for node in candidates:
                nombre, prob, imagen_url, perfil_url = None, None, None, None
                # Búsqueda robusta del nombre
                for sel in [".nombre", ".name", ".player-name", ".media-body strong", "strong"]:
                    tag = node.select_one(sel)
                    if tag and tag.get_text(strip=True):
                        nombre = tag.get_text(strip=True)
                        break

                if not nombre:
                    txt = node.get_text(" ", strip=True)
                    if txt and len(txt.split()) <= 6:
                        nombre = txt.split(" Prob")[0].strip()

                # Búsqueda robusta de la probabilidad
                for sel in [".probabilidad", ".prob", ".badge", ".player-prob", ".label"]:
                    tag = node.select_one(sel)
                    if tag and "%" in tag.get_text():
                        prob = tag.get_text(strip=True)
                        break

                if not prob:
                    m = re.search(r"(\d{1,3}\s?%)", node.get_text(" ", strip=True))
                    if m: prob = m.group(1)

                # Búsqueda de imagen y perfil
                img_tag = node.select_one("img[data-src]")
                if img_tag:
                    imagen_url = img_tag.get("data-src")

                a_tag = node.select_one("a[href*='/jugadores/']")
                if a_tag:
                    perfil_url = a_tag.get("href")

                # Añadir si se encontraron ambos datos y son válidos
                if nombre and prob:
                    if "JugadorJugadorJugador" in nombre or "Prob.Prob" in prob: continue
                    all_rows.append({
                        "Equipo": equipo, 
                        "Nombre": nombre, 
                        "Probabilidad": prob,
                        "Imagen_URL": imagen_url,
                        "Perfil_URL": perfil_url
                    })
            
            time.sleep(0.2) # Pequeña pausa para no saturar el servidor
        
        except requests.exceptions.RequestException as e:
            st.toast(f"Error al cargar datos de {equipo}: {e}", icon="⚠️")
            continue
    
    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows).drop_duplicates()
    df["Probabilidad_num"] = df["Probabilidad"].apply(limpiar_porcentaje)
    df = df.dropna(subset=["Probabilidad_num"])
    
    df = df.drop_duplicates(subset=['Nombre', 'Equipo']).sort_values("Probabilidad_num", ascending=False)
    return df.reset_index(drop=True)