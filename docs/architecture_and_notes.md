# 🏗️ Arquitectura del Sistema

## 📊 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Angular 17)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Login      │  │  Dashboard   │  │   Editor     │           │
│  │  Component   │  │  Component   │  │  Component   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                  │                   │
│         └────────────┬────────────────┬──────┘                   │
│                      │                │                          │
│              ┌───────▼─────────┐      │                          │
│              │ HTTP Interceptor│      │                          │
│              │ + JWT Auth      │      │                          │
│              └───────┬─────────┘      │                          │
│                      │                │                          │
└──────────────────────┼────────────────┼──────────────────────────┘
                       │                │
                ┌──────▼────────────────▼──────┐
                │   FastAPI Backend (Python)   │
                │        (Puerto 8000)         │
                └──────┬────────────────┬──────┘
                       │                │
        ┌──────────────┼────────────────┼──────────────┐
        │              │                │              │
   ┌────▼───┐  ┌────────▼──────┐  ┌────▼──────┐  ┌───▼────┐
   │ Router:│  │  Services:    │  │ Scheduler │  │ Models:│
   │ ────── │  │ ──────────    │  │ ────────  │  │ ────── │
   │ /auth  │  │ Gemini        │  │ APScheduler│ │ Raw    │
   │ /admin │  │ ScrapeGraph   │  │ Daily @8AM│ │Article │
   │        │  │ WordPress     │  │ Every 6h  │ │Generated
   └────────┘  └───┬──────────┘  └───────────┘  └───────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼──┐  ┌───▼────┐  ┌──▼──────┐
   │Gemini │  │ScrapeG │  │WordPress│
   │API    │  │Graph   │  │GraphQL  │
   │raph   │  │OSS     │  │         │
   │2.5Pro │  │        │  │         │
   └───────┘  └────────┘  └─────────┘
        │          │          │
        └──────────┼──────────┘
                   │
         ┌─────────▼─────────┐
         │  PostgreSQL BD    │
         │   (Neon/Local)    │
         │  ┌──────────────┐ │
         │  │raw_articles  │ │
         │  │generated_    │ │
         │  │articles      │ │
         │  │scraper_      │ │
         │  │templates     │ │
         │  └──────────────┘ │
         └───────────────────┘
```

---

## 🔄 Flujo de Datos

### 1. Scraping Automático

```
APScheduler (Timer)
    ↓
scraping_job() función
    ↓
Obtener plantillas activas de BD
    ↓
Para cada URL en SCRAPE_URLS:
    ├─→ Llamar a ScrapeGraphAI
    ├─→ Extraer: title, body, image, context
    ├─→ Guardar en raw_articles
    ├─→ Enviar contexto a Gemini 2.5 Pro
    ├─→ Recibir JSON generado
    └─→ Guardar en generated_articles (status: draft)
```

### 2. Edición y Publicación

```
Admin abre Dashboard
    ↓
GET /admin/articles (con JWT)
    ↓
Backend retorna lista de artículos (draft/pending/published)
    ↓
Admin hace click en "Editar"
    ↓
GET /admin/articles/{id}
    ↓
Componente EditorComponent muestra formulario
    ↓
Admin modifica título, descripción, SEO
    ↓
PUT /admin/articles/{id}
    ↓
Backend actualiza BD
    ↓
Admin hace click en "Publicar"
    ↓
POST /admin/articles/{id}/publish
    ↓
Backend crea POST en WordPress vía WPGraphQL (DRAFT)
    ↓
Retorna wp_post_id
    ↓
BD actualiza estado a "published"
```

### 3. Autenticación JWT

```
Usuario escribe credenciales
    ↓
POST /auth/login {username, password}
    ↓
Backend verifica contra USERS_DB
    ↓
Si válido:
    ├─→ Genera JWT con expiración (480 minutos)
    ├─→ Retorna token
    └─→ Frontend almacena en localStorage
    
Si inválido:
    └─→ Retorna 401 Unauthorized

Cada request posterior:
    ├─→ Frontend agrega header: Authorization: Bearer {token}
    ├─→ Backend valida token con jwt.decode()
    └─→ Si válido, procesa request; si no, retorna 401
```

---

## 📁 Estructura de Carpetas Detallada

```
news-ai-generator/
│
├── backend/
│   ├── main.py                           # Punto de entrada FastAPI
│   ├── database.py                       # Config AsyncPG + SQLAlchemy
│   ├── models.py                         # SQLAlchemy ORM models
│   ├── scheduler.py                      # APScheduler jobs
│   ├── init_db.py                        # Script de inicialización
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                       # POST /auth/login
│   │   ├── articles.py                   # CRUD de artículos
│   │   ├── templates.py                  # CRUD de plantillas
│   │   └── health.py                     # Health checks
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_service.py             # Gemini 2.5 Pro integration
│   │   ├── scrapegraph_service.py        # ScrapeGraphAI integration
│   │   └── wordpress_service.py          # WordPress GraphQL integration
│   │
│   └── utils/
│       ├── __init__.py
│       └── auth_utils.py                 # JWT helpers
│
├── frontend/
│   ├── src/
│   │   ├── index.html
│   │   ├── main.ts
│   │   │
│   │   ├── app/
│   │   │   ├── app.component.ts          # Componente raíz
│   │   │   ├── app.module.ts             # NgModule principal
│   │   │   ├── app-routing.module.ts     # Routing setup
│   │   │   │
│   │   │   ├── pages/
│   │   │   │   ├── login/
│   │   │   │   │   └── login.component.ts
│   │   │   │   ├── dashboard/
│   │   │   │   │   └── dashboard.component.ts
│   │   │   │   └── editor/
│   │   │   │       └── editor.component.ts
│   │   │   │
│   │   │   ├── services/
│   │   │   │   ├── auth.service.ts       # Auth & JWT
│   │   │   │   └── article.service.ts    # API calls
│   │   │   │
│   │   │   └── guards/
│   │   │       └── auth.guard.ts         # Route protection
│   │   │
│   │   ├── environments/
│   │   │   ├── environment.ts
│   │   │   └── environment.prod.ts
│   │   │
│   │   └── styles.css                    # Global styles
│   │
│   ├── angular.json
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── DEPLOYMENT.md
└── ARCHITECTURE.md
```

---

## 🔌 Integraciones Externas

### Google Gemini 2.5 Pro

**Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent`

**Payload:**
```python
{
  "model": "gemini-2.5-pro",
  "messages": [
    {
      "role": "user",
      "content": "Eres redactor... [PROMPT COMPLETO]"
    }
  ]
}
```

**Respuesta esperada:**
```json
{
  "title": "Título del artículo",
  "description": "Descripción corta",
  "seo": {
    "meta_title": "Meta title",
    "meta_description": "Meta description",
    "keywords": ["palabra1", "palabra2"]
  }
}
```

### ScrapeGraphAI (Open-source)

**Endpoint:** `http://scrapegraph:8000/api/scrape`

**Payload:**
```python
{
  "url": "https://ejemplo.com/articulo",
  "config": {
    "headless": True,
    "timeout": 30
  },
  "template": {
    "selectors": {
      "title": "h1",
      "body": "article p",
      "image": "img[itemprop='image']",
      "context": "p"
    }
  }
}
```

### WordPress GraphQL

**Endpoint:** `https://tudominio.com/graphql`

**Mutation (Crear Post):**
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    post {
      id
      databaseId
      title
      status
    }
  }
}
```

---

## 🗄️ Esquema de Base de Datos

### Tabla: raw_articles

```sql
CREATE TABLE raw_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    scraped_title TEXT,
    scraped_body TEXT,
    image_url TEXT,
    context TEXT,
    raw_json JSONB,
    scraper_template UUID REFERENCES scraper_templates(id),
    scraper_version VARCHAR(50),
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_raw_articles_source ON raw_articles(source);
CREATE INDEX idx_raw_articles_scraped_at ON raw_articles(scraped_at DESC);
```

### Tabla: generated_articles

```sql
CREATE TABLE generated_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_article_id UUID NOT NULL REFERENCES raw_articles(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    seo_meta JSONB,
    image_url TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending_review', 'published')),
    wp_post_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_generated_articles_status ON generated_articles(status);
CREATE INDEX idx_generated_articles_raw_article_id ON generated_articles(raw_article_id);
CREATE INDEX idx_generated_articles_created_at ON generated_articles(created_at DESC);
```

### Tabla: scraper_templates

```sql
CREATE TABLE scraper_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    selectors JSONB NOT NULL,
    rules JSONB,
    version VARCHAR(50) DEFAULT '1.0',
    active VARCHAR(5) DEFAULT 'true',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_scraper_templates_domain ON scraper_templates(domain);
CREATE INDEX idx_scraper_templates_active ON scraper_templates(active);
```

---

## 🔐 Flujo de Seguridad

```
Request HTTP
    ↓
├─ Sin Authorization header
│   └─→ Se deja pasar (solo a /auth/login)
│
└─ Con Authorization header
    ├─→ FastAPI extrae Bearer token
    ├─→ Valida con JWT secret
    ├─→ Si expirado → 401 Unauthorized
    ├─→ Si inválido → 401 Unauthorized
    └─→ Si válido → Continúa a endpoint
        ├─→ usuario = payload["sub"]
        └─→ Procesa request
```

---

## ⚡ Performance Optimizations

### Backend
- **AsyncPG:** Conexiones asincrónicas a BD
- **Connection pooling:** NullPool para stateless
- **Indexación:** Índices en campos de búsqueda
- **Caching:** Headers Cache-Control en respuestas
- **Compression:** Gzip en responses FastAPI

### Frontend
- **Lazy loading:** Rutas con preloading
- **OnPush detection:** ChangeDetectionStrategy
- **Virtual scrolling:** Para listas grandes
- **Image optimization:** Angular image directive
- **Bundle splitting:** Webpack optimization

### Base de Datos
- **Índices en tablas principales**
- **Particionamiento por fecha** (futura escalabilidad)
- **EXPLAIN ANALYZE** para queries
- **Connection pooling:** PgBouncer si necesario

---

## 📊 Escalabilidad

### Horizontal Scaling
```
Load Balancer (nginx)
    ├─→ Backend instancia 1 (puerto 8001)
    ├─→ Backend instancia 2 (puerto 8002)
    ├─→ Backend instancia 3 (puerto 8003)
    │
    └─→ PostgreSQL replicado (master-slave)
```

### Vertical Scaling
```
Aumentar recursos:
- CPU cores
- RAM
- Disk space
- Network bandwidth
```

### Cuando considerar:
- Llegar a 1000+ artículos/día
- 1000+ usuarios concurrentes
- Baja en performance < 1 segundo

---

## 🧪 Testing (Roadmap)

### Unitarios
```python
# tests/test_gemini_service.py
def test_generate_article():
    context = "..."
    result = generate_article(context)
    assert "title" in result
    assert "description" in result
```

### Integración
```python
# tests/test_articles_api.py
def test_get_articles():
    response = client.get("/admin/articles")
    assert response.status_code == 401  # Sin token
```

### End-to-end
```typescript
// frontend/e2e/dashboard.spec.ts
it('should list articles', () => {
  cy.visit('/dashboard');
  cy.get('[data-testid="article-card"]').should('be.visible');
});
```

---

## 📈 Monitoreo

### Métricas a trackear
- Latencia de API (p50, p95, p99)
- Tasa de error (4xx, 5xx)
- Uso de BD (queries/segundo, conexiones)
- Uso de CPU/RAM
- Errors de integración (Gemini, WordPress)

### Alertas recomendadas
- Error rate > 1%
- Response time > 5 segundos
- BD conexiones agotadas
- Disk space < 10%
- API key expirada

---

## 🔄 CI/CD Pipeline (Recomendado)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: npm run lint
      - run: npm run test
      
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: docker build -t image:tag .
      - run: docker push image:tag
      
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

---

## 📚 Stack de Desarrollo

| Componente | Tecnología | Versión | Propósito |
|-----------|-----------|---------|----------|
| Backend | Python | 3.11 | Lenguaje principal |
| Framework | FastAPI | 0.109 | API async |
| BD | PostgreSQL | 16 | Persistencia |
| ORM | SQLAlchemy | 2.0 | Mapeo ORM |
| Frontend | Angular | 17 | UI Admin |
| Autenticación | JWT | - | Seguridad |
| IA | Gemini 2.5 Pro | - | Generación contenido |
| Scraping | ScrapeGraphAI | OSS | Extracción datos |
| WordPress | WPGraphQL | - | Publicación |
| Scheduler | APScheduler | 3.10 | Tareas automáticas |
| Contenedores | Docker | - | Despliegue |
| Orquestación | Docker Compose | - | Desarrollo |

---

**Última actualización:** 2024  
**Versión:** 1.0.0  
**Estado:** ✅ Listo para producción