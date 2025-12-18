# 🗞️ News AI Generator - Backend

Sistema de scraping y generación automática de noticias con IA.

## 📁 Estructura del Proyecto

```
backend/
├── app/                          # Código principal de la aplicación
│   ├── __init__.py
│   ├── main.py                   # Punto de entrada FastAPI
│   ├── scheduler.py              # Jobs programados (APScheduler)
│   │
│   ├── core/                     # Módulos centrales
│   │   ├── __init__.py
│   │   ├── config.py             # Configuración y variables de entorno
│   │   ├── database.py           # Conexión a PostgreSQL
│   │   └── models.py             # Modelos SQLAlchemy
│   │
│   ├── routers/                  # Endpoints de la API
│   │   ├── __init__.py
│   │   ├── auth.py               # Login y JWT
│   │   ├── articles.py           # CRUD de artículos
│   │   ├── templates.py          # CRUD de plantillas
│   │   └── health.py             # Health checks
│   │
│   ├── services/                 # Servicios externos
│   │   ├── __init__.py
│   │   ├── gemini.py             # Google Gemini AI
│   │   ├── scrapegraph.py        # ScrapeGraphAI
│   │   └── wordpress.py          # WordPress GraphQL
│   │
│   └── utils/                    # Utilidades
│       ├── __init__.py
│       └── auth.py               # Autenticación JWT
│
├── scripts/                      # Scripts de utilidad
│   ├── __init__.py
│   └── init_db.py                # Inicializar BD con datos
│
├── docs/                         # Documentación
│   ├── api_documentation.txt
│   ├── api_examples.md
│   ├── architecture_and_notes.md
│   └── deployment_guide.md
│
├── .env.example                  # Variables de entorno ejemplo
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Imagen Docker
└── README.md                     # Este archivo
```

## 🚀 Inicio Rápido

### 1. Clonar y configurar

```bash
cd backend
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Instalar dependencias

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

```bash
# Opción A: Docker
docker run -d --name news_db \
  -e POSTGRES_USER=news_user \
  -e POSTGRES_PASSWORD=news_password \
  -e POSTGRES_DB=news_ai \
  -p 5432:5432 \
  postgres:15

# Opción B: Usar Neon (cloud)
# Actualizar DATABASE_URL en .env
```

### 4. Inicializar base de datos

```bash
python -m scripts.init_db
```

### 5. Ejecutar servidor

```bash
# Desarrollo
uvicorn app.main:app --reload --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Acceder a la documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐳 Docker

```bash
# Construir imagen
docker build -t newsai-backend .

# Ejecutar
docker run -d -p 8000:8000 --env-file .env newsai-backend
```

## 📡 Endpoints de la API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/login` | Login y obtener JWT |
| `POST` | `/admin/articles/run` | Ejecutar scraping manual |
| `GET` | `/admin/articles` | Listar artículos |
| `GET` | `/admin/articles/{id}` | Obtener artículo |
| `PUT` | `/admin/articles/{id}` | Editar artículo |
| `POST` | `/admin/articles/{id}/publish` | Publicar a WordPress |
| `POST` | `/admin/templates` | Crear plantilla |
| `GET` | `/admin/templates` | Listar plantillas |
| `PUT` | `/admin/templates/{id}` | Actualizar plantilla |
| `DELETE` | `/admin/templates/{id}` | Eliminar plantilla |
| `POST` | `/admin/templates/{id}/test` | Probar plantilla |
| `GET` | `/football/presets` | Listar ligas preconfiguradas (ej. Perú Liga 1) |
| `GET` | `/football/presets/{alias}/standings` | Tabla de posiciones usando preset |
| `GET` | `/football/leagues/{league_id}/fixtures` | Partidos por liga/temporada |
| `GET` | `/football/leagues/{league_id}/top-scorers` | Goleadores por liga |
| `GET` | `/health` | Health check |

## ⚙️ Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de PostgreSQL | `postgresql+asyncpg://user:pass@host/db` |
| `SECRET_KEY` | Clave secreta JWT | `your-secret-key` |
| `GEMINI_API_KEY` | API Key de Google Gemini | `AIza...` |
| `WP_GRAPHQL_ENDPOINT` | URL GraphQL de WordPress | `https://site.com/graphql` |
| `WP_AUTH_TOKEN` | Token JWT de WordPress | `eyJ...` |
| `SCRAPE_URLS` | URLs a scrapear (separadas por coma) | `https://bbc.com,https://rpp.pe` |
| `FOOTYSTATS_API_KEY` | API Key de FootyStats | `tu-api-key` |
| `FOOTYSTATS_BASE_URL` | Base URL FootyStats | `https://www.footystats.org/api/` |
| `FOOTYSTATS_PRESET_LEAGUES` | JSON con ligas alias->league_id o season_id | `{"peru_primera":{"season_id":14912,"season":2025},"peru_segunda":{"season_id":16183,"season":2025}}` |

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app
```

## 📝 Licencia

MIT License
# Deploy test - Thu 18 Dec 2025 11:09:21 AM -05
# Cloud Build retry - Thu 18 Dec 2025 12:49:24 PM -05
