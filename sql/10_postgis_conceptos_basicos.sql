-- =============================================================================
-- 10 — PostGIS a mano: conceptos básicos antes de automatizar con Python
-- =============================================================================
-- Objetivo: entender qué hace de verdad 10_postgis_analisis.py, tecleando las
-- mismas órdenes SQL una a una contra la base de datos, sin nada de Python
-- por medio. El script Python no hace magia — solo repite estos mismos pasos
-- en un bucle, leyendo el CSV en vez de valores escritos a mano.
--
-- Cómo ejecutar este archivo completo de una vez (con el contenedor arrancado,
-- `docker compose up -d postgis`):
--   docker exec -i arcgis-yolo-postgis psql -U gis_user -d gis_db < sql/10_postgis_conceptos_basicos.sql
--
-- O mejor para aprender: entra a una sesión interactiva y pega los bloques
-- uno a uno, leyendo el resultado de cada uno antes de pasar al siguiente:
--   docker exec -it arcgis-yolo-postgis psql -U gis_user -d gis_db
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. Crear una tabla con una columna de geometría real (no lat/lon sueltos)
-- -----------------------------------------------------------------------------
-- geometry(Point, 4326) = "esta columna guarda puntos, en el sistema de
-- coordenadas GPS normal (SRID 4326)". Ver TEORIA-GIS.md §6.3-6.4.

DROP TABLE IF EXISTS detecciones_manual;

CREATE TABLE detecciones_manual (
    id SERIAL PRIMARY KEY,
    clase TEXT,
    geom geometry(Point, 4326)
);


-- -----------------------------------------------------------------------------
-- 2. Insertar puntos a mano
-- -----------------------------------------------------------------------------
-- ST_MakePoint(lon, lat) construye el punto — OJO al orden, es (X, Y) =
-- (longitud, latitud), no (lat, lon) como solemos escribirlo a mano fuera de
-- SQL. ST_SetSRID le dice a Postgres en qué sistema de referencia está.

-- Punto 1: Puerta del Sol, Madrid — el centro de nuestra "zona de obra"
INSERT INTO detecciones_manual (clase, geom)
VALUES ('bus', ST_SetSRID(ST_MakePoint(-3.7038, 40.4168), 4326));

-- Punto 2: Barcelona — lejos, para tener con qué comparar
INSERT INTO detecciones_manual (clase, geom)
VALUES ('bus', ST_SetSRID(ST_MakePoint(2.1686, 41.3874), 4326));


-- -----------------------------------------------------------------------------
-- 3. Ver qué se ha guardado de verdad
-- -----------------------------------------------------------------------------
-- La geometría se guarda en un formato binario (WKB) ilegible a simple vista.
-- ST_AsText() la convierte a WKT (Well-Known Text), el formato de texto
-- estándar: POINT(lon lat).

SELECT id, clase, ST_AsText(geom) FROM detecciones_manual;

-- Resultado esperado:
--  id | clase |       st_astext
-- ----+-------+------------------------
--   1 | bus   | POINT(-3.7038 40.4168)
--   2 | bus   | POINT(2.1686 41.3874)


-- -----------------------------------------------------------------------------
-- 4. La pregunta real: ¿qué punto cae dentro de 300 m de Puerta del Sol?
-- -----------------------------------------------------------------------------
-- ST_DWithin(a, b, distancia) devuelve true/false. Reproyectamos a EPSG:25830
-- (métrico, España peninsular) porque en 4326 "300" serían grados, no metros
-- — ver el error clásico anotado en TEORIA-GIS.md §2 y §6.3.

SELECT
    id,
    clase,
    ST_DWithin(
        ST_Transform(geom, 25830),
        ST_Transform(ST_SetSRID(ST_MakePoint(-3.7038, 40.4168), 4326), 25830),
        300
    ) AS dentro_zona
FROM detecciones_manual;

-- Resultado esperado:
--  id | clase | dentro_zona
-- ----+-------+-------------
--   1 | bus   | t
--   2 | bus   | f


-- -----------------------------------------------------------------------------
-- 5. Bonus: distancia exacta en metros a Puerta del Sol
-- -----------------------------------------------------------------------------

SELECT
    id,
    clase,
    ROUND(
        ST_Distance(
            ST_Transform(geom, 25830),
            ST_Transform(ST_SetSRID(ST_MakePoint(-3.7038, 40.4168), 4326), 25830)
        )::numeric, 1
    ) AS distancia_metros
FROM detecciones_manual;


-- -----------------------------------------------------------------------------
-- Limpieza (opcional) — esta tabla es solo para practicar a mano.
-- El script 10_postgis_analisis.py crea y rellena su propia tabla
-- ('detecciones') automáticamente a partir del CSV real, así que no dependen
-- una de la otra.
-- -----------------------------------------------------------------------------
-- DROP TABLE detecciones_manual;
