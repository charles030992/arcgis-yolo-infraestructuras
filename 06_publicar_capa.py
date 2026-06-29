import csv
import os
from dotenv import load_dotenv
from arcgis.gis import GIS

load_dotenv()

# --- BLOQUE 1: Crear datos de ejemplo ---
# Simulamos 5 activos de infraestructura con coordenadas reales de Madrid

datos = [
    {"nombre": "Señal_001", "tipo": "señal_trafico", "estado": "bueno",     "latitud": 40.4168, "longitud": -3.7038},
    {"nombre": "Señal_002", "tipo": "señal_trafico", "estado": "deteriorado","latitud": 40.4195, "longitud": -3.7012},
    {"nombre": "Farola_001", "tipo": "alumbrado",    "estado": "bueno",     "latitud": 40.4150, "longitud": -3.7055},
    {"nombre": "Farola_002", "tipo": "alumbrado",    "estado": "averiado",  "latitud": 40.4210, "longitud": -3.6998},
    {"nombre": "Señal_003", "tipo": "señal_obra",    "estado": "bueno",     "latitud": 40.4180, "longitud": -3.7070},
]

ruta_csv = "activos_infraestructura.csv"

with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["nombre", "tipo", "estado", "latitud", "longitud"])
    writer.writeheader()
    writer.writerows(datos)

print(f"CSV creado con {len(datos)} activos: {ruta_csv}")

# --- BLOQUE 2: Conectar a ArcGIS Online y subir el CSV ---

print("\nConectando a ArcGIS Online...")
gis = GIS(
    "https://www.arcgis.com",
    client_id=os.getenv("ARCGIS_CLIENT_ID")
)
print(f"Conectado como: {gis.users.me.username}")

# Propiedades del item que vamos a subir
propiedades_item = {
    "title": "Activos Infraestructura - Test",
    "type": "CSV",
    "tags": "infraestructura, activos, test, python",
    "description": "Capa de prueba publicada desde Python con coordenadas de activos urbanos"
}

print("\nSubiendo CSV a ArcGIS Online...")
item_csv = gis.content.add(propiedades_item, data=ruta_csv)
print(f"CSV subido — ID: {item_csv.id}")

# --- BLOQUE 3: Publicar como Feature Layer ---
# Indicamos qué columnas contienen las coordenadas

parametros_publicacion = {
    "locationType": "coordinates",
    "latitudeFieldName": "latitud",
    "longitudeFieldName": "longitud",
    "coordinateFieldType": "LatLong"
}

print("\nPublicando como Feature Layer...")
feature_layer = item_csv.publish(publish_parameters=parametros_publicacion)

print(f"\n✓ Capa publicada correctamente")
print(f"  Título : {feature_layer.title}")
print(f"  ID     : {feature_layer.id}")
print(f"  URL    : https://www.arcgis.com/home/item.html?id={feature_layer.id}")

# Limpieza: borramos el CSV local una vez subido
os.remove(ruta_csv)
print(f"\nCSV local eliminado.")
