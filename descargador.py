import requests
import re
from bs4 import BeautifulSoup
import yt_dlp
import os
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import requests
import json

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
        'quiet': True,
        'no_warnings': True,    # Para ocultar un error que aparece si no tienes instalado Node.js en tu ordenador.
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
    
def procesar_cancion(url_spotify):
    # Paso 1: Obtener la información de la canción
    metadatos = obtener_metadatos_spotify(url_spotify)
    
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


def procesar_colecciones(url_spotify):
    """
    Extrae las canciones de una playlist o álbum usando la API pública 
    del widget de inserción de Spotify, esquivando bloqueos de HTML y DRM.
    """
    print("\n📦 Analizando la colección de Spotify vía Widget API... (Buscando canciones)")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3"
    }
    
    try:
        # 1. Identificar si es playlist o álbum y extraer su ID único
        # Usamos expresiones regulares básicas para limpiar la URL
        match_tipo = re.search(r"/(playlist|album)/([a-zA-Z0-9]+)", url_spotify)
        
        if not match_tipo:
            print("❌ No se pudo determinar si es un álbum o una playlist válida.")
            return
            
        tipo = match_tipo.group(1) # Extrae "playlist" o "album"
        id_coleccion = match_tipo.group(2) # Extrae el churro de letras/números del ID
        
        # 2. Llamamos a la API del Widget de Spotify (Es pública, rápida y devuelve JSON puro)
        url_api_widget = f"https://open.spotify.com/embed/{tipo}/{id_coleccion}"
        
        respuesta = requests.get(url_api_widget, headers=headers)
        if respuesta.status_code != 200:
            print(f"❌ No se pudo acceder a la colección del Widget (Código: {respuesta.status_code})")
            return
            
        # 3. Spotify guarda los datos de las canciones dentro de un script de JavaScript 
        # en una variable llamada resourceData. Vamos a cazar ese JSON textualmente.
        html = respuesta.text
        # Buscamos el texto que hay dentro de la etiqueta <script id="initial-state"> o similar
        # Para asegurar compatibilidad, buscamos el patrón del JSON de canciones
        buscar_json = re.search(r'<script id="initial-state" type="text/plain">([^<]+)</script>', html)
        
        urls_canciones = []
        
        if buscar_json:
            import urllib.parse
            # El JSON suele venir codificado en formato web (URL encoded), lo decodificamos
            texto_codificado = buscar_json.group(1)
            texto_claro = urllib.parse.unquote(texto_codificado)
            
            datos_json = json.loads(texto_claro)
            
            # Navegamos por el JSON interno del Widget de Spotify para extraer los IDs de los tracks
            # Dependiendo de si es álbum o playlist, la estructura cambia ligeramente, pero yt-dlp/spotify
            # suele estructurarlo en los recursos del cliente:
            try:
                instancias = datos_json.get("data", {}).get("entity", {})
                # Si es playlist, las canciones suelen venir en 'tracks', si es álbum en 'items' o directamente listadas
                tracks_lista = instancias.get("tracks", {}).get("items", []) or instancias.get("tracks", [])
                
                # Si viene vacío, probamos el formato alternativo del JSON comprimido
                if not tracks_lista and "r" in datos_json: # Formato compacto moderno de Spotify embed
                    # Intentamos buscar todos los IDs de canciones con un patrón de texto directo en el JSON descompreso
                    ids = re.findall(r'spotify:track:([a-zA-Z0-9]{22})', texto_claro)
                    for track_id in ids:
                        url_t = f"https://open.spotify.com/track/{track_id}"
                        if url_t not in urls_canciones:
                            urls_canciones.append(url_t)
                else:
                    for item in tracks_lista:
                        # En playlists a veces viene dentro de un nodo 'track'
                        track_info = item.get("track", item)
                        track_id = track_info.get("id")
                        if track_id:
                            urls_canciones.append(f"https://open.spotify.com/track/{track_id}")
            except Exception:
                pass

        # 4. PLAN C (El más bruto y efectivo): Si el JSON cambia de forma, usamos fuerza bruta de Regex.
        # Buscamos cualquier patrón "spotify:track:ID" o "/track/ID" dentro del HTML del embed.
        if not urls_canciones:
            ids_fuerza_bruta = re.findall(r'spotify:track:([a-zA-Z0-9]+)', html) or re.findall(r'/track/([a-zA-Z0-9]+)', html)
            for track_id in ids_fuerza_bruta:
                # Los IDs de canciones de Spotify siempre tienen 22 caracteres
                if len(track_id) == 22:
                    url_t = f"https://open.spotify.com/track/{track_id}"
                    if url_t not in urls_canciones:
                        urls_canciones.append(url_t)

        total_canciones = len(urls_canciones)
        
        if total_canciones == 0:
            print("❌ No se encontraron canciones. Verifica que la playlist sea pública o tenga canciones.")
            return
            
        print(f"📋 ¡API del Widget consultada con éxito! Se han detectado {total_canciones} canciones.")
        print("=" * 50)
        
        # Lanzamos el bucle definitivo hacia tu función procesar_cancion
        for indice, url_track in enumerate(urls_canciones, start=1):
            print(f"\n[➡] Canción {indice} de {total_canciones}")
            procesar_cancion(url_track)
            
        print("\n🎉 ¡Colección terminada de procesar con éxito! 🎉\n")
        
    except Exception as e:
        print(f"❌ Error crítico al procesar la colección: {e}")

def main():
    print("=========================================")
    print("   SPOTIFY DOWNLOADER LOCAL - MULTITASK  ")
    print("=========================================\n")
    
    while True:
        print("Introduce la URL de Spotify (o escribe 'salir' para terminar):")
        url_spotify = input("🔗 URL: ").strip()
        
        if url_spotify.lower() == 'salir':
            print("\n👋 ¡Gracias por usar el descargador! Saliendo...")
            break
        elif "/track/" in url_spotify:
            procesar_cancion(url_spotify)
        elif "/album/" in url_spotify or "/playlist/" in url_spotify:
            procesar_colecciones(url_spotify)
        elif not url_spotify:
            continue
        else:
            print("❌ No se ha encontrado una URL correcta de Spotify.")
            continue
        
        
if __name__ == "__main__":
    main()