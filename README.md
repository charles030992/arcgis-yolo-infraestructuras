# ArcGIS + YOLO: Detección de Infraestructuras Georreferenciada

Pipeline completo: foto de obra → detección de objetos con YOLO → punto georreferenciado en ArcGIS Online.

## Stack

- **ArcGIS API for Python** — conexión, consulta y publicación de capas GIS
- **YOLOv8** — detección de objetos en imágenes de infraestructuras (Google Colab)
- **Python 3.11** + Anaconda — entorno de desarrollo

## Estructura del proyecto

```
01_conexion_arcgis.py     → Conexión a ArcGIS Online y búsqueda de capas públicas
02_login_autenticado.py   → Autenticación OAuth con cuenta ArcGIS
03_explorar_capa.py       → Estructura interna de una Feature Layer: campos, geometría, registros
04_consulta_filtros.py    → Queries con filtros sobre capas reales (próximamente)
05_visualizacion.py       → Mapas interactivos en Jupyter (próximamente)
06_publicar_capa.py       → Crear y publicar capa propia en ArcGIS Online (próximamente)
07_yolo_deteccion.py      → Detección de objetos con YOLOv8 (Google Colab)
08_flujo_completo.py      → Foto → YOLO → punto en ArcGIS
```

## Caso de uso

Aplicado al sector de obra e infraestructuras:
1. Técnico fotografía señal, activo o defecto en campo
2. YOLO identifica el objeto y su tipo
3. El sistema publica un punto georreferenciado en ArcGIS con foto y atributos
4. El equipo de gestión visualiza el mapa actualizado en tiempo real

## Setup

```bash
conda create -n arcgis-yolo python=3.11 -y
conda activate arcgis-yolo
conda install -c esri arcgis -y
pip install python-dotenv
```

Copia `.env.example` a `.env` y añade tu Application ID de ArcGIS Online.

## Aprendizaje

Proyecto desarrollado como formación intensiva en GIS + Computer Vision aplicada a infraestructuras.
