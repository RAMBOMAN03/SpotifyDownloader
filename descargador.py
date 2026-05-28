import requests
from bs4 import BeautifulSoup
import yt_dlp
import os

# ==========================================
# MÓDULO 1: EXTRACCIÓN DE METADATOS (SPOTIFY)
# ==========================================

def obtener_metadatos_spotify(url_spotify):
    """
    Hace scraping de la URL pública de Spotify y extrae los metadatos limpios.
    Devuelve un diccionario con la información o None si falla.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    try:
        respuesta = requests.get(url_spotify, headers=headers)
        if respuesta.status_code != 200:
            print(f"❌ Error al acceder a Spotify (Código: {respuesta.status_code})")
            return None
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        # Extraemos etiquetas crudas de los meta-tags
        titulo = soup.find("meta", property="og:title")["content"]
        descripcion = soup.find("meta", property="og:description")["content"]
        url_portada = soup.find("meta", property="og:image")["content"]
        
        # Parseamos la descripción (Ej: "YOVNGCHIMI, JC Reyes · MVLAN · Song · 2026")
        partes = [p.strip() for p in descripcion.split("·")]
        artistas = partes[0]
        album = partes[1]
        anio = partes[-1]
        
        return {
            "titulo": titulo,
            "artistas": artistas,
            "album": album,
            "anio": anio,
            "url_portada": url_portada
        }
    except Exception as e:
        print(f"❌ Error parseando metadatos de Spotify: {e}")
        return None


# ==========================================
# MÓDULO 2: DESCARGA DE AUDIO (YOUTUBE)
# ==========================================

def descargar_audio_desde_youtube(artistas, titulo):
    """
    Busca la canción en YouTube y descarga el audio convertido a MP3 a 320kbps.
    Devuelve el nombre del archivo generado si tiene éxito.
    """
    termino_busqueda = f"ytsearch1:{artistas} - {titulo} audio"
    nombre_archivo_salida = f"{titulo}.mp3"
    
    opciones_ytdl = {
        'format': 'bestaudio/best',
        'outtmpl': f'{titulo}.%(ext)s',  # Guarda temporalmente con la extensión nativa
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'quiet': False, # Muestra el progreso de la descarga en consola
    }
    
    try:
        print(f"🔍 Buscando en YouTube: '{artistas} - {titulo}'...")
        with yt_dlp.YoutubeDL(opciones_ytdl) as ydl:
            ydl.download([termino_busqueda])
        return nombre_archivo_salida
    except Exception as e:
        print(f"❌ Error al descargar desde YouTube: {e}")
        return None


# ==========================================
# FLUIDO PRINCIPAL (ORQUESTADOR / MAIN)
# ==========================================

def main():
    print("=== INICIANDO SPOTIFY DOWNLOADER LOCAL ===")
    
    url_objetivo = "https://open.spotify.com/intl-es/track/74t17BRV4el0mU0Tb8XY1k?si=aed609bf187241d6"
    
    # Paso 1: Obtener la información de la canción
    metadatos = obtener_metadatos_spotify(url_objetivo)
    
    if not metadatos:
        print("Abortando: No se pudieron obtener los metadatos.")
        return
        
    print(f"\n🎵 Canción: {metadatos['titulo']}")
    print(f"🎤 Artistas: {metadatos['artistas']}")
    print(f"📅 Año: {metadatos['anio']}\n")
    
    # Paso 2: Descargar el audio basándonos en esos metadatos
    archivo_mp3 = descargar_audio_desde_youtube(metadatos['artistas'], metadatos['titulo'])
    
    if archivo_mp3:
        print(f"\n🚀 Proceso completado. Archivo listo: {archivo_mp3}")
        # Aquí es donde en el futuro llamaremos al Hito 3: inyectar_metadatos(archivo_mp3, metadatos)
    else:
        print("\n❌ El proceso falló en la etapa de descarga.")

if __name__ == "__main__":
    main()