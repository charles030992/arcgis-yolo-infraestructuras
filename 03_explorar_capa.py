from arcgis.gis import GIS
from arcgis.features import FeatureLayer

gis = GIS()

# Buscamos una capa publica de infraestructuras de carreteras en España
print("=== Buscando capas de infraestructuras ===")
resultados = gis.content.search("carreteras España", item_type="Feature Service", max_items=5)
for i, item in enumerate(resultados):
    print(f"[{i}] {item.title}")
    print(f"    ID: {item.id}")
    print(f"    URL: {item.url}\n")

# Cogemos el primero y exploramos su estructura
if resultados:
    item = resultados[0]
    print(f"=== Explorando: {item.title} ===")

    capa = FeatureLayer(item.url + "/0")
    propiedades = capa.properties

    print(f"Tipo de geometria : {propiedades.geometryType}")
    print(f"Sistema de coordenadas: {propiedades.get('sourceSpatialReference', {}).get('latestWkid', 'ver abajo')}")
    print(f"Numero de campos  : {len(propiedades.fields)}")

    print("\nCampos disponibles (atributos de cada feature):")
    for campo in propiedades.fields[:8]:
        print(f"  - {campo['name']:30} ({campo['type']})")

    print("\nConsultando los primeros 3 registros...")
    features = capa.query(where="1=1", out_fields="*", result_record_count=3)
    for f in features.features:
        print(f"  Atributos: {dict(list(f.attributes.items())[:4])}")
        if f.geometry:
            print(f"  Geometria: {list(f.geometry.items())[:2]}")
