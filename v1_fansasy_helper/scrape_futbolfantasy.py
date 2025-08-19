import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0 Safari/537.36"
}

# Lista de equipos de LaLiga y sus URLs en FutbolFantasy
equipos_urls = {
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

def scrape_equipo(nombre_equipo, url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[ERROR] No se pudo acceder a {nombre_equipo} ({url})")
        return []

    soup = BeautifulSoup(response.text, "lxml")
    jugadores_data = []

    jugadores = soup.select(".jugador")  # Selector general de jugador

    for j in jugadores:
        nombre_tag = j.select_one(".nombre")
        prob_tag = j.select_one(".probabilidad")

        nombre = nombre_tag.get_text(strip=True) if nombre_tag else None
        prob = prob_tag.get_text(strip=True) if prob_tag else None

        # Filtramos líneas basura
        if not nombre or not prob:
            continue
        if "JugadorJugadorJugador" in nombre or "Prob.Prob.Prob." in prob:
            continue

        jugadores_data.append({
            "Equipo": nombre_equipo,
            "Nombre": nombre,
            "Probabilidad": prob
        })

    return jugadores_data

if __name__ == "__main__":
    all_data = []
    for equipo, url in equipos_urls.items():
        print(f"[SCRAPING] {equipo}...")
        datos = scrape_equipo(equipo, url)
        all_data.extend(datos)
        time.sleep(1)

    # Guardar todo en CSV
    df = pd.DataFrame(all_data)
    df.to_csv("data_laliga.csv", index=False, encoding="utf-8")
    print(f"[OK] Datos guardados en data_laliga.csv con {len(df)} registros")