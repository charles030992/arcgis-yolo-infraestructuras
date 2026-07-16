# ArcGIS + YOLO: Detección de Infraestructuras Georreferenciada

Pipeline completo: foto de obra → detección de objetos con YOLO → punto georreferenciado en ArcGIS Online.

---

## Índice de módulos

| #  | Script                     | Descripción                                              | Estado       |
|----|----------------------------|----------------------------------------------------------|--------------|
| 01 | `01_conexion_arcgis.py`    | Conexión a ArcGIS Online y búsqueda de capas públicas    | ✅ Completado |
| 02 | `02_login_autenticado.py`  | Autenticación OAuth con cuenta ArcGIS                    | ✅ Completado |
| 03 | `03_explorar_capa.py`      | Estructura de una Feature Layer: campos, geometría       | ✅ Completado |
| 04 | `04_consulta_filtros.py`   | Queries con filtros sobre capas reales                   | ✅ Completado |
| 05 | `05_mapas_interactivos.ipynb` | Mapas interactivos con Folium en Jupyter              | ✅ Completado |
| 06 | `06_publicar_capa.py`      | Crear y publicar capa propia en ArcGIS Online            | ✅ Completado |
| 07 | `07_yolo_deteccion.py`     | Detección de objetos con YOLOv8                          | ✅ Completado |
| 08 | `08_pipeline_completo.py`  | Foto → YOLO → punto georreferenciado en ArcGIS (EXIF o coordenada por defecto) | ✅ Completado |
| 09 | `09_analisis_espacial.py`  | Análisis espacial con GeoPandas/Shapely: buffer + spatial join sobre las detecciones | ✅ Completado |
| 10 | `10_postgis_analisis.py` + `sql/10_postgis_conceptos_basicos.sql` | Mismo análisis espacial resuelto con SQL espacial (PostGIS, `ST_*`) — primero a mano en SQL puro, luego automatizado en Python | ✅ Completado |

---

## Stack tecnológico

### GIS y datos espaciales
- **ArcGIS API for Python** — conexión, consulta y publicación de capas en ArcGIS Online
- **GeoPandas** — operaciones espaciales masivas, spatial join
- **Shapely** — geometrías individuales, buffer, intersección, distancia
- **Rasterio** — lectura de GeoTIFF, bandas, resolución, recorte
- **GDAL** — traducción entre formatos (`ogr2ogr`, `gdalwarp`)
- **PostGIS** — extensión espacial de PostgreSQL, funciones `ST_`, índices GIST

### Computer Vision
- **YOLOv8 (Ultralytics)** — detección de objetos en imágenes de infraestructuras

### Infraestructura y entorno
- **Docker** — contenerización del entorno Python + base de datos PostGIS
- **Git** — control de versiones con flujo de ramas por funcionalidad

### Visualización
- **Folium / Leaflet** — mapas interactivos en web y Jupyter
- **OpenLayers** — visualización de capas GIS en navegador

---

## Estructura del proyecto

```
arcGIS-Yolo-python/
├── 01_conexion_arcgis.py
├── 02_login_autenticado.py
├── 03_explorar_capa.py
├── 04_consulta_filtros.py
├── 05_mapas_interactivos.ipynb
├── 06_publicar_capa.py
├── 07_yolo_deteccion.py
├── 08_pipeline_completo.py
├── 09_analisis_espacial.py
├── 10_postgis_analisis.py
├── sql/
│   └── 10_postgis_conceptos_basicos.sql   # los mismos conceptos de 10, en SQL puro para practicar a mano
├── fotos_prueba/                # fotos de prueba (incluye una con GPS EXIF inyectado)
├── TEORIA-GIS.md                # notas de teoría de repaso (CRS, sjoin, PostGIS...)
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Caso de uso

Aplicado al sector de obra e infraestructuras:

1. Técnico fotografía señal, activo o defecto en campo
2. YOLO identifica el objeto y su tipo con bounding box
3. El sistema publica un punto georreferenciado en ArcGIS con foto y atributos
4. El equipo de gestión visualiza el mapa actualizado en tiempo real

---

## Setup local (sin Docker)

```bash
conda create -n arcgis-yolo python=3.11 -y
conda activate arcgis-yolo
conda install -c esri arcgis -y
pip install python-dotenv ultralytics geopandas shapely psycopg2-binary sqlalchemy
```

> **Nota (aprendida 2026-07-16):** instala GeoPandas/Shapely/psycopg2 con
> `pip`, no con `conda install -c conda-forge`. El solver clásico de conda
> puede tardar horas (o no terminar) resolviendo el árbol de dependencias
> de GDAL/PROJ/GEOS; `pip` usa wheels precompiladas y tarda segundos.

Para el módulo 10 (PostGIS), levanta solo ese contenedor:

```bash
docker compose up -d postgis
```

## Setup con Docker

```bash
docker-compose up -d
```

Copia `.env.example` a `.env` y completa las credenciales antes de arrancar.

---

## Flujo Git del proyecto

Cada funcionalidad se desarrolla en su propia rama y se fusiona a `main` al completarse:

```bash
git checkout -b feature/nombre-funcionalidad
# ... desarrollo ...
git add .
git commit -m "feat: descripción clara de lo que hace"
git checkout main
git merge feature/nombre-funcionalidad
git push origin main
```

---

## Aprendizaje

Proyecto desarrollado como formación intensiva en GIS + Computer Vision aplicada a infraestructuras urbanas.
