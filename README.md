# 🚀 Backend MIDES

Esta es la aplicación backend para MIDES, construida con FastAPI y PostgreSQL. La aplicación proporciona una API REST para la gestión de vehículos, choferes, lugares comunes, usuarios y planificación de rutas.

## 🛠️ Tecnologías

- ⚡ FastAPI - Framework web moderno y rápido
- 🐘 PostgreSQL con PostGIS - Base de datos espacial
- 🐳 Docker y Docker Compose - Containerización
- 🔄 SQLAlchemy - ORM para base de datos
- 🗺️ GeoAlchemy2 - Extensión espacial para SQLAlchemy
- 🔐 JWT - Autenticación de usuarios
- 📊 Alembic - Migraciones de base de datos
- 📝 Reportlab - Generación de PDFs
- 📈 Matplotlib - Visualización de datos

## 📁 Estructura del Proyecto

- 🔐 `/app/autenticacion` - Módulos de autenticación y autorización
- 📊 `/app/alembic` - Migraciones de base de datos
- 🗄️ `/app/models.py` - Modelos de datos Pydantic
- 🛣️ `/app/routes.py` - Rutas de la API
- 🎲 `/app/database.py` - Modelos SQLAlchemy y lógica de base de datos
- 🛠️ `/app/utils` - Utilidades (generación de PDFs, emails, etc.)
- 📜 `/app/scripts` - Scripts de utilidad y población de datos

## 🚀 Instalación

1. Clonar el repositorio
2. Copiar el archivo de variables de entorno:
   ```bash
   cp .env.example .env
   ```
3. Configurar las variables de entorno en el archivo `.env`
4. Levantar los contenedores con Docker Compose:
   ```bash
   docker-compose up -d
   ```

## 💻 Desarrollo

Primero, copia el archivo de variables de entorno y configúralo:

```bash
cp .env.example .env
```

> **📝 Nota**: Para desarrollo local con Docker Compose, lo único crucial es que `POSTGRES_HOST=db`. El resto de las variables pueden configurarse según tu preferencia.

Luego, para ejecutar el ambiente de desarrollo completo:

```bash
docker-compose up --build
```

Este comando:
- 🏗️ Construye/reconstruye las imágenes si hay cambios
- 🐘 Levanta la base de datos PostgreSQL con PostGIS
- 🔄 Ejecuta las migraciones de la base de datos automáticamente
- 🚀 Inicia el servidor FastAPI

## 🏭 Producción

El flujo de despliegue completo es el siguiente:

1. Construir la **imagen del backend** y subirla al registry:
```bash
docker build -t [REGISTRY_URL]/mides-backend:[TAG] . --push
```

⚠️ Antes de continuar, asegúrate de que el archivo `.env` contenga las variables de entorno correctas para el ambiente de producción y este disponible para los siguientes comandos:

2. En el ambiente de producción, descargar y ejecutar la imagen:
```bash
docker pull [REGISTRY_URL]/mides-backend:[TAG]
docker run --name backend --env-file [PATH_TO_ENV_FILE] -p 8000:8000 -d [REGISTRY_URL]/mides-backend:[TAG]
```

> **📝 Nota**: Al iniciar, el contenedor automáticamente verifica y aplica cualquier migración pendiente en la base de datos usando Alembic. Esto asegura que el esquema de la base de datos esté siempre actualizado con la última versión del código.


## ⚙️ Variables de Entorno

Las variables de entorno necesarias son:

```bash
# Configuración de PostgreSQL
POSTGRES_HOST=db 
POSTGRES_PORT=5432
POSTGRES_USER=usuario
POSTGRES_PASSWORD=contraseña
POSTGRES_DB=mides

# Configuración de la aplicación
DOMINIO_FRONTEND=http://localhost:5173

# Configuración de Email (para recuperación de contraseña)
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_email_password
SENDER_APP_PASSWORD=your_email_app_password
```

> **📝 Nota**: Los valores mostrados arriba son ejemplos para desarrollo local. En un entorno de producción, estas variables deberán ajustarse según corresponda.

## 📦 Base de Datos

El proyecto utiliza PostgreSQL con la extensión PostGIS para el manejo de datos geoespaciales. Las migraciones se manejan con Alembic:

```bash
# Crear una nueva migración
alembic revision --autogenerate -m "descripción del cambio"

# Aplicar migraciones
alembic upgrade head 
```

## 📚 Documentación API

Una vez que el servidor está corriendo, puedes acceder a la documentación interactiva de la API en:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
