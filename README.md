# Ingesta MV Cloud

Pipeline de ingesta de datos para el proyecto ProyCloud. Extrae el 100% de los registros de los microservicios con base de datos persistente y los carga como archivos CSV en un bucket Amazon S3, listos para ser catalogados por AWS Glue y consultados con AWS Athena.

## Microservicios del proyecto

| Microservicio           | Stack                  | Base de datos          | ¿Se ingesta? |
|-------------------------|------------------------|------------------------|--------------|
| `backend_catalogo`      | Java / Spring Boot     | PostgreSQL             | ✅ Sí         |
| `backend_comunity`      | Python / FastAPI       | MySQL                  | ✅ Sí         |
| `cinema-session-service`| Python / FastAPI       | **Ninguna (stateless)**| ❌ No aplica  |
| `iteraction-service`      | Node.js                | MongoDB                | ✅ Sí         |

> **¿Por qué `cinema-session-service` no tiene contenedor de ingesta?**
> Este microservicio gestiona salas de cine en vivo (sincronización de reproducción y chat en tiempo real). Su estado es **efímero** — vive únicamente en la memoria RAM del proceso mientras el contenedor está activo. No persiste ningún dato en base de datos; cuando la sesión termina, la información se descarta por diseño. Por lo tanto, no hay datos que extraer ni ingestar. Si en el futuro se requiriera guardar historial de sesiones, ese dato debería residir en un servicio de Analytics, no en este microservicio.

## Arquitectura de ingesta

```
[PostgreSQL]  →  ingesta-catalogo   →  s3://bucket/catalogo/YYYY-MM-DD/
[MySQL]       →  ingesta-comunity   →  s3://bucket/comunity/YYYY-MM-DD/
[MongoDB]     →  ingesta-iteraction →  s3://bucket/iteraction/YYYY-MM-DD/
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
└── ingesta-iteraction/
    ├── Dockerfile
    ├── requirements.txt
    └── ingest.py               # Extrae de MongoDB → CSV → S3
```

## Tablas / Colecciones extraídas

| Microservicio   | Base de datos | Tablas / Colecciones                                                                 |
|-----------------|---------------|--------------------------------------------------------------------------------------|
| `backend_catalogo` | PostgreSQL   | `movie`, `artist`, `genre`, `movie_genre`, `movie_artist`, `movie_video_source`, `movie_subtitle` |
| `backend_comunity` | MySQL        | `users`, `clubs`, `memberships`, `watch_rooms`, `watch_participants`                |
| `iteraction-service`| MongoDB      | Extrae dinámicamente todas las colecciones (`reviews`, `likes`, `watchlists`, etc.) |

## Uso

### 1. Clonar y configurar

```bash
git clone git@github.com:villabos/ingesta-mv-cloud.git
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
| `villabos/ingesta-catalogo:latest` | Ingesta PostgreSQL   |
| `villabos/ingesta-comunity:latest` | Ingesta MySQL        |
| `villabos/ingesta-iteraction:latest` | Ingesta MongoDB      |

Para publicar las imágenes:

```bash
docker build -t villabos/ingesta-catalogo:latest ./ingesta-catalogo
docker build -t villabos/ingesta-comunity:latest ./ingesta-comunity
docker build -t villabos/ingesta-iteraction:latest ./ingesta-iteraction

docker push villabos/ingesta-catalogo:latest
docker push villabos/ingesta-comunity:latest
docker push villabos/ingesta-iteraction:latest
```
