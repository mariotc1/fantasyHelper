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


def _generar_card_html(jugador: pd.Series) -> str:
    """Genera el HTML para una única tarjeta de jugador."""
    prob = jugador.get('Probabilidad_num', 0)
    if prob >= 80: color_bg, color_txt, border_col = "#dcfce7", "#166534", "#22c55e"
    elif prob >= 60: color_bg, color_txt, border_col = "#fef9c3", "#854d0e", "#eab308"
    else: color_bg, color_txt, border_col = "#fee2e2", "#991b1b", "#ef4444"

    nombre_display = jugador.get('Mi_nombre', 'N/A')
    if len(nombre_display) > 12:
        parts = nombre_display.split()
        if len(parts) > 1:
            nombre_display = f"{parts[0][0]}. {parts[-1]}"
        else:
            nombre_display = nombre_display[:11] + "."

    imagen_url = jugador.get('Imagen_URL', 'https://static.futbolfantasy.com/images/default-black.jpg')
    perfil_url = jugador.get('Perfil_URL', '#')
    posicion = jugador.get('Posicion', 'N/A')
    equipo = jugador.get('Equipo', 'N/A')

    return f"""
    <div class="card-container">
        <div class="player-card" 
             style="--mouse-x: 50%; --mouse-y: 50%;"
             data-nombre="{jugador.get('Mi_nombre', 'N/A')}" 
             data-equipo="{equipo}" 
             data-posicion="{posicion}"
             data-probabilidad="{int(prob)}"
             data-imagen-url="{imagen_url}"
             data-perfil-url="{perfil_url}">
            <div class="player-card-inner">
                <div class="card-header">
                    <span class="pos-pill">{posicion}</span>
                    <span class="prob-pill" style="background:{color_bg}; color:{color_txt};">{int(prob)}%</span>
                </div>
                <div class="player-image-small">
                    <img src="{imagen_url}" alt="{nombre_display}" onerror="this.onerror=null;this.src='https://static.futbolfantasy.com/images/default-black.jpg';">
                </div>
                <div class="card-body">
                    <div class="p-name">{nombre_display}</div>
                    <div class="p-team">{equipo}</div>
                </div>
                <div class="health-bar" style="background:{border_col}; width:{prob}%;"></div>
            </div>
        </div>
    </div>
    """



def generar_html_alineacion_completa(
    df_xi: pd.DataFrame, 
    df_banca: pd.DataFrame = None,
    pdf_base64: str = None,
    link_twitter: str = "#",
    link_whatsapp: str = "#",
    render_for_screenshot: bool = False
) -> str:
    """
    Genera una visualización HTML de la alineación completa, incluyendo el banquillo
    y botones de acción integrados en el campo.
    Si render_for_screenshot es True, omite los botones para una captura limpia.
    """
    # 1. Organizar datos del XI titular y construir HTML del campo
    posiciones = {"POR": [], "DEF": [], "CEN": [], "DEL": []}
    for _, jugador in df_xi.iterrows():
        pos = jugador.get("Posicion")
        if pos in posiciones:
            posiciones[pos].append(jugador)
    formacion_str = f"{len(posiciones['DEF'])}-{len(posiciones['CEN'])}-{len(posiciones['DEL'])}"
    lineas_html = ""
    for pos_key in ["DEL", "CEN", "DEF", "POR"]:
        jugadores = posiciones[pos_key]
        num_jugadores = len(jugadores)
        justify = "space-around" if num_jugadores > 1 else "center"
        linea_html = f'<div class="line" style="justify-content: {justify};">'
        for jugador in jugadores:
            linea_html += _generar_card_html(jugador)
        linea_html += "</div>"
        lineas_html += linea_html

    # 2. Construir HTML del banquillo si existe
    banquillo_html = ""
    if df_banca is not None and not df_banca.empty:
        banquillo_html = '<div class="bench-title"><span>Banquillo</span></div>'
        banquillo_html += '<div class="bench-container">'
        for _, jugador in df_banca.iterrows():
            banquillo_html += _generar_card_html(jugador)
        banquillo_html += '</div>'
    
    # 3. Construir HTML para los botones de acción (si no es para captura)
    action_buttons_html = ""
    if not render_for_screenshot:
        pdf_link_html = ""
        if pdf_base64:
            pdf_link_html = f"""
            <a href="data:application/pdf;base64,{pdf_base64}" download="fantasy_xi.pdf" class="action-btn pdf-btn" title="Descargar XI en PDF">
                <svg viewBox="0 0 24 24" fill="currentColor"><path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M13.5,16V19H10.5V16H8L12,12L16,16H13.5M13,9V3.5L18.5,9H13Z" /></svg>
            </a>
            """
        
        action_buttons_html = f"""
        <div class="action-buttons">
            <div class="share-menu">
                <button class="action-btn share-btn-main" title="Compartir XI">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18,16.08C17.24,16.08 16.56,16.38 16.04,16.85L8.91,12.7C8.96,12.47 9,12.24 9,12C9,11.76 8.96,11.53 8.91,11.3L16.04,7.15C16.56,7.62 17.24,7.92 18,7.92C19.66,7.92 21,6.58 21,4.92C21,3.26 19.66,1.92 18,1.92C16.34,1.92 15,3.26 15,4.92C15,5.16 15.04,5.39 15.09,5.61L7.96,9.75C7.44,9.28 6.76,8.98 6,8.98C4.34,8.98 3,10.32 3,11.98C3,13.64 4.34,14.98 6,14.98C6.76,14.98 7.44,14.68 7.96,14.2L15.09,18.34C15.04,18.57 15,18.8 15,19.04C15,20.7 16.34,22.04 18,22.04C19.66,22.04 21,20.7 21,19.04C21,17.38 19.66,16.08 18,16.08Z" /></svg>
                </button>
                <div class="share-options">
                    <a href="{link_twitter}" target="_blank" class="action-btn-sub twitter-btn" title="Compartir en X">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></svg>
                    </a>
                    <a href="{link_whatsapp}" target="_blank" class="action-btn-sub whatsapp-btn" title="Compartir en WhatsApp">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21 5.46 0 9.91-4.45 9.91-9.91S17.5 2 12.04 2zM12.04 20.12c-1.48 0-2.93-.4-4.2-1.15l-.3-.18-3.12.82.83-3.04-.2-.31c-.82-1.31-1.26-2.83-1.26-4.38 0-4.54 3.7-8.24 8.24-8.24 4.54 0 8.24 3.7 8.24 8.24s-3.7 8.24-8.24 8.24zm4.52-6.14c-.25-.12-1.47-.72-1.7-.8s-.39-.12-.56.12c-.17.25-.64.8-.79.96-.15.17-.3.19-.55.06s-1.04-.38-1.98-1.22c-.74-.66-1.23-1.47-1.38-1.72s-.02-.38.11-.51c.11-.11.25-.28.37-.42s.17-.25.25-.42c.08-.17.04-.31-.02-.43s-.56-1.34-.76-1.84c-.2-.48-.4-.42-.55-.42s-.3-.01-.46-.01c-.16 0-.42.06-.64.31s-.87.85-.87 2.07c0 1.22.89 2.4 1.01 2.56.12.17 1.76 2.67 4.27 3.78 2.51 1.1 2.51.74 2.96.71.45-.03 1.47-.6 1.67-1.18s.2-1.09.14-1.18c-.05-.1-.17-.16-.42-.28z"></path></svg>
                    </a>
                </div>
            </div>
            {pdf_link_html}
        </div>
        """
        
    # 4. HTML completo con CSS y JS
    background_style = "background: #f0f2f6;" if render_for_screenshot else "background: transparent;"
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
            body {{ 
                margin: 0; padding: 20px 0; font-family: 'Inter', sans-serif; {background_style}
                display: flex; flex-direction: column; align-items: center; overflow-x: hidden;
            }}
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
                position: absolute; bottom: 12px; right: 12px;
                background: rgba(0,0,0,0.6); color: white;
                padding: 4px 10px; border-radius: 20px;
                font-size: 12px; font-weight: 800; z-index: 5;
                backdrop-filter: blur(4px);
            }}
            /* Contenedor de botones de acción */
            .action-buttons {{
                position: absolute; bottom: 12px; left: 12px;
                z-index: 10; display: flex; gap: 8px;
            }}
            .action-btn, .action-btn-sub {{
                width: 36px; height: 36px; border-radius: 50%;
                background: rgba(0,0,0,0.6); color: white; border: none; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
                transition: all 0.2s ease-in-out; backdrop-filter: blur(4px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }}
            .action-btn:hover, .action-btn-sub:hover {{
                transform: scale(1.1); background: rgba(0,0,0,0.8);
            }}
            .action-btn svg, .action-btn-sub svg {{ width: 20px; height: 20px; }}
            /* Menú de compartir */
            .share-menu {{ position: relative; }}
            .share-options {{
                display: flex; flex-direction: column-reverse; gap: 8px;
                position: absolute; bottom: 44px; left: 0;
                opacity: 0; visibility: hidden;
                transform: translateY(10px); transition: all 0.2s ease-in-out;
            }}
            .share-menu:hover .share-options {{
                opacity: 1; visibility: visible; transform: translateY(0);
            }}
            .action-btn-sub.twitter-btn {{ background: #000; }}
            .action-btn-sub.whatsapp-btn {{ background: #25D366; }}
            .img-btn {{ background-color: #4A90E2; }}
            .pdf-btn {{ background-color: #D0021B; }}

            .line {{ flex: 1; display: flex; align-items: center; width: 100%; padding: 0 4px; z-index: 2; }}
            .card-container {{ width: 19%; display: flex; justify-content: center; perspective: 1000px; }}
            .player-card {{ width: 100%; max-width: 85px; cursor: pointer; transform-style: preserve-3d; transition: transform 0.1s linear; }}
            .player-card-inner {{
                position: relative; width: 100%;
                background: linear-gradient(160deg, rgba(248, 250, 252, 0.85), rgba(238, 242, 247, 0.75));
                backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
                border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                overflow: hidden; display: flex; flex-direction: column;
                border: 1px solid rgba(255, 255, 255, 0.5);
                transform: translateZ(0); transition: box-shadow 0.3s ease;
                padding-bottom: 3px;
            }}
            .player-card-inner.clicked {{ box-shadow: 0 0 25px rgba(255, 255, 255, 0.8), 0 4px 12px rgba(0,0,0,0.25); }}
            .player-card-inner::before, .player-card-inner::after {{
                content: ''; position: absolute; top: 0; left: 0;
                width: 100%; height: 100%; z-index: 0; pointer-events: none;
            }}
            .player-card-inner::before {{
                background: radial-gradient(circle at var(--mouse-x) var(--mouse-y), rgba(180, 210, 255, 0.6) 0%, rgba(200, 180, 255, 0.5) 25%, transparent 50%);
                opacity: 0; transition: opacity 0.4s ease;
            }}
            .player-card:hover .player-card-inner::before {{ opacity: 1; }}
            .player-card-inner::after {{
                left: -150%; width: 80%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                transform: skewX(-25deg); transition: left 0.8s cubic-bezier(0.23, 1, 0.32, 1);
            }}
            .player-card:hover .player-card-inner::after {{ left: 150%; }}
            .card-header, .player-image-small, .card-body, .health-bar {{ z-index: 1; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 3px 4px; font-size: 9px; font-weight: 700; color: #555; }}
            .player-image-small {{ height: 50px; width: 100%; overflow: hidden; }}
            .player-image-small img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
            .card-body {{ text-align: center; padding: 2px 2px 6px 2px; flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }}
            .p-name {{ font-size: clamp(10px, 2.5vw, 12px); font-weight: 800; color: #1e293b; line-height: 1.1; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .p-team {{ font-size: 8px; color: #64748b; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .health-bar {{ position: absolute; bottom: 0; left: 0; height: 3px; }}

            /* Estilos del Banquillo */
            .bench-title {{ width: 100%; text-align: center; margin: 20px 0 10px 0; font-size: 20px; font-weight: 800; color: #333; text-transform: uppercase; letter-spacing: 1px; }}
            .bench-title span {{ background: #f0f2f6; padding: 5px 20px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .bench-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; padding: 10px; width: 100%; max-width: 900px; }}
            .bench-container .card-container {{ width: 100px; }}
            .bench-container .player-card {{ max-width: 100px; }}

            /* Modal Styles */
            .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: 100; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; transition: opacity 0.4s ease, visibility 0.4s ease; }}
            .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
            .modal-card {{ width: 90%; max-width: 340px; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 10px 40px rgba(0,0,0,0.3); padding: 20px; color: #333; transform: scale(0.95); opacity: 0; transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease; }}
            .modal-overlay.visible .modal-card {{ transform: scale(1); opacity: 1; }}
            .modal-close {{ position: absolute; top: 10px; right: 10px; width: 30px; height: 30px; border-radius: 50%; background: rgba(0, 0, 0, 0.1); color: #333; border: none; cursor: pointer; font-size: 16px; font-weight: bold; display: flex; align-items: center; justify-content: center; }}
            #modal-player-image {{ width: 100%; height: 200px; border-radius: 12px; overflow: hidden; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
            #modal-player-image img {{ width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }}
            #modal-player-name {{ font-size: 28px; font-weight: 800; margin: 8px 0; line-height: 1.1; color: #1a202c; text-align: center; transform: translateY(20px); opacity: 0; text-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            #modal-player-team {{ font-size: 16px; color: #4a5568; text-align: center; transform: translateY(20px); opacity: 0; text-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .modal-stats {{ display: flex; justify-content: space-around; margin-top: 15px; transform: translateY(20px); opacity: 0;}}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: 800; color: #2d3748; text-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .stat-label {{ font-size: 12px; color: #718096; }}
            .modal-footer-link {{ display: block; text-align: center; color: #4299e1; text-decoration: none; margin-top: 20px; font-weight: 600; transform: translateY(20px); opacity: 0; }}
            .modal-overlay.visible .modal-card > *:not(#modal-player-image) {{ transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1), opacity 0.4s ease; }}
            .modal-overlay.visible #modal-player-name {{ transition-delay: 0.1s; }}
            .modal-overlay.visible #modal-player-team {{ transition-delay: 0.15s; }}
            .modal-overlay.visible .modal-stats {{ transition-delay: 0.2s; }}
            .modal-overlay.visible .modal-footer-link {{ transition-delay: 0.25s; }}
            .modal-overlay.visible .modal-card > *:not(.modal-close):not(#modal-player-image) {{ transform: translateY(0); opacity: 1; }}

            @media (prefers-color-scheme: dark) {{
                body {{ background: #0e1117; }}
                .bench-title {{ color: #e5e7eb; }}
                .bench-title span {{ background: #262730; }}
            }}
            @media (min-width: 768px) {{
                .pitch-wrapper {{ max-width: 600px; aspect-ratio: unset; height: 650px; }}
                .player-card {{ max-width: 100px; transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
                .p-name {{ font-size: 13px; }}
                .p-team {{ font-size: 10px; }}
                .card-header {{ font-size: 10px; padding: 5px; }}
                .player-image-small {{ height: 65px; }}
                .bench-container .card-container {{ width: 120px; }}
                .bench-container .player-card {{ max-width: 120px; }}
            }}
        </style>
    </head>
    <body>
        <div class="pitch-wrapper">
            <div class="pitch">
                {action_buttons_html}
                <div class="formation-badge">{formacion_str}</div>
                <div class="area top"></div>
                <div class="area bot"></div>
                <div class="line-half"></div>
                <div class="circle-center"></div>
                {lineas_html}
            </div>
        </div>

        {banquillo_html}

        <div id="player-modal" class="modal-overlay">
            <div class="modal-card">
                <button class="modal-close">&times;</button>
                <div id="modal-player-image"><img src="" alt="Foto del jugador"></div>
                <h2 id="modal-player-name">Nombre Jugador</h2>
                <p id="modal-player-team">Equipo</p>
                <div class="modal-stats">
                    <div class="stat">
                        <div id="modal-pos" class="stat-value"></div>
                        <div class="stat-label">Posición</div>
                    </div>
                    <div class="stat">
                        <div id="modal-prob" class="stat-value"></div>
                        <div class="stat-label">Prob. XI</div>
                    </div>
                </div>
                <a id="modal-profile-link" href="#" target="_blank" class="modal-footer-link">Ver perfil completo</a>
            </div>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function () {{
                const modal = document.getElementById('player-modal');
                const modalClose = modal.querySelector('.modal-close');
                const playerCards = document.querySelectorAll('.player-card');
                const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                if (isMobile) {{ setupGyro(); }} else {{ setupMouse(); }}

                function setupGyro() {{
                    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {{
                        document.body.addEventListener('click', function requestGyroPermission() {{
                            DeviceOrientationEvent.requestPermission()
                                .then(p => {{ if (p === 'granted') window.addEventListener('deviceorientation', handleOrientation); }})
                                .catch(console.error);
                        }}, {{ once: true }});
                    }} else if (typeof DeviceOrientationEvent !== 'undefined') {{
                        window.addEventListener('deviceorientation', handleOrientation);
                    }}
                }}
                
                function handleOrientation(event) {{
                    const beta = event.beta, gamma = event.gamma;
                    if (beta === null || gamma === null) return;
                    const rotX = Math.max(-45, Math.min(45, beta)) * 0.25;
                    const rotY = Math.max(-45, Math.min(45, gamma)) * 0.5;
                    window.requestAnimationFrame(() => {{
                        playerCards.forEach(c => c.style.transform = `rotateX(${{rotX}}deg) rotateY(${{rotY}}deg) scale(1.03)`);
                    }});
                }}
                
                function setupMouse() {{
                    playerCards.forEach(card => {{
                        const inner = card.querySelector('.player-card-inner');
                        card.addEventListener('mousemove', (e) => {{
                            const r = card.getBoundingClientRect();
                            const x = e.clientX - r.left, y = e.clientY - r.top;
                            const rotX = (y - r.height / 2) / (r.height / 2) * -8;
                            const rotY = (x - r.width / 2) / (r.width / 2) * 8;
                            window.requestAnimationFrame(() => {{
                                card.style.transform = `rotateX(${{rotX}}deg) rotateY(${{rotY}}deg) scale(1.05)`;
                            }});
                            card.style.setProperty('--mouse-x', `${{(x / r.width) * 100}}%`);
                            card.style.setProperty('--mouse-y', `${{(y / r.height) * 100}}%`);
                        }});
                        card.addEventListener('mouseleave', () => card.style.transform = 'rotateX(0) rotateY(0) scale(1)');
                    }});
                }}

                function showModal(data) {{
                    document.getElementById('modal-prob').innerText = data.probabilidad + '%';
                    document.getElementById('modal-pos').innerText = data.posicion;
                    document.getElementById('modal-player-name').innerText = data.nombre;
                    document.getElementById('modal-player-team').innerText = data.equipo;
                    document.getElementById('modal-player-image').querySelector('img').src = data.imagenUrl;
                    document.getElementById('modal-profile-link').href = data.perfilUrl;
                    modal.classList.add('visible');
                }}

                function hideModal() {{ modal.classList.remove('visible'); }}

                playerCards.forEach(card => {{
                    card.addEventListener('click', function() {{ showModal(this.dataset); }});
                }});

                modalClose.addEventListener('click', hideModal);
                modal.addEventListener('click', e => {{ if (e.target === modal) hideModal(); }});
            }});
        </script>
    </body>
    </html>
    """
    return full_html


def generar_html_grid_jugadores(
    df_jugadores: pd.DataFrame,
    titulo: str = "Jugadores de tu Plantilla"
) -> str:
    """
    Genera una visualización HTML de una lista de jugadores en un grid responsivo.
    """
    # 1. Construir HTML del grid
    grid_html = ""
    if df_jugadores is not None and not df_jugadores.empty:
        grid_html = f'<div class="bench-title"><span>{titulo} ({len(df_jugadores)})</span></div>'
        grid_html += '<div class="bench-container">'
        for _, jugador in df_jugadores.iterrows():
            grid_html += _generar_card_html(jugador)
        grid_html += '</div>'

    # 2. HTML completo con CSS y JS
    full_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0; padding: 10px 0; font-family: 'Inter', sans-serif; background: transparent;
                display: flex; flex-direction: column; align-items: center; overflow-x: hidden;
            }}
            .card-container {{ width: 100px; display: flex; justify-content: center; perspective: 1000px; }}
            .player-card {{ width: 100%; max-width: 85px; cursor: pointer; transform-style: preserve-3d; transition: transform 0.1s linear; }}
            .player-card-inner {{
                position: relative; width: 100%;
                background: linear-gradient(160deg, rgba(248, 250, 252, 0.85), rgba(238, 242, 247, 0.75));
                backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
                border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                overflow: hidden; display: flex; flex-direction: column;
                border: 1px solid rgba(255, 255, 255, 0.5);
                transform: translateZ(0); transition: box-shadow 0.3s ease;
                padding-bottom: 3px;
            }}
            .player-card:hover .player-card-inner {{ transform: scale(1.05); }}
            .card-header, .player-image-small, .card-body, .health-bar {{ z-index: 1; }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; padding: 3px 4px; font-size: 9px; font-weight: 700; }}
            .pos-pill {{ background: rgba(0,0,0,0.05); padding: 1px 4px; border-radius: 4px; }}
            .prob-pill {{ padding: 1px 4px; border-radius: 4px; }}
            .player-image-small {{ height: 50px; width: 100%; overflow: hidden; }}
            .player-image-small img {{ width: 100%; height: 100%; object-fit: cover; object-position: top; }}
            .card-body {{ text-align: center; padding: 2px 2px 6px 2px; flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }}
            .p-name {{ font-size: clamp(10px, 2.5vw, 12px); font-weight: 800; color: #1e293b; line-height: 1.1; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .p-team {{ font-size: 8px; color: #64748b; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .health-bar {{ position: absolute; bottom: 0; left: 0; height: 3px; }}

            .bench-title {{ width: 100%; text-align: center; margin: 0 0 15px 0; font-size: 16px; font-weight: 800; color: #555; text-transform: uppercase; letter-spacing: 0.5px; }}
            .bench-title span {{ background: rgba(0,0,0,0.03); padding: 6px 15px; border-radius: 20px; }}
            .bench-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; padding: 10px; width: 100%; max-width: 900px; }}

            .modal-overlay, .modal-card, .modal-close, #modal-player-image, #modal-player-name, #modal-player-team, .modal-stats, .stat, .stat-value, .stat-label, .modal-footer-link {{
                /* Re-use all modal styles from above */
            }}
            .modal-overlay {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: 1000; display: flex; align-items: center; justify-content: center; opacity: 0; visibility: hidden; transition: opacity 0.4s ease, visibility 0.4s ease; }}
            .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
            .modal-card {{ width: 90%; max-width: 340px; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.3); box-shadow: 0 10px 40px rgba(0,0,0,0.3); padding: 20px; color: #333; transform: scale(0.95); opacity: 0; transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease; position: relative; }}
            .modal-overlay.visible .modal-card {{ transform: scale(1); opacity: 1; }}
            .modal-close {{ position: absolute; top: 10px; right: 10px; width: 30px; height: 30px; border-radius: 50%; background: rgba(0, 0, 0, 0.1); color: #333; border: none; cursor: pointer; font-size: 16px; font-weight: bold; display: flex; align-items: center; justify-content: center; z-index: 1010; }}
            #modal-player-image {{ width: 100%; height: 200px; border-radius: 12px; overflow: hidden; margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
            #modal-player-image img {{ width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }}
            #modal-player-name {{ font-size: 28px; font-weight: 800; margin: 8px 0; line-height: 1.1; color: #1a202c; text-align: center; }}
            #modal-player-team {{ font-size: 16px; color: #4a5568; text-align: center;}}
            .modal-stats {{ display: flex; justify-content: space-around; margin-top: 15px;}}
            .stat {{ text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: 800; color: #2d3748; }}
            .stat-label {{ font-size: 12px; color: #718096; }}
            .modal-footer-link {{ display: block; text-align: center; color: #4299e1; text-decoration: none; margin-top: 20px; font-weight: 600; }}

            @media (prefers-color-scheme: dark) {{
                .bench-title {{ color: #e5e7eb; }}
                .bench-title span {{ background: #262730; }}
                .player-card-inner {{ background: linear-gradient(160deg, rgba(55, 65, 81, 0.85), rgba(31, 41, 55, 0.75)); border: 1px solid rgba(255, 255, 255, 0.2); }}
                .p-name {{ color: #f3f4f6; }} .p-team {{ color: #9ca3af; }}
                .pos-pill {{ background: rgba(255,255,255,0.08); }}
                .modal-card {{ background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.1); }}
                #modal-player-name, #modal-player-team, .stat-value, .modal-close {{ color: #e5e7eb; }}
                .stat-label {{ color: #9ca3af; }}
            }}
             @media (min-width: 768px) {{
                .card-container {{ width: 120px; }}
                .player-card {{ max-width: 120px; }}
            }}
        </style>
    </head>
    <body>
        {grid_html}
        <div id="player-modal" class="modal-overlay">
            <div class="modal-card">
                <button class="modal-close">&times;</button>
                <div id="modal-player-image"><img src="" alt="Foto del jugador"></div>
                <h2 id="modal-player-name">Nombre Jugador</h2>
                <p id="modal-player-team">Equipo</p>
                <div class="modal-stats">
                    <div class="stat">
                        <div id="modal-pos" class="stat-value"></div>
                        <div class="stat-label">Posición</div>
                    </div>
                    <div class="stat">
                        <div id="modal-prob" class="stat-value"></div>
                        <div class="stat-label">Prob. XI</div>
                    </div>
                </div>
                <a id="modal-profile-link" href="#" target="_blank" class="modal-footer-link">Ver perfil completo</a>
            </div>
        </div>
        <script>
            // El script para el modal es autocontenido y se puede copiar directamente.
            document.addEventListener('DOMContentLoaded', function () {{
                const modal = document.getElementById('player-modal');
                if (!modal) return;
                const modalClose = modal.querySelector('.modal-close');
                const playerCards = document.querySelectorAll('.player-card');

                function showModal(data) {{
                    document.getElementById('modal-prob').innerText = data.probabilidad + '%';
                    document.getElementById('modal-pos').innerText = data.posicion;
                    document.getElementById('modal-player-name').innerText = data.nombre;
                    document.getElementById('modal-player-team').innerText = data.equipo;
                    document.getElementById('modal-player-image').querySelector('img').src = data.imagenUrl;
                    document.getElementById('modal-profile-link').href = data.perfilUrl;
                    modal.classList.add('visible');
                }}

                function hideModal() {{ modal.classList.remove('visible'); }}

                playerCards.forEach(card => {{
                    card.addEventListener('click', function() {{ showModal(this.dataset); }});
                }});

                modalClose.addEventListener('click', hideModal);
                modal.addEventListener('click', e => {{ if (e.target === modal) hideModal(); }});
            }});
        </script>
    </body>
    </html>
    """
    return full_html
