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
                     style="--mouse-x: 50%; --mouse-y: 50%;"
                     data-nombre="{jugador['Mi_nombre']}" 
                     data-equipo="{jugador['Equipo']}" 
                     data-posicion="{jugador['Posicion']}"
                     data-probabilidad="{int(prob)}"
                     data-imagen-url="{imagen_url}"
                     data-perfil-url="{perfil_url}">
                    <div class="player-card-inner">
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
            
            .card-container {{ 
                width: 19%; 
                display: flex; 
                justify-content: center;
                perspective: 1000px;
            }}
            .player-card {{
                width: 100%; max-width: 85px;
                cursor: pointer;
                transform-style: preserve-3d;
                transition: transform 0.1s linear; /* Faster transition for gyro */
            }}
            .player-card-inner {{
                position: relative;
                width: 100%;
                height: 100%;
                background: linear-gradient(160deg, rgba(248, 250, 252, 0.85), rgba(238, 242, 247, 0.75));
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border-radius: 8px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.25);
                overflow: hidden; 
                display: flex; 
                flex-direction: column;
                border: 1px solid rgba(255, 255, 255, 0.5);
                transform: translateZ(0);
                transition: box-shadow 0.3s ease;
            }}
             .player-card-inner.clicked {{
                box-shadow: 0 0 25px rgba(255, 255, 255, 0.8), 0 4px 12px rgba(0,0,0,0.25);
            }}
            
            /* Holographic BG & Shine Effect */
            .player-card-inner::before, .player-card-inner::after {{
                content: '';
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
                z-index: 0;
                pointer-events: none;
            }}
            /* Holographic shimmer */
            .player-card-inner::before {{
                background: radial-gradient(
                    circle at var(--mouse-x) var(--mouse-y),
                    rgba(180, 210, 255, 0.6) 0%,
                    rgba(200, 180, 255, 0.5) 25%,
                    transparent 50%
                );
                opacity: 0;
                transition: opacity 0.4s ease;
            }}
            .player-card:hover .player-card-inner::before {{
                opacity: 1;
            }}
            /* Sweeping shine */
            .player-card-inner::after {{
                left: -150%;
                width: 80%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                transform: skewX(-25deg);
                transition: left 0.8s cubic-bezier(0.23, 1, 0.32, 1);
            }}
            .player-card:hover .player-card-inner::after {{
                left: 150%;
            }}

            .card-header, .player-image-small, .card-body, .health-bar {{
                z-index: 1; /* Ensure content is above the pseudo-elements */
            }}

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
                background: rgba(0,0,0,0.5); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
                z-index: 100; display: flex; align-items: center; justify-content: center;
                opacity: 0; visibility: hidden; transition: opacity 0.4s ease, visibility 0.4s ease;
            }}
            .modal-overlay.visible {{ opacity: 1; visibility: visible; }}
            .modal-card {{
                width: 90%; max-width: 340px;
                background: rgba(255, 255, 255, 0.25); /* Increased opacity */
                backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                padding: 20px;
                color: #333;
                transform: scale(0.95); opacity: 0;
                transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
            }}
            .modal-overlay.visible .modal-card {{ transform: scale(1); opacity: 1; }}
            .modal-close {{
                position: absolute; top: 10px; right: 10px;
                width: 30px; height: 30px; border-radius: 50%;
                background: rgba(0, 0, 0, 0.1); color: #333;
                border: none; cursor: pointer; font-size: 16px; font-weight: bold;
                display: flex; align-items: center; justify-content: center;
            }}
            
            #modal-player-image {{
                width: 100%; height: 200px; border-radius: 12px; overflow: hidden;
                margin: 10px 0; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                /* No entry animation for the image to ensure it's always visible */
            }}
            #modal-player-image img {{ width: 100%; height: 100%; object-fit: cover; object-position: center 15%; }}
            
            #modal-player-name {{
                font-size: 28px; font-weight: 800; margin: 8px 0; line-height: 1.1;
                color: #1a202c; text-align: center;
                transform: translateY(20px); opacity: 0;
                text-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            #modal-player-team {{ 
                font-size: 16px; color: #4a5568; text-align: center; 
                transform: translateY(20px); opacity: 0;
                text-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            
            .modal-stats {{ display: flex; justify-content: space-around; margin-top: 15px; transform: translateY(20px); opacity: 0;}}
            .stat {{ text-align: center; }}
            .stat-value {{ 
                font-size: 24px; font-weight: 800; color: #2d3748;
                text-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .stat-label {{ font-size: 12px; color: #718096; }}

            .modal-footer-link {{ 
                display: block; text-align: center; color: #4299e1; text-decoration: none; 
                margin-top: 20px; font-weight: 600; transform: translateY(20px); opacity: 0;
            }}

            /* Modal Content Animation */
            .modal-overlay.visible .modal-card > *:not(#modal-player-image) {{
                transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1), opacity 0.4s ease;
            }}
            .modal-overlay.visible #modal-player-name {{ transition-delay: 0.1s; }}
            .modal-overlay.visible #modal-player-team {{ transition-delay: 0.15s; }}
            .modal-overlay.visible .modal-stats {{ transition-delay: 0.2s; }}
            .modal-overlay.visible .modal-footer-link {{ transition-delay: 0.25s; }}
            
            .modal-overlay.visible .modal-card > *:not(.modal-close):not(#modal-player-image) {{
                 transform: translateY(0);
                 opacity: 1;
            }}

            @media (min-width: 768px) {{
                .pitch-wrapper {{ max-width: 700px; aspect-ratio: unset; height: 680px; }}
                .player-card {{ max-width: 110px; transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
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
                <div id="modal-player-image">
                    <img src="" alt="Foto del jugador">
                </div>
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

                function setupGyro() {{
                    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {{
                        // iOS 13+ requires user interaction to request permission.
                        // We'll ask on the first click on the body.
                        document.body.addEventListener('click', function requestGyroPermission() {{
                            DeviceOrientationEvent.requestPermission()
                                .then(permissionState => {{
                                    if (permissionState === 'granted') {{
                                        window.addEventListener('deviceorientation', handleOrientation);
                                        // Remove the listener so it doesn't ask again.
                                        document.body.removeEventListener('click', requestGyroPermission);
                                    }}
                                }})
                                .catch(console.error);
                        }}, {{ once: true }});
                    }} else if (typeof DeviceOrientationEvent !== 'undefined') {{
                        // Non-iOS or older iOS devices
                        window.addEventListener('deviceorientation', handleOrientation);
                    }}
                }}
                
                function handleOrientation(event) {{
                    const beta = event.beta;  //-180 to 180 (front-to-back tilt)
                    const gamma = event.gamma; //-90 to 90 (left-to-right tilt)
                    
                    if (beta === null || gamma === null) return;

                    // Clamp values for stability and subtle effect
                    const clampedBeta = Math.max(-45, Math.min(45, beta));
                    const clampedGamma = Math.max(-45, Math.min(45, gamma));

                    const rotateX = clampedBeta * 0.25;
                    const rotateY = clampedGamma * 0.5;
                    
                    // Use requestAnimationFrame to avoid layout thrashing and for smoother animations
                    window.requestAnimationFrame(() => {{
                        playerCards.forEach(card => {{
                            card.style.transform = `rotateX(${{rotateX}}deg) rotateY(${{rotateY}}deg) scale(1.03)`;
                        }});
                    }});
                }}
                
                if (isMobile) {{
                   setupGyro();
                }} else {{
                    // Desktop mouse interactions
                    playerCards.forEach(card => {{
                        const cardInner = card.querySelector('.player-card-inner');
                        
                        card.addEventListener('mousemove', (e) => {{
                            const rect = card.getBoundingClientRect();
                            const x = e.clientX - rect.left;
                            const y = e.clientY - rect.top;
                            const {{width, height}} = rect;
                            
                            const rotateX = (y - height / 2) / (height / 2) * -8;
                            const rotateY = (x - width / 2) / (width / 2) * 8;
                            
                            window.requestAnimationFrame(() => {{
                                card.style.transform = `rotateX(${{rotateX}}deg) rotateY(${{rotateY}}deg) scale(1.05)`;
                            }});

                            const bgPosX = (x / width) * 100;
                            const bgPosY = (y / height) * 100;
                            card.style.setProperty('--mouse-x', `${{bgPosX}}%`);
                            card.style.setProperty('--mouse-y', `${{bgPosY}}%`);
                        }});

                        card.addEventListener('mouseleave', () => {{
                            card.style.transform = 'rotateX(0) rotateY(0) scale(1)';
                            if (cardInner) cardInner.classList.remove('clicked');
                        }});

                        card.addEventListener('mousedown', () => {{
                            if (cardInner) cardInner.classList.add('clicked');
                        }});
                        card.addEventListener('mouseup', () => {{
                            if (cardInner) cardInner.classList.remove('clicked');
                        }});
                    }});
                }}

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
