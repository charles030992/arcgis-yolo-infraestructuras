"""
Módulo 11 — Rasterio: bandas, resolución, recorte y cálculo de NDVI.

Genera una imagen satelital sintética de 2 bandas (RED, NIR) sobre la misma
zona de referencia que 09_analisis_espacial.py (Puerta del Sol, Madrid),
calcula el NDVI y lo muestrea en puntos georreferenciados como si fueran
detecciones YOLO de los scripts 08/09. No hay imagen satelital real
disponible: se simula un parche de vegetación sana en el centro para poder
verificar que el NDVI distingue vegetación de suelo/urbano.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.transform import from_origin, rowcol
from rasterio.windows import Window

# Mismo punto de referencia que el script 09, para que el raster caiga en la
# misma zona que las detecciones YOLO georreferenciadas.
CENTRO_ZONA = (40.4168, -3.7038)  # (lat, lon)
CRS_GEOGRAFICO = "EPSG:4326"

# Rejilla de 100x100 píxeles. Resolución en grados (0.0001° ≈ 11 m en la
# latitud de Madrid) — suficiente para una demo, no para medir con precisión.
FILAS, COLUMNAS = 100, 100
RESOLUCION_GRADOS = 0.0001

RUTA_IMAGEN_SATELITE = Path("imagen_satelite_sintetica.tif")
RUTA_NDVI = Path("ndvi_resultado.tif")


def generar_imagen_satelite_sintetica():
    """Crea un GeoTIFF de 2 bandas (RED, NIR) con un parche de vegetación."""
    rng = np.random.default_rng(seed=42)

    red = rng.uniform(0.15, 0.25, size=(FILAS, COLUMNAS)).astype("float32")
    nir = rng.uniform(0.15, 0.25, size=(FILAS, COLUMNAS)).astype("float32")

    centro_fila, centro_col = FILAS // 2, COLUMNAS // 2
    fila, columna = np.ogrid[:FILAS, :COLUMNAS]
    distancia_centro = np.sqrt((fila - centro_fila) ** 2 + (columna - centro_col) ** 2)
    mascara_vegetacion = distancia_centro <= 20

    red[mascara_vegetacion] = rng.uniform(0.04, 0.08, size=mascara_vegetacion.sum())
    nir[mascara_vegetacion] = rng.uniform(0.45, 0.60, size=mascara_vegetacion.sum())

    origen_lon = CENTRO_ZONA[1] - (COLUMNAS / 2) * RESOLUCION_GRADOS
    origen_lat = CENTRO_ZONA[0] + (FILAS / 2) * RESOLUCION_GRADOS
    transform = from_origin(origen_lon, origen_lat, RESOLUCION_GRADOS, RESOLUCION_GRADOS)

    perfil = {
        "driver": "GTiff",
        "height": FILAS,
        "width": COLUMNAS,
        "count": 2,
        "dtype": "float32",
        "crs": CRS_GEOGRAFICO,
        "transform": transform,
    }

    with rasterio.open(RUTA_IMAGEN_SATELITE, "w", **perfil) as destino:
        destino.write(red, 1)
        destino.write(nir, 2)
        destino.set_band_description(1, "RED")
        destino.set_band_description(2, "NIR")

    print(f"Imagen satelital sintética generada: {RUTA_IMAGEN_SATELITE}")


def inspeccionar_raster(ruta):
    """Metadatos básicos de un raster: bandas, resolución, CRS, extent."""
    with rasterio.open(ruta) as src:
        resolucion_x, resolucion_y = src.res
        print(f"\nMetadatos de {ruta}:")
        print(f"  Bandas: {src.count}")
        print(f"  Tamaño: {src.width} x {src.height} píxeles")
        print(f"  Resolución de píxel: {resolucion_x:.6f}° x {resolucion_y:.6f}°")
        print(f"  CRS: {src.crs}")
        print(f"  Extent (bounds): {src.bounds}")
        print(f"  Tipo de dato: {src.dtypes[0]}")


def calcular_ndvi():
    """NDVI = (NIR - RED) / (NIR + RED). Rango [-1, 1]."""
    with rasterio.open(RUTA_IMAGEN_SATELITE) as src:
        red = src.read(1)
        nir = src.read(2)
        perfil = src.profile

    ndvi = ((nir - red) / (nir + red)).astype("float32")

    perfil.update(count=1, dtype="float32")
    with rasterio.open(RUTA_NDVI, "w", **perfil) as destino:
        destino.write(ndvi, 1)
        destino.set_band_description(1, "NDVI")

    print(f"\nNDVI calculado. Rango: [{ndvi.min():.3f}, {ndvi.max():.3f}]")
    print(f"NDVI guardado: {RUTA_NDVI}")


def recortar_subzona(ruta, filas_ventana=40, columnas_ventana=40):
    """Recorte por ventana (windowed read) centrado en el propio raster."""
    with rasterio.open(ruta) as src:
        fila_inicio = (src.height - filas_ventana) // 2
        columna_inicio = (src.width - columnas_ventana) // 2
        ventana = Window(columna_inicio, fila_inicio, columnas_ventana, filas_ventana)
        recorte = src.read(1, window=ventana)

    print(f"\nRecorte de {filas_ventana}x{columnas_ventana} píxeles del centro:")
    print(f"  NDVI medio en el recorte: {recorte.mean():.3f}")


def interpretar_ndvi(valor):
    if valor > 0.3:
        return "vegetación"
    if valor > 0.1:
        return "vegetación escasa"
    return "suelo/urbano"


def muestrear_en_puntos_deteccion(puntos):
    """
    Muestrea NDVI en puntos (lat, lon), como si fueran detecciones YOLO
    georreferenciadas (mismo formato que 08_pipeline_completo.py / 09).
    Caso real: "¿qué cobertura vegetal hay donde se detectó cada activo?".
    """
    coordenadas = [(lon, lat) for lat, lon in puntos]

    with rasterio.open(RUTA_NDVI) as src:
        valores = [muestra[0] for muestra in src.sample(coordenadas)]

    print("\nNDVI muestreado en puntos de detección:")
    for (lat, lon), ndvi_punto in zip(puntos, valores):
        print(f"  ({lat:.4f}, {lon:.4f}) -> NDVI={ndvi_punto:.3f} ({interpretar_ndvi(ndvi_punto)})")


def visualizar_ndvi(puntos, ruta_salida=Path("ndvi_visualizacion.png")):
    """
    Pinta el raster NDVI como imagen (verde=vegetación, rojo=suelo/urbano) y
    marca encima los puntos de detección muestreados. Los .tif no se pueden
    ver como texto ni abrir con un visor normal de imágenes; esto es el
    equivalente raster de los mapas Folium (.html) que ya generan 05/09.
    """
    with rasterio.open(RUTA_NDVI) as src:
        ndvi = src.read(1)
        transform = src.transform

    fig, ax = plt.subplots(figsize=(6, 6))
    imagen = ax.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    fig.colorbar(imagen, ax=ax, label="NDVI")
    ax.set_title("NDVI sintético — zona Puerta del Sol (ejemplo)")
    ax.set_xlabel("columna (píxel)")
    ax.set_ylabel("fila (píxel)")

    for lat, lon in puntos:
        fila, columna = rowcol(transform, lon, lat)
        ax.plot(columna, fila, marker="x", color="black", markersize=10, markeredgewidth=2)

    fig.savefig(ruta_salida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nVisualización guardada: {ruta_salida}")


if __name__ == "__main__":
    generar_imagen_satelite_sintetica()
    inspeccionar_raster(RUTA_IMAGEN_SATELITE)

    calcular_ndvi()
    inspeccionar_raster(RUTA_NDVI)

    recortar_subzona(RUTA_NDVI)

    puntos_deteccion = [
        CENTRO_ZONA,
        (CENTRO_ZONA[0] + 0.0005, CENTRO_ZONA[1] + 0.0005),
        (CENTRO_ZONA[0] - 0.003, CENTRO_ZONA[1] - 0.003),
    ]
    muestrear_en_puntos_deteccion(puntos_deteccion)
    visualizar_ndvi(puntos_deteccion)
