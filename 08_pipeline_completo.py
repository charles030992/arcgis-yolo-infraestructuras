import csv
import json
import os
import time
from pathlib import Path

import piexif
from dotenv import load_dotenv
from arcgis.gis import GIS

load_dotenv()

RUTA_JSON = Path("resultados_yolo/detecciones.json")

# Coordenada de reserva cuando la foto no trae GPS en el EXIF.
# Usamos Puerta del Sol, Madrid, solo como marcador de "sin ubicación real".
COORDENADA_POR_DEFECTO = (40.4168, -3.7038)


def conectar_arcgis():
    gis = GIS(
        os.getenv("ARCGIS_URL"),
        os.getenv("ARCGIS_USERNAME"),
        os.getenv("ARCGIS_PASSWORD"),
    )
    print(f"Conectado — {gis.users.me.username}")
    return gis


def _dms_a_decimal(dms, ref):
    """Convierte (grados, minutos, segundos) en formato EXIF racional a grados decimales."""
    grados, minutos, segundos = dms
    valor = (grados[0] / grados[1]
             + (minutos[0] / minutos[1]) / 60
             + (segundos[0] / segundos[1]) / 3600)
    if ref in (b"S", b"W"):
        valor = -valor
    return valor


def extraer_coordenadas_exif(ruta_foto):
    """Devuelve (lat, lon) si la foto tiene GPS en el EXIF, o None si no lo tiene."""
    try:
        exif_dict = piexif.load(str(ruta_foto))
        gps = exif_dict.get("GPS", {})
        if not gps or piexif.GPSIFD.GPSLatitude not in gps:
            return None
        lat = _dms_a_decimal(gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef])
        lon = _dms_a_decimal(gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef])
        return (lat, lon)
    except Exception:
        return None


def obtener_coordenadas(ruta_foto):
    """Opción 3: EXIF si existe, si no, coordenada por defecto."""
    coords = extraer_coordenadas_exif(ruta_foto)
    if coords:
        print(f"  GPS EXIF encontrado: {coords}")
        return coords, "exif"
    print(f"  Sin GPS EXIF — usando coordenada por defecto {COORDENADA_POR_DEFECTO}")
    return COORDENADA_POR_DEFECTO, "por_defecto"


def cargar_detecciones():
    with open(RUTA_JSON, encoding="utf-8") as f:
        return json.load(f)


def enriquecer_con_coordenadas(detecciones):
    # Las detecciones de una misma foto comparten ubicación: leemos el EXIF
    # una sola vez por imagen, no una vez por detección.
    cache_coordenadas = {}
    filas = []
    for det in detecciones:
        ruta = det["ruta_imagen"]
        if ruta not in cache_coordenadas:
            cache_coordenadas[ruta] = obtener_coordenadas(ruta)
        (lat, lon), origen = cache_coordenadas[ruta]
        filas.append({
            **det,
            "latitud": lat,
            "longitud": lon,
            "origen_coordenada": origen,
        })
    return filas


def guardar_csv(filas, ruta_csv):
    campos = list(filas[0].keys())
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


def publicar_en_arcgis(gis, ruta_csv, sufijo):
    # El nombre del SERVICIO (a diferencia del título del item) debe ser único
    # en toda la organización — reutilizamos el mismo sufijo que ya lleva el
    # nombre de archivo del CSV, para que todo quede trazable a una misma ejecución.
    nombre_servicio = f"Detecciones_YOLO_Infraestructuras_{sufijo}"

    propiedades_item = {
        "title": f"Detecciones YOLO - Infraestructuras ({sufijo})",
        "type": "CSV",
        "tags": "infraestructura, yolo, deteccion, python",
        "description": "Detecciones de YOLOv8 georreferenciadas (EXIF o coordenada por defecto)",
    }
    item_csv = gis.content.add(propiedades_item, data=str(ruta_csv))
    print(f"CSV subido — ID: {item_csv.id}")

    parametros_publicacion = {
        "name": nombre_servicio,
        "locationType": "coordinates",
        "latitudeFieldName": "latitud",
        "longitudeFieldName": "longitud",
        "coordinateFieldType": "LatLong",
    }
    feature_layer = item_csv.publish(publish_parameters=parametros_publicacion)
    print("\n✓ Capa publicada correctamente")
    print(f"  Título : {feature_layer.title}")
    print(f"  ID     : {feature_layer.id}")
    print(f"  URL    : https://www.arcgis.com/home/item.html?id={feature_layer.id}")
    return feature_layer


if __name__ == "__main__":
    detecciones = cargar_detecciones()
    print(f"{len(detecciones)} detecciones cargadas de {RUTA_JSON}")

    filas = enriquecer_con_coordenadas(detecciones)

    sufijo = time.strftime("%Y%m%d_%H%M%S")
    ruta_csv = Path(f"detecciones_georreferenciadas_{sufijo}.csv")
    guardar_csv(filas, ruta_csv)
    print(f"CSV generado: {ruta_csv}")

    print("\nConectando a ArcGIS Online...")
    gis = conectar_arcgis()

    print("\nSubiendo y publicando...")
    publicar_en_arcgis(gis, ruta_csv, sufijo)
