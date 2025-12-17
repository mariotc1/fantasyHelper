from fpdf import FPDF
import pandas as pd

def generar_pdf_xi(df_xi: pd.DataFrame) -> bytes:
    """Genera un archivo PDF con la alineación del XI ideal."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", "B", size=18)
    pdf.cell(0, 12, "Fantasy XI - Tu Alineacion Ideal", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", size=12)
    
    for _, row in df_xi.iterrows():
        linea = f"{row['Posicion']} - {row['Mi_nombre']} ({row['Equipo']}) - Prob: {row['Probabilidad']}"
        pdf.multi_cell(0, 10, linea, border=1, align="L")
        pdf.ln(2)
    try:
        media = df_xi["Probabilidad_num"].mean()
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Media de probabilidad del XI: {media:.1f}%", ln=True, align="C")
    except Exception:
        pass
        
    return pdf.output(dest='S').encode('latin1')

def generar_html_campo(df_xi: pd.DataFrame) -> str:
    """Genera una visualización HTML de la alineación en un campo de fútbol con modal interactivo."""
    # 1. Organizar datos por posición
    posiciones = {"POR": [], "DEF": [], "CEN": [], "DEL": []}
    for _, jugador in df_xi.iterrows():
        pos = jugador.get("Posicion")
        if pos in posiciones:
            posiciones[pos].append(jugador)
    
    formacion_str = f"{len(posiciones['DEF'])}-{len(posiciones['CEN'])}-{len(posiciones['DEL'])}"

    # 2. Construir HTML de las líneas de jugadores
    lineas_html = ""
    for pos_key in ["DEL", "CEN", "DEF", "POR"]: # Orden visual del campo
        jugadores = posiciones[pos_key]
        num_jugadores = len(jugadores)
        justify = "space-around" if num_jugadores > 1 else "center"
        
        linea_html = f'<div class="line" style="justify-content: {justify};">'
        
        for jugador in jugadores:
            prob = jugador['Probabilidad_num']
            if prob >= 80: color_bg, color_txt, border_col = "#dcfce7", "#166534", "#22c55e" # Verde
            elif prob >= 60: color_bg, color_txt, border_col = "#fef9c3", "#854d0e", "#eab308" # Amarillo
            else: color_bg, color_txt, border_col = "#fee2e2", "#991b1b", "#ef4444" # Rojo

            nombre_display = jugador['Mi_nombre']
            if len(nombre_display) > 12:
                parts = nombre_display.split()
                if len(parts) > 1: nombre_display = f"{parts[0][0]}. {parts[-1]}"
                else: nombre_display = nombre_display[:10] + "."

            imagen_url = jugador.get('Imagen_URL', 'https://static.futbolfantasy.com/images/default-black.jpg')
            perfil_url = jugador.get('Perfil_URL', '#')

            card_html = f"""
            <div class="card-container">
                <div class="player-card" 
                     data-nombre="{jugador['Mi_nombre']}" 
                     data-equipo="{jugador['Equipo']}" 
                     data-posicion="{jugador['Posicion']}"
                     data-probabilidad="{int(prob)}"
                     data-imagen-url="{imagen_url}"
                     data-perfil-url="{perfil_url}">
                    <div class="card-header">
                        <span class="pos-pill">{jugador['Posicion']}</span>
                        <span class="prob-pill" style="background:{color_bg}; color:{color_txt};">{int(prob)}%</span>
                    </div>
                    <div class="player-image-small">
                        <img src="{imagen_url}" alt="{nombre_display}" onerror="this.onerror=null;this.src='https://static.futbolfantasy.com/images/default-black.jpg';">
                    </div>
                    <div class="card-body">
                        <div class="p-name">{nombre_display}</div>
                        <div class="p-team">{jugador['Equipo']}</div>
                    </div>
                    <div class="health-bar" style="background:{border_col}; width:{prob}%;"></div>
                </div>
            </div>
            """
            linea_html += card_html
        
        linea_html += "</div>"
        lineas_html += linea_html

    # 3. HTML completo con CSS y JS
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            :root {{ --grass-dark: #2f7a38; --grass-light: #3a8a44; --line-white: rgba(255,255,255,0.7); }}
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; background: transparent; display: flex; justify-content: center; overflow-x: hidden; }}
            .pitch-wrapper {{ width: 100%; max-width: 500px; aspect-ratio: 2/3.1; position: relative; margin: 0 auto; }}
            .pitch {{
                width: 100%; height: 100%;
                background-color: var(--grass-dark);
                background-image: repeating-linear-gradient(0deg, transparent, transparent 10%, rgba(0,0,0,0.05) 10%, rgba(0,0,0,0.05) 20%);
                border: 2px solid white; border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
                display: flex; flex-direction: column; position: relative; overflow: hidden;
            }}
            .line-half {{ position: absolute; top: 50%; width: 100%; height: 2px; background: var(--line-white); }}
            .circle-center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 20%; aspect-ratio: 1/1; border: 2px solid var(--line-white); border-radius: 50%; }}
            .area {{ position: absolute; left: 50%; transform: translateX(-50%); width: 40%; height: 6%; border: 2px solid var(--line-white); }}
            .area.top {{ top: 0; border-top: 0; }}
            .area.bot {{ bottom: 0; border-bottom: 0; }}
            .formation-badge {{
                position: absolute; top: 12px; right: 12px;
                background: rgba(0,0,0,0.6); color: white;
                padding: 4px 10px; border-radius: 20px;
                font-size: 12px; font-weight: 800; z-index: 5;
                backdrop-filter: blur(4px);
            }}
            .line {{ flex: 1; display: flex; align-items: center; width: 100%; padding: 0 4px; z-index: 2; }}
            .card-container {{ width: 19%; display: flex; justify-content: center; }}
            .player-card {{
                background: white; width: 100%; max-width: 85px;
                border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                overflow: hidden; display: flex; flex-direction: column;
                cursor: pointer; transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }}
            .player-card:hover {{ transform: scale(1.05); }}
            .player-card:active {{ transform: scale(0.95); }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 3px 4px; font-size: 9px; font-weight: 700; color: #555; }}
            .player-image-small {{ height: 50px; width: 100%; overflow: hidden; }}
            .player-image-small img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
            .card-body {{ text-align: center; padding: 2px 2px 6px 2px; flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }}
            .p-name {{ font-size: clamp(10px, 2.5vw, 12px); font-weight: 800; color: #1e293b; line-height: 1.1; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .p-team {{ font-size: 8px; color: #64748b; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .health-bar {{ height: 3px; align-self: flex-start; }}

            /* Modal Styles */
            .modal-overlay {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
                z-index: 100; display: flex; align-items: center; justify-content: center;
                opacity: 0; visibility: hidden; transition: opacity 0.3s ease, visibility 0.3s ease;
            }}
            .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
            .modal-card {{
                position: relative; width: 90%; max-width: 320px;
                aspect-ratio: 3/4.5;
                background: linear-gradient(135deg, #1e293b, #0f172a);
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.5);
                padding: 16px;
                color: white;
                transform: scale(0.9); opacity: 0;
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease;
            }}
            .modal-overlay.visible .modal-card {{ transform: scale(1); opacity: 1; }}
            .modal-close {{
                position: absolute; top: -10px; right: -10px;
                width: 30px; height: 30px; border-radius: 50%;
                background: white; color: #1e293b;
                border: none; cursor: pointer; font-size: 16px; font-weight: bold;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }}
            .modal-card-header {{ text-align: center; }}
            #modal-prob, #modal-pos {{ font-size: 24px; font-weight: 800; }}
            #modal-player-name {{ font-size: 28px; font-weight: 800; margin: 4px 0; line-height: 1.2; }}
            #modal-player-team {{ font-size: 16px; color: #94a3b8; }}
            #modal-player-image {{
                width: calc(100% + 32px); margin-left: -16px; margin-top: 10px;
                height: 60%;
                -webkit-mask-image: linear-gradient(to top, transparent 0%, black 25%);
                mask-image: linear-gradient(to top, transparent 0%, black 25%);
            }}
            #modal-player-image img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
            .modal-footer-link {{ display: block; text-align: center; color: #60a5fa; text-decoration: none; margin-top: 15px; font-weight: 600; }}

            @media (min-width: 768px) {{
                .pitch-wrapper {{ max-width: 700px; aspect-ratio: unset; height: 680px; }}
                .player-card {{ max-width: 110px; }}
                .p-name {{ font-size: 13px; }}
                .p-team {{ font-size: 10px; }}
                .card-header {{ font-size: 10px; padding: 5px; }}
                .player-image-small {{ height: 70px; }}
            }}
        </style>
    </head>
    <body>
        <div class="pitch-wrapper">
            <div class="pitch">
                <div class="formation-badge">{formacion_str}</div>
                <div class="area top"></div>
                <div class="area bot"></div>
                <div class="line-half"></div>
                <div class="circle-center"></div>
                {lineas_html}
            </div>
        </div>

        <div id="player-modal" class="modal-overlay">
            <div class="modal-card">
                <button class="modal-close">&times;</button>
                <div class="modal-card-header">
                    <span id="modal-prob">99%</span> - <span id="modal-pos">DEL</span>
                    <h2 id="modal-player-name">Nombre Jugador</h2>
                    <p id="modal-player-team">Equipo</p>
                </div>
                <div id="modal-player-image">
                    <img src="" alt="Foto del jugador">
                </div>
                <a id="modal-profile-link" href="#" target="_blank" class="modal-footer-link">Ver perfil completo</a>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function () {{
                const modal = document.getElementById('player-modal');
                const modalClose = modal.querySelector('.modal-close');
                const playerCards = document.querySelectorAll('.player-card');

                function showModal(playerData) {{
                    document.getElementById('modal-prob').innerText = playerData.probabilidad + '%';
                    document.getElementById('modal-pos').innerText = playerData.posicion;
                    document.getElementById('modal-player-name').innerText = playerData.nombre;
                    document.getElementById('modal-player-team').innerText = playerData.equipo;
                    document.getElementById('modal-player-image').querySelector('img').src = playerData.imagenUrl;
                    document.getElementById('modal-profile-link').href = playerData.perfilUrl;
                    modal.classList.add('visible');
                }}

                function hideModal() {{
                    modal.classList.remove('visible');
                }}

                playerCards.forEach(card => {{
                    card.addEventListener('click', function() {{
                        const playerData = {{
                            nombre: this.dataset.nombre,
                            equipo: this.dataset.equipo,
                            posicion: this.dataset.posicion,
                            probabilidad: this.dataset.probabilidad,
                            imagenUrl: this.dataset.imagenUrl,
                            perfilUrl: this.dataset.perfilUrl
                        }};
                        showModal(playerData);
                    }});
                }});

                modalClose.addEventListener('click', hideModal);
                modal.addEventListener('click', function(e) {{
                    if (e.target === modal) {{
                        hideModal();
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    return full_html
