"""
07_yolo_deteccion.py — Detección de objetos con YOLOv8
=======================================================
Diseñado para Google Colab, también funciona en local.

¿Qué es YOLO?
  YOLO significa "You Only Look Once". Es una red neuronal de detección
  de objetos que analiza la imagen completa en una SOLA pasada, lo que
  lo hace extremadamente rápido comparado con métodos anteriores que
  dividían la imagen en regiones y las analizaban por separado.

  Versiones disponibles (de menor a mayor precisión y tiempo):
    yolov8n.pt  — nano   (~6 MB,  más rápido)
    yolov8s.pt  — small
    yolov8m.pt  — medium
    yolov8l.pt  — large
    yolov8x.pt  — extra  (~136 MB, más preciso)

  Usamos 'n' (nano) porque es suficiente para aprender y probar.

¿Qué es COCO?
  El modelo viene preentrenado en el dataset COCO (Common Objects in
  Context), con 80 clases de objetos del mundo real: personas, coches,
  semáforos, señales de tráfico, etc. — clases muy útiles para
  inspección de infraestructuras urbanas.

Instalación en Google Colab (ejecutar en la primera celda):
    !pip install ultralytics requests pillow
"""

# ================================================================
# BLOQUE 1: Importaciones
# ================================================================

import csv
import json
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image

# ultralytics es el paquete oficial de YOLOv8.
# Incluye el modelo, las utilidades de visualización y la descarga
# automática de pesos preentrenados.
from ultralytics import YOLO
from ultralytics.utils import ASSETS  # carpeta con imágenes de muestra incluidas en el paquete

print("=" * 60)
print("Script 07 — Detección de infraestructuras con YOLOv8")
print("=" * 60)


# ================================================================
# BLOQUE 2: Cargar el modelo
# ================================================================
# Al instanciar YOLO("yolov8n.pt"), ocurre lo siguiente:
#   1. Si el archivo ya está en caché local, lo carga directamente.
#   2. Si no, lo descarga automáticamente desde los servidores de
#      Ultralytics (~6 MB para la versión nano).
#
# Los "pesos" (weights) son los valores numéricos de las conexiones
# entre neuronas que el modelo aprendió durante el entrenamiento.

print("\n[BLOQUE 2] Cargando modelo YOLOv8n...")
print("  (Si es la primera vez, se descargará ~6 MB — normal)")
modelo = YOLO("yolov8n.pt")
print("  Modelo cargado correctamente.")

# Mostrar las clases relevantes para infraestructura urbana
CLASES_INFRAESTRUCTURA = {
    "traffic light", "stop sign", "car", "truck", "bus",
    "motorcycle", "bicycle", "person", "fire hydrant"
}

print(f"\n  Clases totales del modelo (COCO): {len(modelo.names)}")
print("  Clases de interés para infraestructura urbana:")
for id_clase, nombre in sorted(modelo.names.items()):
    if nombre in CLASES_INFRAESTRUCTURA:
        print(f"    [{id_clase:2d}] {nombre}")


# ================================================================
# BLOQUE 3: Imágenes de prueba con infraestructura urbana
# ================================================================
# En un proyecto real estas serán fotos tomadas en campo:
# drones, cámaras de inspección, móvil, etc.
#
# Usamos las imágenes de muestra incluidas en el paquete ultralytics (ASSETS).
# ASSETS es una ruta dentro del paquete instalado — siempre están disponibles,
# sin descargas externas ni problemas de permisos (403, firewall, etc.).
#
# En el proyecto real estas serán fotos tomadas en campo:
# drones, cámaras de inspección, fotos de móvil, etc.
# Para añadirlas, usa "ruta_local" apuntando a tu archivo.

imagenes_prueba = [
    {
        "nombre": "calle_autobus",
        "ruta_local": str(ASSETS / "bus.jpg"),
        "descripcion": "Calle urbana con autobús y peatones"
    },
    {
        "nombre": "personas_exterior",
        "ruta_local": str(ASSETS / "zidane.jpg"),
        "descripcion": "Personas en espacio exterior"
    },
    {
        "nombre": "bus_con_gps",
        "ruta_local": "fotos_prueba/bus_con_gps.jpg",
        "descripcion": "Prueba: bus.jpg con GPS EXIF inyectado (Barcelona) para validar el script 08"
    },
    # Cuando tengas fotos propias de infraestructuras, añádelas así:
    # {
    #     "nombre": "farola_sector_norte",
    #     "ruta_local": "/content/mi_foto.jpg",   # ruta en Colab tras subir el archivo
    #     "descripcion": "Inspección farola — sector norte"
    # },
]

# Carpeta donde guardaremos las imágenes descargadas y los resultados
carpeta_resultados = Path("resultados_yolo")
carpeta_resultados.mkdir(exist_ok=True)


# ================================================================
# BLOQUE 4: Descargar imágenes desde URL
# ================================================================

def descargar_imagen(url: str, ruta_destino: Path) -> bool:
    """
    Descarga una imagen desde una URL y la guarda en disco.
    Retorna True si tuvo éxito, False si hubo algún error.
    """
    try:
        # Sin cabecera User-Agent, servidores como Wikipedia devuelven 403 Forbidden
        # porque bloquean peticiones que no se identifican como un navegador.
        # Añadimos esta cabecera para que el servidor nos trate como petición legítima.
        headers = {"User-Agent": "Mozilla/5.0 (compatible; YOLO-infraestructuras/1.0)"}
        # Hacemos una petición HTTP GET con timeout de 15 segundos
        respuesta = requests.get(url, timeout=15, headers=headers)
        # raise_for_status() lanza una excepción si el servidor devuelve error (404, 500...)
        respuesta.raise_for_status()
        # Convertimos los bytes recibidos en una imagen y la guardamos
        img = Image.open(BytesIO(respuesta.content)).convert("RGB")
        img.save(ruta_destino)
        return True
    except Exception as e:
        print(f"    ERROR: {e}")
        return False


print("\n[BLOQUE 4] Descargando imágenes de prueba...")
imagenes_disponibles = []

for img_info in imagenes_prueba:
    print(f"  → {img_info['descripcion']}...", end=" ")

    # Si ya tiene ruta local (imagen propia), la usamos directamente
    if "ruta_local" in img_info:
        ruta = Path(img_info["ruta_local"])
        if ruta.exists():
            print("OK (local)")
            imagenes_disponibles.append({**img_info, "ruta_procesada": str(ruta)})
        else:
            print(f"NO ENCONTRADA en {ruta}")
        continue

    # Si tiene URL, la descargamos
    ruta = carpeta_resultados / f"{img_info['nombre']}_original.jpg"
    if descargar_imagen(img_info["url"], ruta):
        print("OK")
        imagenes_disponibles.append({**img_info, "ruta_procesada": str(ruta)})
    else:
        print("OMITIDA (continuamos con las demás)")

print(f"\n  Imágenes listas para analizar: {len(imagenes_disponibles)}")


# ================================================================
# BLOQUE 5: Inferencia — detectar objetos
# ================================================================
# "Inferencia" es el proceso de pasar datos por el modelo entrenado
# para obtener predicciones. Se diferencia del "entrenamiento" en que
# aquí solo usamos el modelo, no lo modificamos.
#
# El modelo devuelve, para cada objeto detectado:
#   - Clase: qué tipo de objeto es (coche, persona, semáforo...)
#   - Confianza: probabilidad de que la detección sea correcta (0-1)
#   - Bounding box: coordenadas del rectángulo que rodea al objeto
#
# Parámetros importantes:
#   conf  — umbral mínimo de confianza. Descartamos detecciones por
#            debajo de este valor. 0.35 = mínimo 35% de confianza.
#   iou   — umbral para NMS (Non-Maximum Suppression). Cuando varios
#            bounding boxes detectan el mismo objeto, el NMS elimina
#            los redundantes. IoU mide cuánto se solapan dos cajas.

print("\n[BLOQUE 5] Ejecutando detección con YOLOv8n...")

CONFIANZA_MINIMA = 0.35
todas_detecciones = []

for img_info in imagenes_disponibles:
    print(f"\n  --- {img_info['descripcion']} ---")

    resultados = modelo.predict(
        source=img_info["ruta_procesada"],
        conf=CONFIANZA_MINIMA,
        iou=0.45,
        verbose=False,  # silenciamos el log interno de ultralytics
    )

    # predict() siempre devuelve una lista (puede procesar lotes de imágenes).
    # Como pasamos una sola imagen, tomamos el primer elemento.
    resultado = resultados[0]
    cajas = resultado.boxes

    if len(cajas) == 0:
        print("  Sin detecciones con la confianza mínima establecida.")
        continue

    print(f"  {len(cajas)} objeto(s) detectado(s):")

    for caja in cajas:
        # xyxy = coordenadas del bounding box:
        #   x1,y1 = esquina superior izquierda
        #   x2,y2 = esquina inferior derecha
        x1, y1, x2, y2 = [round(v, 1) for v in caja.xyxy[0].tolist()]

        confianza   = float(caja.conf[0])
        id_clase    = int(caja.cls[0])
        nombre_clase = modelo.names[id_clase]
        ancho_px    = round(x2 - x1, 1)
        alto_px     = round(y2 - y1, 1)

        # Marcamos con ★ las clases relevantes para infraestructura
        marca = "★" if nombre_clase in CLASES_INFRAESTRUCTURA else " "

        print(f"  {marca} {nombre_clase:<20} "
              f"confianza: {confianza:.0%}  "
              f"bbox: ({x1},{y1})→({x2},{y2})  "
              f"tamaño: {ancho_px}×{alto_px}px")

        todas_detecciones.append({
            "imagen"            : img_info["nombre"],
            "descripcion_imagen": img_info["descripcion"],
            "ruta_imagen"       : img_info["ruta_procesada"],
            "clase"             : nombre_clase,
            "id_clase"          : id_clase,
            "es_infraestructura": nombre_clase in CLASES_INFRAESTRUCTURA,
            "confianza"         : round(confianza, 4),
            "x1"                : x1,
            "y1"                : y1,
            "x2"                : x2,
            "y2"                : y2,
            "ancho_px"          : ancho_px,
            "alto_px"           : alto_px,
        })

    # --- Guardar imagen con bounding boxes dibujados ---
    # result.plot() devuelve un array NumPy (BGR) con las cajas pintadas.
    # Lo convertimos a RGB para guardarlo correctamente con PIL.
    imagen_anotada = resultado.plot()
    imagen_pil = Image.fromarray(imagen_anotada[..., ::-1])  # BGR → RGB
    ruta_anotada = carpeta_resultados / f"{img_info['nombre']}_anotada.jpg"
    imagen_pil.save(ruta_anotada)
    print(f"  Imagen anotada guardada: {ruta_anotada}")


# ================================================================
# BLOQUE 6: Guardar resultados en CSV y JSON
# ================================================================
# Guardamos en dos formatos:
#   CSV  — fácil de abrir en Excel para explorar los datos
#   JSON — formato estructurado que usaremos en el Script 08
#           para enviar las detecciones a ArcGIS Online

print("\n[BLOQUE 6] Guardando resultados...")

if todas_detecciones:
    campos_csv = [
        "imagen", "descripcion_imagen", "ruta_imagen", "clase", "id_clase",
        "es_infraestructura", "confianza",
        "x1", "y1", "x2", "y2", "ancho_px", "alto_px"
    ]

    ruta_csv = carpeta_resultados / "detecciones.csv"
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos_csv)
        writer.writeheader()
        writer.writerows(todas_detecciones)
    print(f"  CSV  → {ruta_csv}")

    ruta_json = carpeta_resultados / "detecciones.json"
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(todas_detecciones, f, ensure_ascii=False, indent=2)
    print(f"  JSON → {ruta_json}")

else:
    print("  No hay detecciones que guardar.")


# ================================================================
# BLOQUE 7: Resumen final
# ================================================================

print("\n" + "=" * 60)
print("RESUMEN")
print("=" * 60)

if todas_detecciones:
    conteo = {}
    for det in todas_detecciones:
        conteo[det["clase"]] = conteo.get(det["clase"], 0) + 1

    total = len(todas_detecciones)
    confianza_media = sum(d["confianza"] for d in todas_detecciones) / total

    print(f"\n  Imágenes analizadas : {len(imagenes_disponibles)}")
    print(f"  Total de detecciones: {total}")
    print(f"  Confianza media     : {confianza_media:.0%}")
    print(f"\n  Objetos detectados por clase (★ = relevante para infraestructura):")

    for clase, n in sorted(conteo.items(), key=lambda x: -x[1]):
        marca = "★" if clase in CLASES_INFRAESTRUCTURA else " "
        print(f"    {marca} {clase:<25} {n:>3} detección(es)")

    print(f"\n  Archivos generados en: {carpeta_resultados}/")
    print("    ├── *_original.jpg     — imágenes descargadas")
    print("    ├── *_anotada.jpg      — imágenes con bounding boxes")
    print("    ├── detecciones.csv    — tabla de resultados (Excel)")
    print("    └── detecciones.json   — datos para Script 08 (ArcGIS)")

else:
    print("  No se realizaron detecciones.")

print("\n✓ Script 07 completado.")
print("  El JSON generado es la entrada del Script 08: pipeline YOLO → ArcGIS.")
