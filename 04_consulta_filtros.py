from arcgis.gis import GIS
from arcgis.features import FeatureLayer

gis = GIS()

# La misma capa que exploramos: paradas de autobus de Cataluña
URL_CAPA = "https://services1.arcgis.com/nCKYwcSONQTkPA4K/arcgis/rest/services/ParadasInterurbanosBarcelona/FeatureServer/0"
capa = FeatureLayer(URL_CAPA)

# ── 1. CONTAR registros totales (sin traer datos) ──────────────────────────
total = capa.query(where="1=1", return_count_only=True)
print(f"Total de paradas en la capa: {total}")

# ── 2. FILTRO SIMPLE por operador ──────────────────────────────────────────
# SQL equivalente: SELECT * FROM paradas WHERE Operador = 'SAGALÉS'
print("\n=== Paradas del operador SAGALÉS ===")
sagales = capa.query(
    where="Operador = 'SAGALÉS'",
    out_fields="Nombre_de_la_parada, Nombre_de_la_linea, Operador",
    result_record_count=5
)
print(f"Registros encontrados: {sagales.features.__len__()}")
for f in sagales.features:
    a = f.attributes
    print(f"  {a['Nombre_de_la_parada']:45} | Linea: {a['Nombre_de_la_linea']}")

# ── 3. FILTRO CON LIKE (búsqueda parcial) ──────────────────────────────────
# SQL equivalente: SELECT * FROM paradas WHERE Nombre_de_la_parada LIKE '%Barcelona%'
print("\n=== Paradas que contienen 'Barcelona' en el nombre ===")
bcn = capa.query(
    where="Nombre_de_la_parada LIKE '%Barcelona%'",
    out_fields="Nombre_de_la_parada, Operador",
    result_record_count=5
)
print(f"Registros encontrados: {bcn.features.__len__()}")
for f in bcn.features:
    a = f.attributes
    print(f"  {a['Nombre_de_la_parada']:45} | {a['Operador']}")

# ── 4. FILTRO COMBINADO (AND) ──────────────────────────────────────────────
# SQL equivalente: SELECT * FROM paradas WHERE Operador = 'SAGALÉS' AND Nombre_de_la_linea LIKE '%B%'
print("\n=== SAGALÉS con líneas que contienen 'B' ===")
combinado = capa.query(
    where="Operador = 'SAGALÉS' AND Nombre_de_la_linea LIKE '%B%'",
    out_fields="Nombre_de_la_parada, Nombre_de_la_linea",
    result_record_count=5
)
print(f"Registros encontrados: {combinado.features.__len__()}")
for f in combinado.features:
    a = f.attributes
    print(f"  {a['Nombre_de_la_parada']:45} | Linea: {a['Nombre_de_la_linea']}")

# ── 5. TRAER SOLO CAMPOS ESPECÍFICOS + convertir a tabla legible ───────────
print("\n=== Tabla resumen: nombre y operador de 10 paradas ===")
muestra = capa.query(
    where="1=1",
    out_fields="Nombre_de_la_parada, Operador",
    result_record_count=10,
    order_by_fields="OBJECTID ASC"
)
# Convertir a DataFrame de pandas (como harías con SQL + pandas)
df = muestra.sdf
print(df[["Nombre_de_la_parada", "Operador"]].to_string(index=False))
