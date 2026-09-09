# Ingesta MV Cloud

Pipeline de ingesta de datos para el proyecto ProyCloud. Extrae el 100% de los registros de los 3 microservicios y los carga como archivos CSV en un bucket Amazon S3, listos para ser catalogados por AWS Glue y consultados con AWS Athena.

## Arquitectura

```
[PostgreSQL]  →  ingesta-catalogo  →  s3://bucket/catalogo/YYYY-MM-DD/
[MySQL]       →  ingesta-comunity  →  s3://bucket/comunity/YYYY-MM-DD/
[MongoDB]     →  ingesta-frontend  →  s3://bucket/frontend/YYYY-MM-DD/
```

## Estructura del repositorio

```
ingesta-mv-cloud/
├── docker-compose.yml          # Orquesta los 3 contenedores
├── .env.example                # Plantilla de variables de entorno
├── ingesta-catalogo/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ingest.py               # Extrae de PostgreSQL → CSV → S3
├── ingesta-comunity/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ingest.py               # Extrae de MySQL → CSV → S3
└── ingesta-frontend/
    ├── Dockerfile
    ├── requirements.txt
    └── ingest.py               # Extrae de MongoDB → CSV → S3
```

## Tablas / Colecciones extraídas

| Microservicio   | Base de datos | Tablas / Colecciones                                                                 |
|-----------------|---------------|--------------------------------------------------------------------------------------|
| backend_catalogo | PostgreSQL   | `movie`, `artist`, `genre`, `movie_genre`, `movie_artist`, `movie_video_source`, `movie_subtitle` |
| backend_comunity | MySQL        | `users`, `clubs`, `memberships`, `watch_rooms`, `watch_participants`                |
| frontend         | MongoDB      | configurable vía `MONGO_COLLECTIONS` (env var)                                       |

## Uso

### 1. Clonar y configurar

```bash
git clone git@github.com:dado4cs/ingesta-mv-cloud.git
cd ingesta-mv-cloud
cp .env.example .env
# Editar .env con las credenciales reales
nano .env
```

### 2. En la MV de Ingesta (EC2) — usando imágenes de Docker Hub

> Asegúrate de que la EC2 tenga un **Rol IAM** con acceso a S3 (`AmazonS3FullAccess`).

```bash
docker compose up
```

### 3. Desarrollo local — build desde fuentes

Comenta las líneas `image:` y descomenta las líneas `build:` en `docker-compose.yml`:

```bash
docker compose up --build
```

## Variables de entorno

Todas las variables se configuran en el archivo `.env`. Consulta `.env.example` para la lista completa.

| Variable         | Descripción                              | Ejemplo                        |
|------------------|------------------------------------------|--------------------------------|
| `PG_HOST`        | Host de PostgreSQL                       | `10.0.0.5`                     |
| `MYSQL_HOST`     | Host de MySQL                            | `10.0.0.6`                     |
| `MONGO_URI`      | URI de conexión de MongoDB               | `mongodb://10.0.0.7:27017`     |
| `S3_BUCKET`      | Nombre del bucket S3 destino             | `mi-datalake-ingesta`          |
| `AWS_REGION`     | Región de AWS                            | `us-east-1`                    |

> **Nota sobre credenciales AWS:** Si la MV de Ingesta es una EC2 con un Rol IAM asignado, `boto3` tomará los permisos automáticamente y **no** necesitas `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY`.

## Imágenes en Docker Hub

| Imagen                         | Descripción             |
|--------------------------------|-------------------------|
| `dado4cs/ingesta-catalogo:latest` | Ingesta PostgreSQL   |
| `dado4cs/ingesta-comunity:latest` | Ingesta MySQL        |
| `dado4cs/ingesta-frontend:latest` | Ingesta MongoDB      |

Para publicar las imágenes:

```bash
docker build -t dado4cs/ingesta-catalogo:latest ./ingesta-catalogo
docker build -t dado4cs/ingesta-comunity:latest ./ingesta-comunity
docker build -t dado4cs/ingesta-frontend:latest ./ingesta-frontend

docker push dado4cs/ingesta-catalogo:latest
docker push dado4cs/ingesta-comunity:latest
docker push dado4cs/ingesta-frontend:latest
```
