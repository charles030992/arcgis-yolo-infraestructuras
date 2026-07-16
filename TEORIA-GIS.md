# Teoría GIS — notas de repaso

Documento vivo de conceptos teóricos que van apareciendo mientras construimos
el proyecto. Objetivo: tener una referencia rápida para repasar antes de una
entrevista o cuando se nos olvide "por qué hacíamos esto así". Se amplía en
cada sesión, no se reescribe.

---

## 1. Las tres librerías que hay debajo de todo (GDAL, PROJ, GEOS)

Cuando instalamos `geopandas`, en realidad estamos instalando un paquete
Python que por debajo se apoya en tres librerías C/C++ mucho más antiguas y
usadas por *todo* el ecosistema GIS (QGIS, ArcGIS, PostGIS, GDAL...). No son
cosa de GeoPandas — son la base común de todo el sector.

| Librería | Qué hace | Analogía | Quién la usa por debajo |
|---|---|---|---|
| **GDAL/OGR** | Lee y escribe formatos geoespaciales (Shapefile, GeoJSON, GeoTIFF, CSV georreferenciado...) | El "traductor de formatos universal" | GeoPandas (`gpd.read_file`), Rasterio, QGIS, ArcGIS por dentro |
| **PROJ** | Convierte coordenadas de un sistema de referencia a otro (CRS) | El "cambio de idioma de coordenadas" | GeoPandas (`.to_crs()`), GDAL lo usa internamente |
| **GEOS** | Hace las operaciones geométricas puras: buffer, intersección, distancia, contiene/está dentro | La "calculadora de formas" | Shapely (es un envoltorio Python de GEOS), PostGIS |

**Regla mental:** GDAL lee/escribe, PROJ traduce coordenadas, GEOS calcula
geometría. Shapely = GEOS en Python. GeoPandas = pandas + Shapely + GDAL +
PROJ, todo integrado.

**¿Se piden en ofertas?** Sí, pero depende del perfil:
- Roles de **analista GIS / GIS Developer backend / Geospatial Data
  Engineer** las mencionan explícitamente ("GDAL/OGR", "PostGIS", a veces
  "GEOS/PROJ").
- Roles más de **frontend GIS** (como la oferta de COTESA que ya
  registramos) no las piden — ahí piden ArcGIS Maps SDK for JS, Angular.
- Aparecen poco en el nombre exacto ("GEOS") porque se dan por hecho al
  pedir "GeoPandas" o "PostGIS" — pero si en una entrevista técnica preguntan
  "¿qué pasa por debajo cuando haces un buffer?", esta es la respuesta.

---

## 2. CRS: sistema de referencia de coordenadas — por qué importa

Hay dos grandes familias de CRS:

- **Geográfico** (ej. `EPSG:4326`, WGS84 — el de GPS/lat-lon de toda la
  vida): las unidades son **grados**. Es el que usan ArcGIS Online, EXIF de
  fotos, Google Maps.
- **Proyectado** (ej. `EPSG:25830`, ETRS89/UTM 30N — el oficial para España
  peninsular): las unidades son **metros**. Aplasta la esfera terrestre en
  un plano para una zona concreta.

**El error clásico (anotado hoy, 2026-07-16):** hacer un `.buffer(300)`
directamente sobre datos en `EPSG:4326` pensando en "300 metros". En
grados, 300 no significa nada consistente — un grado de longitud mide
distinto en el ecuador que en Madrid, y además el resultado se deforma. El
buffer se ha calculado en grados de arco, no en metros reales.

**Regla práctica:** si vas a medir distancias, hacer buffers o calcular
áreas → reproyecta primero a un CRS métrico adecuado a la zona
(`.to_crs("EPSG:25830")` para España peninsular). Si solo vas a
mostrar el punto en un mapa o guardarlo en ArcGIS → `EPSG:4326` está bien.

Esto es exactamente lo primero que un revisor técnico miraría en un PR de
geoprocesamiento: si mides en grados sin darte cuenta, el resultado parece
funcionar (no da error) pero es matemáticamente incorrecto — es un bug
silencioso, no un crash.

---

## 3. GeoDataFrame y la columna `geometry`

Una tabla con columnas `latitud, longitud` sueltas es, para el ordenador,
exactamente igual de "espacial" que una tabla con `temperatura, humedad`:
dos números cualquiera, sin significado geométrico.

La columna `geometry` de un `GeoDataFrame` **activa** esos números como
objetos geométricos reales (`Point`, `Polygon`, `Line`), con reglas
matemáticas definidas: distancia, si un punto está dentro de un polígono, si
dos formas se cruzan, etc. No es tanto "traducir a un idioma que entienda
otro mapa" como **dar de alta los números como objetos con los que GEOS
sabe operar**. A partir de ahí, ya puedes preguntarle a la tabla cosas que
antes no podías: "¿qué filas caen dentro de esta zona?", "¿a qué distancia
está cada fila de este punto?".

Analogía corregida: no es un traductor entre mapas — es más parecido a
convertir dos columnas de texto en un objeto `datetime`: antes solo tenías
números/strings, después puedes preguntar "¿cuántos días de diferencia
hay?" porque el objeto ya sabe las reglas del calendario. Con `geometry`
pasa lo mismo pero con las reglas de la geometría en vez del calendario.

---

## 4. Spatial Join (`sjoin`)

Un `JOIN` normal (SQL, pandas `merge`) junta dos tablas comparando el
**valor** de una columna compartida (ej. `cliente_id` en ambas tablas).

Un **spatial join** (`gpd.sjoin`) junta dos tablas comparando una
**relación geométrica** entre sus geometrías, no un valor de columna. No
existe una columna común — la "clave" es "¿este punto está dentro de este
polígono?", calculado sobre la marcha por GEOS para cada combinación.

**Ejemplo paso a paso (el de nuestro script `09_analisis_espacial.py`):**
1. Tabla A: detecciones YOLO (puntos), una fila por detección.
2. Tabla B: zona de obra (un polígono, un buffer circular).
3. `sjoin(A, B, predicate="within")` recorre cada punto de A y le pregunta a
   GEOS: "¿este punto cae dentro de ese polígono de B?".
4. Si la respuesta es sí, la fila de A se queda con el índice (y atributos)
   de la fila de B correspondiente. Si es no, queda vacío (`NaN`).
5. Con eso construimos una columna booleana `dentro_zona_obra`.

**Ejemplo de la vida real (más claro que "zona de obra"):** tienes un Excel
de 10.000 direcciones de clientes (lat/lon) y un shapefile con los polígonos
de los distritos postales de Madrid. No hay ninguna columna común entre las
dos tablas — el cliente no tiene "distrito_id" apuntado. `sjoin` recorre
cada cliente y comprueba geométricamente en qué polígono de distrito cae,
y te devuelve la tabla de clientes con el distrito ya asignado. Es la forma
estándar de "etiquetar geográficamente" datos que no vienen etiquetados.

**Predicados más comunes:** `within` (A dentro de B), `intersects` (se
tocan o solapan), `contains` (B dentro de A), `touches` (solo se tocan en el
borde).

**Trampa a vigilar:** las dos tablas del `sjoin` deben estar en el **mismo
CRS**, o el resultado es silenciosamente incorrecto (o directamente lanza
error/warning). Por eso en el script reproyectamos ambas a `EPSG:25830`
antes de cruzarlas.

**Aplicación directa a proyecto de septiembre (Cobertura ITV Madrid):**
mismo patrón exacto — Tabla A = centroides de barrio o direcciones de
vehículos, Tabla B = buffers de cobertura (radio/tiempo de desplazamiento)
alrededor de cada estación ITV. El `sjoin` responde "¿qué barrios/vehículos
quedan cubiertos por qué estación?", que es la base de cualquier análisis
de cobertura de servicio.

---

## 5. Patrón Folium (mapas interactivos) — receta reutilizable

Folium ya ha aparecido en el notebook `05_mapas_interactivos.ipynb` y ahora
en `09_analisis_espacial.py`. El patrón se repite siempre igual:

```python
# 1. Mapa base — centro y zoom inicial
mapa = folium.Map(location=[lat, lon], zoom_start=14)

# 2. Añadir capas una por una, cada una con su .add_to(mapa)
folium.Marker(
    location=[lat, lon],
    popup=folium.Popup("<b>HTML libre aquí</b><br>otro dato", max_width=250),
    icon=folium.Icon(color="red", icon="warning-sign"),
).add_to(mapa)

folium.CircleMarker(               # punto con radio en píxeles, coloreable
    location=[lat, lon], radius=6, color="red", fill=True, fill_opacity=0.8
).add_to(mapa)

folium.Circle(                     # círculo con radio en METROS reales
    location=[lat, lon], radius=300, color="orange", fill=True
).add_to(mapa)

# 3. Iterar sobre datos reales (filas de DataFrame o features de ArcGIS)
#    añadiendo un marcador por fila, normalmente coloreado según algún
#    atributo (ej. dentro/fuera de zona, tipo de detección...)

# 4. Exportar para verlo fuera de Jupyter / compartirlo
mapa.save("archivo.html")
```

**Puntos clave que se olvidan fácil:**
- `Marker`/`CircleMarker` = radio en **píxeles** (estético). `Circle` = radio
  en **metros reales** (para representar buffers/zonas de cobertura).
- Los `Popup` aceptan HTML directo — así se muestran varios atributos al
  hacer clic, no solo un texto plano.
- `location` siempre es `[lat, lon]` en Folium (ojo, no `[lon, lat]` como en
  GeoJSON/Shapely, que usan `(x, y)` = `(lon, lat)`). Fuente típica de bugs
  al mezclar librerías.

---

## Pendiente de anotar aquí más adelante
- PostGIS y las funciones `ST_*` (cuando lleguemos a ese módulo).
- Rasterio / GDAL para raster (bandas, resolución) — aún sin módulo.
- Diferencia `intersects` vs `overlaps` vs `crosses` con ejemplos visuales.
