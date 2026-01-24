# 🚀 Guía de Despliegue en Google Cloud Run

## 📋 Requisitos Previos

Antes de desplegar a Cloud Run, asegúrate de tener:

1. **Google Cloud CLI instalado**
   ```bash
   # Descargar desde: https://cloud.google.com/sdk/docs/install
   gcloud --version
   ```

2. **Docker instalado**
   ```bash
   docker --version
   ```

3. **Autenticado en Google Cloud**
   ```bash
   gcloud auth login
   gcloud auth configure-docker
   ```

4. **Proyecto creado en Google Cloud**
   ```bash
   gcloud projects list
   gcloud config set project YOUR_PROJECT_ID
   ```

5. **Facturación habilitada** en tu proyecto de Google Cloud

---

## 🔧 Pasos de Preparación

### 1. Configurar Variables de Entorno

Copiar el archivo de ejemplo y llenarlo con valores reales:

```bash
cp .env.production .env.prod.local
# Editar .env.prod.local con tus valores
```

**Variables críticas requeridas:**
- `DATABASE_URL` - PostgreSQL connection string (ej. Neon, CloudSQL)
- `GEMINI_API_KEY` - API key de Google Gemini
- `GROQ_API_KEY` - API key de Groq
- `SECRET_KEY` - Clave secreta para JWT (generar una nueva)
- `WP_AUTH_TOKEN` - Token de WordPress
- `SPORTMONKS_API_TOKEN` - Token de Sportmonks

### 2. Crear Secretos en Google Cloud

Los secretos deben almacenarse en Google Cloud Secret Manager:

```bash
# Crear secretos
gcloud secrets create DATABASE_URL --data-file=- < <(echo "tu_database_url")
gcloud secrets create GEMINI_API_KEY --data-file=- < <(echo "tu_gemini_key")
gcloud secrets create GROQ_API_KEY --data-file=- < <(echo "tu_groq_key")
gcloud secrets create SECRET_KEY --data-file=- < <(echo "tu_secret_key")
gcloud secrets create WP_AUTH_TOKEN --data-file=- < <(echo "tu_wp_token")
gcloud secrets create SPORTMONKS_API_TOKEN --data-file=- < <(echo "tu_sportmonks_token")

# Ver secretos creados
gcloud secrets list
```

O una opción más segura - usar Google Cloud Console:
- Ir a: Cloud Console → Secret Manager
- Crear cada secreto manualmente

---

## 🚀 Despliegue Automatizado

### Opción 1: Usar el Script de Deployment

```bash
# Permiso de ejecución (ya hecho)
chmod +x scripts/deploy.sh

# Desplegar (usa valores por defecto)
./scripts/deploy.sh

# Desplegar con parámetros personalizados
./scripts/deploy.sh newsai-backend us-central1 tu-proyecto-id
```

**Parámetros:**
- `$1` - SERVICE_NAME (default: newsai-backend)
- `$2` - REGION (default: us-central1)
- `$3` - PROJECT_ID (default: proyecto actual)

### Opción 2: Despliegue Manual

```bash
# 1. Build de la imagen
docker build -t newsai-backend:latest .

# 2. Tag para Google Container Registry
docker tag newsai-backend:latest gcr.io/tu-proyecto-id/newsai-backend:latest

# 3. Push a GCR
docker push gcr.io/tu-proyecto-id/newsai-backend:latest

# 4. Desplegar a Cloud Run
gcloud run deploy newsai-backend \
    --image gcr.io/tu-proyecto-id/newsai-backend:latest \
    --region us-central1 \
    --platform managed \
    --memory 1Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-instances 100 \
    --min-instances 1 \
    --allow-unauthenticated \
    --update-secrets DATABASE_URL=DATABASE_URL:latest,\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
GROQ_API_KEY=GROQ_API_KEY:latest,\
SECRET_KEY=SECRET_KEY:latest,\
WP_AUTH_TOKEN=WP_AUTH_TOKEN:latest,\
SPORTMONKS_API_TOKEN=SPORTMONKS_API_TOKEN:latest
```

---

## 📊 Configuración de Cloud Run

### Especificaciones:
- **Memory:** 1Gi (1024MB)
- **CPU:** 2
- **Timeout:** 3600 segundos (1 hora)
- **Concurrency:** 80 requests simultáneos por instancia
- **Min Instances:** 1 (siempre activa)
- **Max Instances:** 100 (escalado automático)
- **Platform:** Managed (Google gestiona la infraestructura)

### Ajustar según necesidades:

```bash
# Si necesitas más recursos
gcloud run deploy newsai-backend \
    --image gcr.io/tu-proyecto-id/newsai-backend:latest \
    --memory 2Gi \
    --cpu 4 \
    --min-instances 2 \
    --max-instances 200
```

---

## ✅ Verificación Post-Deployment

```bash
# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe newsai-backend \
    --region us-central1 \
    --format='value(status.url)')
echo "Service URL: $SERVICE_URL"

# Probar health check
curl "$SERVICE_URL/health"

# Ver logs en tiempo real
gcloud run logs read newsai-backend --region us-central1 --follow

# Ver detalles del servicio
gcloud run services describe newsai-backend --region us-central1

# Listar revisions
gcloud run revisions list --service newsai-backend --region us-central1
```

---

## 🛠️ Troubleshooting

### Error: "Secret not found"
```bash
# Verificar que los secretos existen
gcloud secrets list

# Crear el secreto si falta
gcloud secrets create NOMBRE_SECRETO --data-file=- < <(echo "valor")
```

### Error: "Permission denied"
```bash
# Dar permisos a la cuenta de servicio
gcloud projects get-iam-policy tu-proyecto-id
gcloud projects add-iam-policy-binding tu-proyecto-id \
    --member=serviceAccount:tu-proyecto-id@appspot.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### Error: "Image not found"
```bash
# Verificar autenticación con Docker
gcloud auth configure-docker

# Hacer push de la imagen nuevamente
docker push gcr.io/tu-proyecto-id/newsai-backend:latest
```

### Error: "Container failed to start"
```bash
# Ver logs detallados
gcloud run logs read newsai-backend --region us-central1 --limit 50

# El puerto debe ser 8080 (verificado en Dockerfile)
```

---

## 📈 Monitoreo y Logging

### Cloud Logging
```bash
# Ver logs de la última hora
gcloud run logs read newsai-backend --region us-central1 --limit 100

# Ver logs con filtro
gcloud run logs read newsai-backend --region us-central1 \
    --limit 50 \
    --format="table(timestamp,severity,textPayload)"
```

### Cloud Monitoring
- Dashboard en: Cloud Console → Monitoring
- Configurar alertas para:
  - Tasa de errores
  - Latencia
  - Uso de memoria
  - Solicitudes por segundo

### Métricas importantes
```bash
# Ver estadísticas de uso
gcloud run services describe newsai-backend --region us-central1 \
    --format="table(status.observedGeneration,status.conditions)"
```

---

## 🔄 Actualizaciones y Rollback

### Desplegar nueva versión
```bash
# Build y push de nueva imagen
docker build -t gcr.io/tu-proyecto-id/newsai-backend:v1.0.1 .
docker push gcr.io/tu-proyecto-id/newsai-backend:v1.0.1

# Desplegar
gcloud run deploy newsai-backend \
    --image gcr.io/tu-proyecto-id/newsai-backend:v1.0.1 \
    --region us-central1
```

### Rollback a versión anterior
```bash
# Listar revisions
gcloud run revisions list --service newsai-backend --region us-central1

# Desplegar versión anterior
gcloud run deploy newsai-backend \
    --image gcr.io/tu-proyecto-id/newsai-backend:v1.0.0 \
    --region us-central1
```

---

## 💰 Optimización de Costos

### Reducir costos:
1. **Min Instances a 0** - La aplicación se escala a cero cuando no hay tráfico
   ```bash
   gcloud run deploy newsai-backend --min-instances 0
   ```

2. **Usar regiones más baratas** - Ej: us-central1 es más barato que europe-west1

3. **Reducir CPU/Memory** - Si no la necesitas toda
   ```bash
   gcloud run deploy newsai-backend --memory 512Mi --cpu 1
   ```

4. **Cloud Scheduler** - Para tareas programadas, usa Cloud Scheduler en lugar de APScheduler

---

## 📋 Checklist Pre-Deployment

- [ ] Todos los tests pasan (`pytest`)
- [ ] Variables de entorno configuradas en Secret Manager
- [ ] Dockerfile actualizado para puerto 8080
- [ ] requirements.txt actualizado con todas las dependencias
- [ ] .gcloudignore está en la raíz
- [ ] BASE DE DATOS está preparada (migrations ejecutadas)
- [ ] Credenciales de APIs externas son válidas
- [ ] CORS está configurado para tu dominio frontend
- [ ] Health check endpoint `/health` funciona
- [ ] Commit final hecho en git

---

## 🎯 Próximos Pasos

1. Ejecutar: `./scripts/deploy.sh`
2. Esperar a que Cloud Run construya y despliegue
3. Verificar logs: `gcloud run logs read newsai-backend`
4. Probar endpoint: `curl YOUR_SERVICE_URL/health`
5. Configurar dominio personalizado (opcional):
   ```bash
   gcloud run domain-mappings create \
       --service newsai-backend \
       --domain tu-dominio.com \
       --region us-central1
   ```

---

**¡Listo para desplegar a producción! 🚀**
