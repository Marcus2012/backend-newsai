# 📰 News AI Generator - Sistema Full-Stack

Sistema completo de scraping automático de noticias y generación de contenido con IA usando Gemini 2.5 Pro.

## 🎯 Características

✅ **Scraping automático** desde múltiples fuentes con ScrapeGraphAI  
✅ **Generación de contenido IA** usando Gemini 2.5 Pro  
✅ **Publicación en WordPress** vía WPGraphQL  
✅ **Dashboard administrativo** con Angular 17+  
✅ **Autenticación JWT** segura  
✅ **Base de datos PostgreSQL** en Neon  
✅ **Scheduler automático** con APScheduler  
✅ **Docker Compose** para despliegue fácil  

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.11** + **FastAPI**
- **SQLAlchemy** + **PostgreSQL**
- **ScrapeGraphAI** (Open-source)
- **Google Gemini 2.5 Pro API**
- **APScheduler** para tareas programadas
- **JWT** para autenticación

### Frontend
- **Angular 17+**
- **TypeScript**
- **Reactive Forms**
- **Bootstrap utilities**

### Infraestructura
- **Docker & Docker Compose**
- **PostgreSQL 16**
- **Redis** (opcional para Celery)

---

## 📁 Estructura de Carpetas

```
news-ai-generator/
├── backend/
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── database.py             # Configuración BD
│   ├── models.py               # Modelos SQLAlchemy
│   ├── scheduler.py            # Jobs programados
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routers/
│   │   ├── auth.py
│   │   ├── articles.py
│   │   ├── templates.py
│   │   └── health.py
│   ├── services/
│   │   ├── gemini_service.py
│   │   ├── scrapegraph_service.py
│   │   └── wordpress_service.py
│   └── utils/
│       └── auth_utils.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts
│   │   │   ├── pages/
│   │   │   │   ├── login/
│   │   │   │   ├── dashboard/
│   │   │   │   └── editor/
│   │   │   └── services/
│   │   │       ├── auth.service.ts
│   │   │       └── article.service.ts
│   │   └── environments/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🚀 Inicio Rápido

### Requisitos Previos
- Docker & Docker Compose
- Google Cloud API Key (Gemini)
- WordPress con WPGraphQL habilitado (opcional)

### Paso 1: Clonar y configurar

```bash
git clone https://github.com/tuusername/news-ai-generator.git
cd news-ai-generator

# Crear archivo .env
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables críticas en .env:**
```
GEMINI_API_KEY=tu-key-de-gemini-aqui
SECRET_KEY=genera-una-clave-segura
WP_GRAPHQL_ENDPOINT=https://tudominio.com/graphql
WP_AUTH_TOKEN=tu-token-wordpress
```

### Paso 2: Iniciar con Docker Compose

```bash
docker-compose up -d
```

Este comando levanta:
- PostgreSQL (puerto 5432)
- ScrapeGraphAI (puerto 8001)
- FastAPI Backend (puerto 8000)
- Angular Frontend (puerto 4200)
- Redis (puerto 6379)

### Paso 3: Acceder a la aplicación

```
Frontend: http://localhost:4200
Backend API: http://localhost:8000
Documentación API: http://localhost:8000/docs
```

### Paso 4: Login

**Credenciales de demo:**
- Usuario: `admin`
- Contraseña: `admin123`

O:
- Usuario: `editor`
- Contraseña: `editor123`

---

## 📊 Base de Datos

### Tablas principales

#### `raw_articles`
Almacena artículos scrapeados crudos:
```sql
id (UUID)                    -- ID único
source (text)                -- Fuente (BBC, El Comercio, etc)
source_url (text)            -- URL original
scraped_title (text)         -- Título extraído
scraped_body (text)          -- Cuerpo del artículo
image_url (text)             -- URL de imagen
context (text)               -- Contexto para IA
raw_json (JSONB)             -- JSON completo del scraping
scraper_template (varchar)   -- ID de plantilla usada
scraper_version (varchar)    -- Versión del scraper
scraped_at (timestamptz)     -- Fecha de scraping
created_at, updated_at       -- Timestamps
```

#### `generated_articles`
Artículos generados por la IA:
```sql
id (UUID)                    -- ID único
raw_article_id (FK)          -- Referencia a raw_articles
title (text)                 -- Título generado
description (text)           -- Descripción generada
seo_meta (JSONB)             -- Meta datos SEO
image_url (text)             -- Imagen del artículo
status (enum)                -- draft | pending_review | published
wp_post_id (varchar)         -- ID del post en WordPress
created_at, updated_at
```

#### `scraper_templates`
Plantillas de scraping personalizables:
```sql
id (UUID)
domain (varchar)             -- Dominio (ej: bbc.com)
selectors (JSONB)            -- Selectores CSS
rules (JSONB)                -- Reglas de parseo
version (varchar)
active (varchar)
created_at, updated_at
```

---

## 🔌 API Endpoints

### Autenticación

**POST** `/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```
Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

### Artículos

**GET** `/admin/articles` - Listar borradores
- Query params: `status_filter`, `skip`, `limit`

**GET** `/admin/articles/{id}` - Obtener artículo

**PUT** `/admin/articles/{id}` - Editar borrador
```json
{
  "title": "Nuevo título",
  "description": "Nueva descripción",
  "seo_meta": {
    "meta_title": "...",
    "meta_description": "...",
    "keywords": ["palabra1", "palabra2"]
  }
}
```

**POST** `/admin/articles/{id}/publish` - Publicar en WordPress

### Plantillas de Scraping

**POST** `/admin/templates` - Crear plantilla
```json
{
  "domain": "bbc.com",
  "selectors": {
    "title": "h1, .headline",
    "body": "article, .content",
    "image": "img[itemprop='image']"
  },
  "rules": { }
}
```

**GET** `/admin/templates` - Listar plantillas

**PUT** `/admin/templates/{id}` - Actualizar

**DELETE** `/admin/templates/{id}` - Eliminar

**POST** `/admin/templates/{id}/test?url=...` - Probar plantilla

### Health

**GET** `/health` - Estado del sistema

**GET** `/health/ready` - Readiness check

---

## 🤖 Prompt de Gemini

El sistema usa este prompt para generar contenido:

```
Eres un redactor profesional. Usando EXCLUSIVAMENTE la información del CONTEXTO, 
genera SOLO este JSON:

{
  "title": "Título conciso",
  "description": "Descripción en 2-3 oraciones",
  "seo": {
    "meta_title": "Meta title (máx 60 chars)",
    "meta_description": "Meta description (máx 160 chars)",
    "keywords": ["palabra1", "palabra2", "palabra3"]
  }
}

REGLAS:
- No inventes hechos
- No agregues cuerpo largo
- Solo JSON, sin explicaciones
```

---

## ⏰ Scheduler

El sistema ejecuta scraping automático en horarios:

- **08:00 AM UTC** - Scraping diario completo
- **Cada 6 horas** - Scraping periódico

Para cambiar horarios, edita `scheduler.py`:

```python
scheduler.add_job(
    scraping_job,
    CronTrigger(hour=8, minute=0),  # Cambiar aquí
    id="daily_scrape"
)
```

---

## 🔐 Seguridad

- **JWT tokens** con expiración configurable
- **HTTPS recomendado** en producción
- **CORS** configurado para desarrollo
- **Validación** de entrada en todos los endpoints
- **Variables de entorno** para secretos

**En producción:**
1. Cambiar `SECRET_KEY` en `.env`
2. Usar HTTPS
3. Configurar CORS correctamente
4. Habilitar validación de headers
5. Usar credenciales seguras para BD

---

## 📤 Integración WordPress

### Requisitos
1. WordPress con **WPGraphQL** plugin instalado
2. Generar **Application Password** en WordPress
3. Configurar en `.env`:

```bash
WP_GRAPHQL_ENDPOINT=https://tudominio.com/graphql
WP_AUTH_TOKEN=tu_application_password
```

### Flujo
1. Backend genera artículo con IA
2. Admin lo edita en el dashboard
3. Al hacer click en "Publicar", se crea un POST en WordPress como **DRAFT**
4. Admin revisa en WordPress y publica si está conforme

---

## 🐛 Troubleshooting

### Conexión a BD rechazada
```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps

# Ver logs
docker-compose logs postgres
```

### ScrapeGraphAI falla
```bash
# Verificar endpoint
curl http://localhost:8001/health

# Ver logs
docker-compose logs scrapegraph
```

### Gemini API error
- Verificar `GEMINI_API_KEY` en `.env`
- Confirmar que la API está habilitada en Google Cloud
- Revisar cuota de uso

### CORS issues
- Verificar que frontend y backend tienen dominios correctos
- En desarrollo, CORS está permitido para todos

---

## 📚 Variables de Entorno Completas

```bash
# Base de datos (Neon)
DATABASE_URL=postgresql+asyncpg://user:pass@host/database

# APIs
GEMINI_API_KEY=                # Google Gemini 2.5 Pro
SECRET_KEY=                    # JWT secret, genera uno fuerte

# ScrapeGraphAI
SCRAPEGRAPH_ENDPOINT=http://localhost:8001/api/scrape

# WordPress
WP_GRAPHQL_ENDPOINT=           # URL del GraphQL de WordPress
WP_AUTH_TOKEN=                 # Bearer token de WordPress

# Scraping
SCRAPE_URLS=https://bbc.com,https://rpp.pe,https://elcomercio.pe

# Frontend
API_URL=http://localhost:8000
ANGULAR_API_URL=http://localhost:8000
```

---

## 🚀 Deployment

### En producción

1. **Backend en Heroku/Railway/Render:**
```bash
# Crear requirements.txt
pip freeze > requirements.txt

# Usar buildpack Python
# Configurar variables de entorno
# Conectar a Neon
```

2. **Frontend en Vercel/Netlify:**
```bash
npm run build
# Deploy la carpeta dist/
```

3. **Base de datos Neon:**
- Crear proyecto en [neon.tech](https://neon.tech)
- Usar connection string en `DATABASE_URL`

---

## 📞 Soporte

Para issues o preguntas:
1. Revisar logs: `docker-compose logs [servicio]`
2. Verificar .env está correctamente configurado
3. Confirmar que todos los servicios están corriendo
4. Revisar documentación de componentes individuales

---

## 📝 Licencia

MIT License - Feel free to use and modify

---

## 🎉 Listo para producción

Este sistema está listo para:
- ✅ Scrapear múltiples fuentes
- ✅ Generar contenido con IA
- ✅ Publicar en WordPress
- ✅ Gestionar via dashboard
- ✅ Escalar con Docker

¡Bienvenido al futuro de la generación de noticias! 📰✨