import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

RUTA_CSV = Path("detecciones_georreferenciadas.csv")

# Mismo escenario que en 09_analisis_espacial.py (GeoPandas), ahora resuelto
# con SQL espacial — para comparar las dos formas de hacer lo mismo.
CENTRO_ZONA_OBRA = (40.4168, -3.7038)  # Puerta del Sol, Madrid
RADIO_ZONA_OBRA_METROS = 300


def conectar():
    url = (
        f"postgresql+psycopg2://{os.getenv('POSTGIS_USER')}:{os.getenv('POSTGIS_PASSWORD')}"
        f"@{os.getenv('POSTGIS_HOST')}:{os.getenv('POSTGIS_PORT')}/{os.getenv('POSTGIS_DB')}"
    )
    return create_engine(url)


def crear_tabla(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS detecciones"))
        conn.execute(text("""
            CREATE TABLE detecciones (
                id SERIAL PRIMARY KEY,
                imagen TEXT,
                clase TEXT,
                confianza NUMERIC,
                geom geometry(Point, 4326)
            )
        """))
        # Índice espacial GIST — sin él, ST_DWithin no puede descartar filas
        # lejanas usando el índice (ver TEORIA-GIS.md §6.6-6.7).
        conn.execute(text("CREATE INDEX idx_detecciones_geom ON detecciones USING GIST (geom)"))


def cargar_csv(engine, ruta_csv):
    df = pd.read_csv(ruta_csv)
    with engine.begin() as conn:
        for _, fila in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO detecciones (imagen, clase, confianza, geom)
                    VALUES (:imagen, :clase, :confianza,
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                """),
                {
                    "imagen": fila["imagen"],
                    "clase": fila["clase"],
                    "confianza": fila["confianza"],
                    "lon": fila["longitud"],
                    "lat": fila["latitud"],
                },
            )
    print(f"{len(df)} filas cargadas en la tabla 'detecciones'")


QUERY_ZONA = text("""
    WITH zona AS (
        SELECT ST_Transform(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 25830) AS geom
    )
    SELECT
        d.clase,
        COUNT(*) AS total,
        COUNT(*) FILTER (
            WHERE ST_DWithin(ST_Transform(d.geom, 25830), zona.geom, :radio)
        ) AS dentro
    FROM detecciones d, zona
    GROUP BY d.clase
    ORDER BY d.clase
""")


def analizar_zona(engine, centro, radio_metros):
    lat, lon = centro
    with engine.connect() as conn:
        filas = conn.execute(QUERY_ZONA, {"lon": lon, "lat": lat, "radio": radio_metros}).fetchall()

    print(f"\nResumen por clase (SQL espacial, zona de obra radio {radio_metros} m):")
    print(f"{'clase':<10} {'total':>6} {'dentro':>7} {'fuera':>6}")
    for clase, total, dentro in filas:
        print(f"{clase:<10} {total:>6} {dentro:>7} {total - dentro:>6}")


def mostrar_plan_consulta(engine, centro, radio_metros):
    # EXPLAIN muestra si Postgres usa el índice GIST (Index Scan) o recorre
    # toda la tabla (Seq Scan). Con solo 10 filas normalmente elige Seq Scan
    # igualmente (más barato para tan pocos datos) — el índice se nota a
    # partir de miles/millones de filas.
    lat, lon = centro
    query_explain = text(f"EXPLAIN {QUERY_ZONA.text}")
    with engine.connect() as conn:
        plan = conn.execute(query_explain, {"lon": lon, "lat": lat, "radio": radio_metros}).fetchall()

    print("\nPlan de ejecución (EXPLAIN) — para ver si se usaría el índice GIST a mayor escala:")
    for (linea,) in plan:
        print(f"  {linea}")


if __name__ == "__main__":
    engine = conectar()
    print("Conectado a PostGIS")

    crear_tabla(engine)
    cargar_csv(engine, RUTA_CSV)
    analizar_zona(engine, CENTRO_ZONA_OBRA, RADIO_ZONA_OBRA_METROS)
    mostrar_plan_consulta(engine, CENTRO_ZONA_OBRA, RADIO_ZONA_OBRA_METROS)
