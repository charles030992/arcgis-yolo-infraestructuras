import time
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

RUTA_CSV = Path("detecciones_georreferenciadas.csv")

# EPSG:4326 = coordenadas GPS (lat/lon) tal cual las da el EXIF/ArcGIS.
# EPSG:25830 = ETRS89 / UTM zona 30N, sistema métrico oficial para España
# peninsular. Todo cálculo de distancias o buffers en metros necesita un CRS
# proyectado como este; en 4326 los "grados" no son una unidad de distancia.
CRS_GEOGRAFICO = "EPSG:4326"
CRS_METRICO = "EPSG:25830"

CENTRO_ZONA_OBRA = (40.4168, -3.7038)  # Puerta del Sol, Madrid
RADIO_ZONA_OBRA_METROS = 300


def cargar_detecciones(ruta_csv):
    df = pd.read_csv(ruta_csv)
    geometria = [Point(lon, lat) for lat, lon in zip(df["latitud"], df["longitud"])]
    return gpd.GeoDataFrame(df, geometry=geometria, crs=CRS_GEOGRAFICO)


def crear_zona_obra(centro, radio_metros):
    lat, lon = centro
    punto = gpd.GeoSeries([Point(lon, lat)], crs=CRS_GEOGRAFICO)
    circulo_metrico = punto.to_crs(CRS_METRICO).buffer(radio_metros)
    return gpd.GeoDataFrame(geometry=circulo_metrico, crs=CRS_METRICO)


def analizar_zona(gdf_detecciones, gdf_zona):
    detecciones_metrico = gdf_detecciones.to_crs(CRS_METRICO)
    centro_zona = gdf_zona.geometry.centroid.iloc[0]

    dentro = gpd.sjoin(detecciones_metrico, gdf_zona, how="left", predicate="within")
    gdf_detecciones["dentro_zona_obra"] = dentro["index_right"].notna().values
    gdf_detecciones["distancia_zona_metros"] = detecciones_metrico.distance(centro_zona).round(1).values
    return gdf_detecciones


def resumen_por_clase(gdf):
    resumen = (
        gdf.groupby("clase")["dentro_zona_obra"]
        .agg(total="count", dentro="sum")
        .assign(fuera=lambda t: t["total"] - t["dentro"])
    )
    print("\nResumen por clase (dentro/fuera de la zona de obra):")
    print(resumen.to_string())


def guardar_mapa(gdf, centro, radio_metros, ruta_html):
    mapa = folium.Map(location=list(centro), zoom_start=16)

    folium.Circle(
        location=list(centro),
        radius=radio_metros,
        color="orange",
        fill=True,
        fill_opacity=0.1,
        popup=f"Zona de obra (radio {radio_metros} m)",
    ).add_to(mapa)

    for _, fila in gdf.iterrows():
        color = "red" if fila["dentro_zona_obra"] else "gray"
        folium.CircleMarker(
            location=[fila["latitud"], fila["longitud"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=(
                f"<b>{fila['clase']}</b><br>"
                f"Confianza: {fila['confianza']:.2f}<br>"
                f"Distancia al centro: {fila['distancia_zona_metros']} m"
            ),
        ).add_to(mapa)

    mapa.save(str(ruta_html))
    print(f"Mapa guardado: {ruta_html}")


if __name__ == "__main__":
    gdf = cargar_detecciones(RUTA_CSV)
    print(f"{len(gdf)} detecciones cargadas de {RUTA_CSV}")

    zona_obra = crear_zona_obra(CENTRO_ZONA_OBRA, RADIO_ZONA_OBRA_METROS)
    gdf = analizar_zona(gdf, zona_obra)

    resumen_por_clase(gdf)

    sufijo = time.strftime("%Y%m%d_%H%M%S")
    ruta_salida = Path(f"detecciones_analisis_espacial_{sufijo}.csv")
    gdf.drop(columns="geometry").to_csv(ruta_salida, index=False)
    print(f"\nCSV con análisis espacial guardado: {ruta_salida}")

    guardar_mapa(gdf, CENTRO_ZONA_OBRA, RADIO_ZONA_OBRA_METROS, "mapa_zona_obra.html")
