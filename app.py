import sqlite3
import os
from flask import Flask, render_template, request

app = Flask(__name__)
RUTA_BD = os.path.join(os.path.dirname(__file__), "El_Arca.db")

def obtener_conexion():
    conn = sqlite3.connect(RUTA_BD)
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por su nombre
    return conn

@app.route("/", methods=["GET"])
def inicio():
    busqueda = request.args.get("q", "").strip()
    filtro_tipo = request.args.get("tipo", "peliculas")

    peliculas = []
    albumes = []

    conn = obtener_conexion()
    cursor = conn.cursor()

    if filtro_tipo == "peliculas":
        if busqueda:
            # Busca en titulo, saga, decada, anio, resolucion y es_x265 / es_animada
            query = """
                SELECT * FROM peliculas
                WHERE titulo LIKE ?
                   OR saga LIKE ?
                   OR decada LIKE ?
                   OR CAST(anio_estreno AS TEXT) LIKE ?
                   OR resolucion LIKE ?
                   OR (es_animada = 1 AND 'animada' LIKE ?)
                   OR (es_x265 = 1 AND 'x265' LIKE ?)
                ORDER BY anio_estreno DESC
            """
            param = f"%{busqueda}%"
            peliculas = cursor.execute(query, (param, param, param, param, param, param, param)).fetchall()
        else:
            peliculas = cursor.execute("SELECT * FROM peliculas ORDER BY id DESC LIMIT 50").fetchall()

    elif filtro_tipo == "musica":
        if busqueda:
            # Busca en artista, titulo del album, anio de lanzamiento, formato y bitrate
            query = """
                SELECT a.nombre AS artista, al.titulo_album, al.anio_lanzamiento, al.bitrate, al.formato
                FROM albumes al
                JOIN artistas a ON al.artista_id = a.id
                WHERE a.nombre LIKE ?
                   OR al.titulo_album LIKE ?
                   OR CAST(al.anio_lanzamiento AS TEXT) LIKE ?
                   OR al.formato LIKE ?
                   OR al.bitrate LIKE ?
                ORDER BY al.anio_lanzamiento DESC
            """
            param = f"%{busqueda}%"
            albumes = cursor.execute(query, (param, param, param, param, param)).fetchall()
        else:
            query = """
                SELECT a.nombre AS artista, al.titulo_album, al.anio_lanzamiento, al.bitrate, al.formato
                FROM albumes al
                JOIN artistas a ON al.artista_id = a.id
                ORDER BY al.id DESC LIMIT 50
            """
            albumes = cursor.execute(query).fetchall()

    conn.close()
    return render_template("index.html", peliculas=peliculas, albumes=albumes, busqueda=busqueda, tipo=filtro_tipo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
