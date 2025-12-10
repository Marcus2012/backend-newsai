# 🚀 Guía de Despliegue en Producción

## 📋 Pre-requisitos

### Servicios externos necesarios:
- **Google Cloud** - Gemini API
- **Neon** - PostgreSQL en la nube
- **WordPress** con WPGraphQL
- **Docker Hub** - Para almacenar imágenes
- **Vercel o Netlify** - Para frontend
- **Railway, Render o Heroku** - Para backend

---

## 1️⃣ Configuración de Base de Datos (Neon)

### Crear proyecto en Neon

1. Ir a [neon.tech](https://neon.tech)
2. Crear una cuenta y nuevo proyecto
3. Copiar la cadena de conexión:
```
postgresql://user:password@host.neon.tech/database?sslmode=require
```

4. Convertir a asyncpg:
```
postgresql+asyncpg://user:password@host.neon.tech/database?sslmode=require
```

### Guardar en secretos
```bash
# En tu proveedor de hosting, agregar variable de entorno:
DATABASE_URL=postgresql+asyncpg://...
```

---

## 2️⃣ Configuración de Google Gemini API

### Obtener API Key

1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Crear nuevo proyecto
3. Habilitar "Generative Language API"
4. Ir a Credenciales → Crear clave de API
5. Copiar la clave

### En tu hosting:
```bash
GEMINI_API_KEY=tu_clave_aqui
```

---

## 3️⃣ Integración WordPress + WPGraphQL

### Instalar WPGraphQL

1. En WordPress dashboard → Plugins → Agregar nuevo
2. Buscar "WPGraphQL" (por Jason Bahl)
3. Instalar y activar
4. Ir a GraphQL → General → Copiar endpoint
```
https://tudominio.com/graphql
```

### Generar Application Password

1. WordPress → Mi perfil → Application Passwords
2. Crear nuevo password con nombre "News AI"
3. Copiar el password generado
4. Guardar en tu variable de entorno:
```bash
WP_GRAPHQL_ENDPOINT=https://tudominio.com/graphql
WP_AUTH_TOKEN=application_password_aqui
```

---

## 4️⃣ Despliegue del Backend

### Opción A: Railway

1. **Crear Dockerfile.prod**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

2. **Actualizar requirements.txt**
```bash
# Agregar gunicorn
echo "gunicorn==21.2.0" >> backend/requirements.txt
```

3. **En Railway:**
- Conectar repo de GitHub
- Agregar plugin PostgreSQL
- Configurar variables de entorno
- Deploy automático

### Opción B: Render

1. Crear `render.yaml`:
```yaml
services:
  - type: web
    name: news-ai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    envVars:
      - key: DATABASE_URL
        scope: build,runtime
        sync: false
      - key: GEMINI_API_KEY
        scope: build,runtime
        sync: false
```

2. Conectar a Render dashboard
3. Agregar variables de entorno
4. Deploy

### Opción C: Heroku (Deprecated pero funciona)

```bash
# Login
heroku login

# Crear app
heroku create news-ai-backend

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Configurar variables
heroku config:set GEMINI_API_KEY=...
heroku config:set SECRET_KEY=...
heroku config:set WP_GRAPHQL_ENDPOINT=...

# Deploy
git push heroku main
```

---

## 5️⃣ Despliegue del Frontend

### Opción A: Vercel

1. **Crear archivo `vercel.json`:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "API_URL": "@api_url_prod"
  }
}
```

2. **Conectar repo a Vercel**
3. **Configurar variable de entorno:**
```
API_URL=https://tu-api-produccion.com
```
4. **Autodeploymento al hacer push**

### Opción B: Netlify

1. **Crear `netlify.toml`:**
```toml
[build]
command = "npm run build"
publish = "dist"

[env]
[env.production]
API_URL = "https://tu-api-produccion.com"

[[redirects]]
from = "/*"
to = "/index.html"
status = 200
```

2. **Conectar repo a Netlify**
3. **Deploy automático**

### Opción C: Servidor propio con Nginx

```bash
# Build
npm run build

# Instalar Nginx
sudo apt-get install nginx

# Crear archivo de configuración
sudo nano /etc/nginx/sites-available/news-ai

# Contenido:
server {
    listen 80;
    server_name tudominio.com;

    root /var/www/news-ai/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Habilitar
sudo ln -s /etc/nginx/sites-available/news-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6️⃣ SSL/HTTPS

### Certificado Let's Encrypt

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generar certificado
sudo certbot certonly --nginx -d tudominio.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### Nginx con SSL

```nginx
server {
    listen 443 ssl http2;
    server_name tudominio.com;

    ssl_certificate /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Resto de configuración...
}

# Redirigir HTTP a HTTPS
server {
    listen 80;
    server_name tudominio.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 7️⃣ Variables de Entorno en Producción

**CRÍTICAS - NO COMPARTIR:**
```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://...

# APIs
GEMINI_API_KEY=...
SECRET_KEY=generar_nueva_clave_segura_aqui
WP_AUTH_TOKEN=...

# WordPress
WP_GRAPHQL_ENDPOINT=https://tudominio.com/graphql

# URLs
SCRAPEGRAPH_ENDPOINT=http://scrapegraph:8000/api/scrape (interno)
SCRAPE_URLS=https://www.bbc.com/news,https://www.elcomercio.pe

# Frontend
API_URL=https://tu-api-produccion.com
ANGULAR_API_URL=https://tu-api-produccion.com
```

### Generar SECRET_KEY segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 8️⃣ Monitoreo y Logging

### Agregar logging a Backend

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Servicios de monitoreo

- **Sentry** - Para errores
- **DataDog** - Para métricas
- **Loggly** - Para logs centralizados
- **Uptime Robot** - Para health checks

### Health check automático

```bash
# Railway/Render pueden hacer health checks
GET /health

# Configurar en dashboard como:
# Health Check Path: /health
```

---

## 9️⃣ Backup y Recuperación

### Backup automático de BD

```bash
# Con Neon (automático):
# - Backups diarios
# - Retención de 7 días

# Si usas PostgreSQL propio:
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
gunzip -c backup.sql.gz | PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER $DB_NAME
```

---

## 🔟 Checklist Pre-Producción

- [ ] Base de datos en Neon configurada
- [ ] API Key de Gemini funcionando
- [ ] WordPress con WPGraphQL habilitado
- [ ] Variables de entorno configuradas
- [ ] SSL/HTTPS configurado
- [ ] Health checks funcionando
- [ ] Logs centralizados
- [ ] Backups configurados
- [ ] Domain DNS apuntando a servidor
- [ ] CORS configurado correctamente
- [ ] Rate limiting habilitado
- [ ] Secret key cambiado
- [ ] Base de datos inicializada con migraciones
- [ ] Test de scraping completado
- [ ] Test de Gemini completado
- [ ] Test de WordPress completado

---

## 🔐 Seguridad en Producción

### Cambios importantes

1. **CORS - Cambiar de `"*"` a dominios específicos:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tudominio.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

2. **HTTPS obligatorio:**
```python
@app.middleware("http")
async def https_redirect(request, call_next):
    if request.url.scheme == "http":
        return RedirectResponse(
            url=request.url.replace("http://", "https://"),
            status_code=301
        )
    return await call_next(request)
```

3. **Rate limiting:**
```bash
pip install slowapi

from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

4. **Headers de seguridad:**
```python
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 📊 Monitoreo Post-Deploy

1. **Verificar salud:**
```bash
curl https://tudominio.com/health
```

2. **Verificar logs:**
```bash
# En tu proveedor (Railway, Render, etc)
# Ver logs en tiempo real
```

3. **Probar endpoints:**
```bash
# Login
curl -X POST https://api.tudominio.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Listar artículos
curl https://api.tudominio.com/admin/articles \
  -H "Authorization: Bearer TOKEN"
```

---

## 🆘 Troubleshooting

### BD no conecta
```bash
# Verificar connection string
# Verificar firewall permite puerto 5432
# Verificar credenciales
```

### Gemini API falla
```bash
# Verificar API Key
# Verificar cuota de uso
# Verificar región API
```

### WordPress no recibe artículos
```bash
# Verificar WPGraphQL endpoint es correcto
# Verificar auth token es válido
# Verificar CORS en WordPress
```

### Frontend no conecta a API
```bash
# Verificar API_URL en environment.prod.ts
# Verificar CORS headers en backend
# Verificar que API está respondiendo
```

---

## 📞 Soporte

- GitHub Issues
- Email: tu-email@tudominio.com
- Documentación: https://tu-documentacion.com

---

**🎉 ¡Felicidades! Tu News AI Generator está en producción**