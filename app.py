import sqlite3
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
RUTA_BD = os.path.join(os.path.dirname(__file__), "El_Arca.db")

def obtener_conexion():
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por su nombre
    return conn

# ---------------------------------------------------------
# RUTA WEB PRINCIPAL (Buscador + Estadísticas)
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def inicio():
    busqueda = request.args.get("q", "").strip()
    filtro_tipo = request.args.get("tipo", "peliculas")

    peliculas = []
    albumes = []

    conn = obtener_conexion()
    cursor = conn.cursor()

    # 1. Totales para el encabezado
    cursor.execute("SELECT COUNT(*) AS total FROM artistas")
    res_artistas = cursor.fetchone()
    total_artistas_val = res_artistas["total"] if res_artistas else 0

    cursor.execute("SELECT COUNT(*) AS total FROM peliculas")
    res_peliculas = cursor.fetchone()
    total_peliculas_val = res_peliculas["total"] if res_peliculas else 0

    cursor.execute("SELECT COUNT(*) AS total FROM albumes")
    res_albumes = cursor.fetchone()
    total_albumes_val = res_albumes["total"] if res_albumes else 0

    # 2. Consultas de búsqueda / listado inicial
    if filtro_tipo == "peliculas":
        if busqueda:
            query = """
                SELECT * FROM peliculas
                WHERE titulo LIKE ?
                   OR saga LIKE ?
                   OR decada LIKE ?
                   OR CAST(anio_estreno AS TEXT) LIKE ?
                   OR resolucion LIKE ?
                   OR (es_animada = 1 AND 'animada' LIKE ?)
                   OR (es_x265 = 1 AND 'x265' LIKE ?)
                ORDER BY anio_estreno ASC, titulo ASC
            """
            param = f"%{busqueda}%"
            peliculas = cursor.execute(query, (param, param, param, param, param, param, param)).fetchall()
        else:
            peliculas = cursor.execute("SELECT * FROM peliculas ORDER BY id DESC LIMIT 50").fetchall()

    elif filtro_tipo == "musica":
        if busqueda:
            query = """
                SELECT a.nombre AS artista, al.titulo_album, al.anio_lanzamiento, al.bitrate, al.formato
                FROM albumes al
                JOIN artistas a ON al.artista_id = a.id
                WHERE a.nombre LIKE ?
                   OR al.titulo_album LIKE ?
                   OR CAST(al.anio_lanzamiento AS TEXT) LIKE ?
                   OR al.formato LIKE ?
                   OR al.bitrate LIKE ?
                ORDER BY al.anio_lanzamiento ASC, al.titulo_album ASC
            """
            param = f"%{busqueda}%"
            albumes = cursor.execute(query, (param, param, param, param, param)).fetchall()
        else:
            query = """
                SELECT a.nombre AS artista, al.titulo_album, al.anio_lanzamiento, al.bitrate, al.formato
                FROM albumes al
                JOIN artistas a ON al.artista_id = a.id
                ORDER BY al.anio_lanzamiento ASC, al.titulo_album ASC LIMIT 50
            """
            albumes = cursor.execute(query).fetchall()

    conn.close()

    return render_template(
        "index.html",
        peliculas=peliculas,
        albumes=albumes,
        busqueda=busqueda,
        tipo=filtro_tipo,
        total_artistas=total_artistas_val,
        total_peliculas=total_peliculas_val,
        total_albumes=total_albumes_val
    )

# ---------------------------------------------------------
# ENDPOINTS API (JSON)
# ---------------------------------------------------------
@app.route("/api/total-artistas", methods=["GET"])
def total_artistas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM artistas")
    resultado = cursor.fetchone()
    total = resultado["total"] if resultado else 0
    conn.close()
    return jsonify({"ok": True, "total_artistas": total})

@app.route("/api/total-peliculas", methods=["GET"])
def total_peliculas():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM peliculas")
    resultado = cursor.fetchone()
    total = resultado["total"] if resultado else 0
    conn.close()
    return jsonify({"ok": True, "total_peliculas": total})

@app.route("/api/total-albumes", methods=["GET"])
def total_albumes():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM albumes")
    resultado = cursor.fetchone()
    total = resultado["total"] if resultado else 0
    conn.close()
    return jsonify({"ok": True, "total_albumes": total})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
