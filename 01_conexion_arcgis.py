from arcgis.gis import GIS

# Login anonimo - acceso publico sin cuenta
print("=== Conexion anonima (publica) ===")
gis_anonimo = GIS()
print(f"Conectado como: {gis_anonimo.properties.user if hasattr(gis_anonimo.properties, 'user') else 'anonimo'}")

# Buscar contenido publico de ArcGIS para verificar que la conexion funciona
print("\n=== Buscando contenido publico de prueba ===")
resultados = gis_anonimo.content.search("infraestructuras España", max_items=3)
for item in resultados:
    print(f"- {item.title} | Tipo: {item.type}")
