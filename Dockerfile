# Usa una imagen base de Python
FROM ubuntu:22.04

# Instala PostgreSQL
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip
# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos al directorio de trabajo
COPY requirements.txt .

# Instala las dependencias del proyecto
RUN pip3 install --no-cache-dir -r requirements.txt
RUN export PYTHONPATH=/

# Ejecuta la aplicación cuando el contenedor se inicie
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]