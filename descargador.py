import requests
from bs4 import BeautifulSoup
import yt_dlp
import os

def descargar_cancion_spotify(url_spotify):
    try:
        # 1. SCRAPING DE METADATOS
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        respuesta = requests.get(url_spotify, headers=headers)
        if respuesta.status_code != 200:
            print("No se pudo acceder a Spotify.")
            return
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        titulo = soup.find("meta", property="og:title")["content"]
        descripcion = soup.find("meta", property="og:description")["content"]
        url_portada = soup.find("meta", property="og:image")["content"]
        
        # Procesamos la descripción (Ejemplo: "YOVNGCHIMI, JC Reyes · MVLAN · Song · 2026")
        partes = [p.strip() for p in descripcion.split("·")]
        artistas = partes[0]      # "YOVNGCHIMI, JC Reyes"
        album = partes[1]         # "MVLAN"
        anio = partes[-1]         # "2026"
        
        print("\n=======================================")
        print(f"🎵 Procesando: {titulo} - {artistas}")
        print("=======================================")
        
        # 2. CONFIGURAR LA BÚSQUEDA Y DESCARGA CON YT-DLP
        # Creamos el término de búsqueda perfecto para YouTube
        termino_busqueda = f"ytsearch1:{artistas} - {titulo} audio"
        
        opciones_ytdl = {
            # Buscamos el mejor audio disponible
            'format': 'bestaudio/best',
            # Destino y nombre del archivo temporal (lo guardamos con el título de la canción)
            'outtmpl': f'{titulo}.%(ext)s',
            # Le decimos a FFmpeg que lo convierta a MP3 con la máxima calidad (320kbps)
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            # Evitamos que llene la pantalla con logos de descarga molestos
            'quiet': False, 
        }
        
        print(f"🔍 Buscando '{artistas} - {titulo}' en YouTube...")
        with yt_dlp.YoutubeDL(opciones_ytdl) as ydl:
            ydl.download([termino_busqueda])
            
        print(f"\n✅ ¡Descarga completada con éxito! Archivo: '{titulo}.mp3'")
        
        # Devolvemos los metadatos para el Hito 3 (Inyectar etiquetas)
        return {
            "archivo": f"{titulo}.mp3",
            "titulo": titulo,
            "artistas": artistas,
            "album": album,
            "anio": anio,
            "url_portada": url_portada
        }
        
    except Exception as e:
        print(f"❌ Error en el proceso: {e}")

# --- PRUEBA DEL HITO 2 ---
url_de_prueba = "https://open.spotify.com/intl-es/track/74t17BRV4el0mU0Tb8XY1k?si=aed609bf187241d6"
datos_cancion = descargar_cancion_spotify(url_de_prueba)