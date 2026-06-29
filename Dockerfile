# Imagen base oficial de Python 3.11
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias primero (optimiza caché de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código al contenedor
COPY . .

# Comando por defecto al arrancar el contenedor
CMD ["python", "--version"]
