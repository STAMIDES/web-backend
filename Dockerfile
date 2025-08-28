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

COPY app/ ./

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000","--root-path", "/api", "--proxy-headers", "--reload"]
