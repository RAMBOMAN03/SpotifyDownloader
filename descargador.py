import requests
from bs4 import BeautifulSoup
import yt_dlp
import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import requests

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

def inyectar_metadatos_mp3(ruta_mp3, metadatos):
    """
    Descarga la carátula e inyecta las etiquetas ID3 (Título, Artista, Álbum, Año y Portada)
    dentro del archivo MP3.
    """
    print(f"🏷️  Inyectando metadatos en '{ruta_mp3}'...")
    
    try:
        # 1. Guardar metadatos de texto básicos (EasyID3 hace que sea muy sencillo)
        # Si el archivo no tiene cabecera ID3 básica, EasyID3 la crea automáticamente
        try:
            audio_texto = EasyID3(ruta_mp3)
        except Exception:
            # Si da error por falta de tags, añadimos una estructura básica limpia
            from mutagen.id3 import ID3NoHeaderError
            audio_texto = EasyID3()
            audio_texto.save(ruta_mp3)
            audio_texto = EasyID3(ruta_mp3)

        audio_texto['title'] = metadatos['titulo']
        audio_texto['artist'] = metadatos['artistas']
        audio_texto['album'] = metadatos['album']
        audio_texto['date'] = metadatos['anio']
        audio_texto.save()

        # 2. Guardar la Carátula (Requiere el módulo ID3 avanzado)
        # Descargamos la imagen de los servidores de Spotify en memoria
        respuesta_portada = requests.get(metadatos['url_portada'])
        if respuesta_portada.status_code == 200:
            audio_imagen = ID3(ruta_mp3)
            
            # APIC es la etiqueta ID3 estándar para "Attached Picture" (Imagen adjunta)
            audio_imagen.add(
                APIC(
                    encoding=3,          # 3 significa codificación UTF-8
                    mime='image/jpeg',   # Las portadas de Spotify suelen ser JPEG
                    type=3,              # 3 significa que es la portada frontal (Front Cover)
                    desc='Front Cover',
                    data=respuesta_portada.content # Los bytes de la imagen
                )
            )
            audio_imagen.save()
            print("🖼️  Carátula incrustada con éxito.")
        else:
            print("⚠️  No se pudo descargar la carátula de Spotify, el MP3 irá sin foto.")

        print("✅ Etiquetas ID3 guardadas perfectamente.")
        return True

    except Exception as e:
        print(f"❌ Error al inyectar los metadatos: {e}")
        return False

def main():
    print("=========================================")
    print("   SPOTIFY DOWNLOADER LOCAL - MULTITASK  ")
    print("=========================================\n")
    
    while True:
        print("Introduce la URL de Spotify (o escribe 'salir' para terminar):")
        url_objetivo = input("🔗 URL: ").strip()
        
        if url_objetivo.lower() == 'salir':
            print("\n👋 ¡Gracias por usar el descargador! Saliendo...")
            break
            
        if not url_objetivo:
            continue
        
        # Paso 1: Obtener la información de la canción
        metadatos = obtener_metadatos_spotify(url_objetivo)
        
        if not metadatos:
            print("❌ Saltando canción por error en metadatos.\n")
            return
            
        print(f"\n🎶 Procesando: {metadatos['titulo']} - {metadatos['artistas']} ({metadatos['anio']})")
        print(f"\n🎵 Canción: {metadatos['titulo']}")
        print(f"🎤 Artistas: {metadatos['artistas']}")
        print(f"💿 Álbum: {metadatos['album']}")
        print(f"📅 Año: {metadatos['anio']}\n")
        
        # Paso 2: Descargar el audio basándonos en esos metadatos
        archivo_mp3 = descargar_audio_desde_youtube(metadatos['artistas'], metadatos['titulo'])
        
        if not archivo_mp3:
            print("\n❌ Saltando canción por error en la etapa de descarga.")
            return

        # Paso 3: Inyectar las etiquetas y la portada al archivo descargado
        # Le pasamos la ruta del archivo generado y el diccionario de metadatos
        exito_tags = inyectar_metadatos_mp3(archivo_mp3, metadatos)
        
        if exito_tags:
            print(f"\n🚀 ¡PROCESO COMPLETADO CON ÉXITO!")
            print(f"📂 Archivo final listo: {os.path.abspath(archivo_mp3)}")
        else:
            print("\n⚠️ El archivo se descargó pero hubo problemas con las etiquetas.")
        
        print("-" * 40)

if __name__ == "__main__":
    main()