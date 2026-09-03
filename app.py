# ---------------------------------------------------------
# RUTA WEB PRINCIPAL (Buscador)
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def inicio():
    busqueda = request.args.get("q", "").strip()
    filtro_tipo = request.args.get("tipo", "peliculas")

    peliculas = []
    albumes = []

    conn = obtener_conexion()
    cursor = conn.cursor()

    # 1. Obtener total de artistas
    cursor.execute("SELECT COUNT(*) AS total FROM artistas")
    res_artistas = cursor.fetchone()
    total_artistas_val = res_artistas["total"] if res_artistas else 0

    # 2. Obtener total de películas
    cursor.execute("SELECT COUNT(*) AS total FROM peliculas")
    res_peliculas = cursor.fetchone()
    total_peliculas_val = res_peliculas["total"] if res_peliculas else 0

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

    # Enviamos ambas variables a la plantilla
    return render_template(
        "index.html",
        peliculas=peliculas,
        albumes=albumes,
        busqueda=busqueda,
        tipo=filtro_tipo,
        total_artistas=total_artistas_val,
        total_peliculas=total_peliculas_val
    )
