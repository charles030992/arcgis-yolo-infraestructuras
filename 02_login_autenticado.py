from arcgis.gis import GIS
from dotenv import load_dotenv
import os

load_dotenv()
client_id = os.getenv("ARCGIS_CLIENT_ID")

print("Abriendo navegador para login con GitHub...")
print("Logate con tu cuenta de GitHub cuando se abra el browser.\n")

gis = GIS("https://www.arcgis.com", client_id=client_id)

print(f"Conectado como : {gis.users.me.username}")
print(f"Nombre         : {gis.users.me.full_name}")
print(f"Rol            : {gis.users.me.role}")

print("\n=== Tu contenido en ArcGIS Online ===")
mi_contenido = gis.content.search(f"owner:{gis.users.me.username}", max_items=10)
if mi_contenido:
    for item in mi_contenido:
        print(f"- {item.title} | {item.type}")
else:
    print("(cuenta nueva, sin contenido aun — normal)")
