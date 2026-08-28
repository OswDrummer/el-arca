import sqlite3
import re
import os

RUTA_BASE = os.path.dirname(__file__)
RUTA_BD = os.path.join(RUTA_BASE, "El_Arca.db")
RUTA_PELIS = os.path.join(RUTA_BASE, "peliculas.txt")
RUTA_MUSICA = os.path.join(RUTA_BASE, "musica.txt")

def crear_base_de_datos():
    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS peliculas")
    cursor.execute("DROP TABLE IF EXISTS albumes")
    cursor.execute("DROP TABLE IF EXISTS artistas")

    cursor.execute("""
        CREATE TABLE peliculas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saga TEXT,
            titulo TEXT NOT NULL,
            anio_estreno INTEGER,
            decada TEXT,
            resolucion TEXT,
            es_x265 INTEGER DEFAULT 0,
            es_animada INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE artistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE albumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artista_id INTEGER,
            titulo_album TEXT NOT NULL,
            anio_lanzamiento INTEGER,
            bitrate TEXT,
            formato TEXT,
            FOREIGN KEY (artista_id) REFERENCES artistas (id)
        )
    """)

    conn.commit()
    conn.close()

def calcular_decada(anio):
    if not anio:
        return "Desconocida"
    return f"{(anio // 10) * 10}s"

def procesar_peliculas():
    if not os.path.exists(RUTA_PELIS):
        print(f"No se encontró el archivo: {RUTA_PELIS}")
        return

    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()

    saga_actual = "Independiente"

    with open(RUTA_PELIS, "r", encoding="utf-8") as file:
        for line in file:
            linea = line.strip()
            if not linea or linea.startswith("#"):
                continue

            if linea.startswith("[") and linea.endswith("]"):
                saga_actual = linea[1:-1].strip()
                continue

            match_anio = re.search(r'\((\d{4})\)', linea)
            anio = int(match_anio.group(1)) if match_anio else None
            decada = calcular_decada(anio)

            match_res = re.search(r'\b(1080p|720p|4K|2160p|480p)\b', linea, re.IGNORECASE)
            resolucion = match_res.group(1).upper() if match_res else "Desconocida"

            es_x265 = 1 if "x265" in linea.lower() or "hevc" in linea.lower() else 0
            es_animada = 1 if "animada" in linea.lower() or "animacion" in linea.lower() else 0

            titulo = re.sub(r'\(\d{4}\)', '', linea)
            titulo = re.sub(r'\b(1080p|720p|4K|2160p|480p|x265|HEVC|animada)\b', '', titulo, flags=re.IGNORECASE)
            titulo = re.sub(r'\[.*?\]', '', titulo).strip()

            cursor.execute("""
                INSERT INTO peliculas (saga, titulo, anio_estreno, decada, resolucion, es_x265, es_animada)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (saga_actual, titulo, anio, decada, resolucion, es_x265, es_animada))

    conn.commit()
    conn.close()

def procesar_musica():
    if not os.path.exists(RUTA_MUSICA):
        print(f"No se encontró el archivo: {RUTA_MUSICA}")
        return

    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()

    artista_actual_id = None

    with open(RUTA_MUSICA, "r", encoding="utf-8") as file:
        for line in file:
            linea = line.strip()
            if not linea or linea.startswith("#"):
                continue

            # Buscar si la línea contiene un año entre paréntesis: ej. (1997)
            match_anio = re.search(r'\((\d{4})\)', linea)

            if match_anio:
                # ES UN ÁLBUM (porque contiene año)
                if artista_actual_id:
                    anio = int(match_anio.group(1))

                    # Extraer lo que está entre corchetes, ej: [Mp3 128kbps] u [Opus 256k]
                    match_corchete = re.search(r'\[(.*?)\]', linea)
                    etiqueta = match_corchete.group(1).strip() if match_corchete else ""

                    # Determinar Formato
                    if "MP3" in etiqueta.upper():
                        formato = "MP3"
                    elif "FLAC" in etiqueta.upper():
                        formato = "FLAC"
                    elif "AAC" in etiqueta.upper() or "M4A" in etiqueta.upper():
                        formato = "AAC"
                    elif "OPUS" in etiqueta.upper():
                        formato = "Opus"
                    else:
                        formato = "MP3"  # Fallback por defecto

                    # Extraer Bitrate / Calidad (ej: 128kbps, 256k, 320k)
                    match_bitrate = re.search(r'\b(\d+k(?:bps)?|VBR|CBR|FLAC)\b', etiqueta, re.IGNORECASE)
                    bitrate = match_bitrate.group(1) if match_bitrate else (etiqueta if etiqueta else "Desconocido")

                    # Limpiar el título del álbum (quitar año y corchetes)
                    titulo_album = re.sub(r'\(\d{4}\)', '', linea)
                    titulo_album = re.sub(r'\[.*?\]', '', titulo_album).strip()

                    cursor.execute("""
                        INSERT INTO albumes (artista_id, titulo_album, anio_lanzamiento, bitrate, formato)
                        VALUES (?, ?, ?, ?, ?)
                    """, (artista_actual_id, titulo_album, anio, bitrate, formato))
            else:
                # ES UN ARTISTA (línea limpia sin año entre paréntesis)
                nombre_artista = linea.strip()
                cursor.execute("INSERT OR IGNORE INTO artistas (nombre) VALUES (?)", (nombre_artista,))
                cursor.execute("SELECT id FROM artistas WHERE nombre = ?", (nombre_artista,))
                res = cursor.fetchone()
                if res:
                    artista_actual_id = res[0]

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Creando estructura de base de datos...")
    crear_base_de_datos()

    print("Procesando archivo de películas...")
    procesar_peliculas()

    print("Procesando archivo de música...")
    procesar_musica()

    print("¡Proceso completado con éxito! La base de datos El_Arca.db ha sido regenerada.")
