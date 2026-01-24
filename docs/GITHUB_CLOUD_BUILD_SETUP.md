# 🚀 Configurar GitHub + Google Cloud Build

Esta guía te ayudará a configurar despliegue automático desde GitHub a Google Cloud Run usando Cloud Build.

---

## 📋 Requisitos Previos

1. **Repositorio en GitHub** con acceso administrativo
2. **Proyecto en Google Cloud** con:
   - Cloud Build habilitado
   - Cloud Run habilitado
   - Container Registry habilitado
   - Secret Manager configurado con las credenciales

---

## 🔧 Paso 1: Crear Secretos en Google Cloud Secret Manager

Los secretos deben existir antes de que Cloud Build intente usarlos:

```bash
# Crear secretos desde el archivo .env.production
gcloud secrets create DATABASE_URL --data-file=- < <(grep "^DATABASE_URL=" .env.production | cut -d'=' -f2-)
gcloud secrets create GEMINI_API_KEY --data-file=- < <(grep "^GEMINI_API_KEY=" .env.production | cut -d'=' -f2-)
gcloud secrets create GROQ_API_KEY --data-file=- < <(grep "^GROQ_API_KEY=" .env.production | cut -d'=' -f2-)
gcloud secrets create SECRET_KEY --data-file=- < <(grep "^SECRET_KEY=" .env.production | cut -d'=' -f2-)
gcloud secrets create WP_AUTH_TOKEN --data-file=- < <(grep "^WP_AUTH_TOKEN=" .env.production | cut -d'=' -f2-)
gcloud secrets create SPORTMONKS_API_TOKEN --data-file=- < <(grep "^SPORTMONKS_API_TOKEN=" .env.production | cut -d'=' -f2-)

# Verificar que los secretos existen
gcloud secrets list
```

O manualmente en Cloud Console:
- Ir a: Cloud Console → Secret Manager
- Crear cada secreto con sus valores

---

## 🔑 Paso 2: Dar Permisos a Cloud Build

Cloud Build necesita acceso a Secret Manager:

```bash
# Obtener el número del proyecto
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')

# Dar permisos a la cuenta de servicio de Cloud Build
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor

# Permisos adicionales para Cloud Run
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/run.admin

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/iam.serviceAccountUser
```

---

## 🔗 Paso 3: Conectar GitHub a Google Cloud

### Opción A: Usar Google Cloud Console (Recomendado)

1. Ir a [Cloud Console → Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Hacer clic en **"Connect Repository"**
3. Seleccionar **GitHub** como proveedor
4. Autorizar Google Cloud Build para acceder a tu cuenta de GitHub
5. Seleccionar tu repositorio **newsai**
6. Hacer clic en **"Connect"**

### Opción B: Usar GitHub Apps (Alternativa)

1. Instalar [Cloud Build GitHub App](https://github.com/apps/google-cloud-build)
2. Autorizar y seleccionar repositorios
3. Configurar en Google Cloud Console

---

## ⚙️ Paso 4: Crear el Trigger

1. En Cloud Console → Cloud Build → Triggers
2. Hacer clic en **"Create Trigger"**
3. Configurar:

   **Nombre:**
   ```
   newsai-backend-deploy
   ```

   **Evento:**
   ```
   Push a rama
   ```

   **Rama (regex):**
   ```
   ^main$
   ```

   **Ubicación del archivo de compilación:**
   ```
   Repository
   cloudbuild.yaml
   ```

4. Hacer clic en **"Create"**

---

## 🎯 Paso 5: Verificar la Configuración

```bash
# Ver triggers creados
gcloud builds triggers list

# Ver ID del trigger
gcloud builds triggers list --format="value(id,name)"
```

---

## 🚀 Paso 6: Probar el Despliegue

### Primera opción: Push a main

```bash
# Hacer un cambio pequeño
echo "# Deploy test" >> README.md

# Commit y push
git add README.md
git commit -m "test: trigger cloud build deployment"
git push origin main
```

### Segunda opción: Disparar manualmente

```bash
# Obtener el ID del trigger
TRIGGER_ID=$(gcloud builds triggers list --filter="name='newsai-backend-deploy'" --format="value(id)")

# Disparar el build
gcloud builds submit --config=cloudbuild.yaml --substitutions=_TRIGGER_ID=$TRIGGER_ID
```

### Ver el progreso

```bash
# Ver logs en tiempo real
gcloud builds log --stream

# Ver historial de builds
gcloud builds list --limit 10

# Ver detalles de un build específico
gcloud builds log BUILD_ID --stream
```

---

## 📊 Monitoreo de Deployments

### Cloud Build Dashboard
- [Ir a Cloud Builds](https://console.cloud.google.com/cloud-build/builds)
- Ver historial de todos los deployments
- Haz clic en un build para ver logs detallados

### Cloud Run Dashboard
- [Ir a Cloud Run](https://console.cloud.google.com/run)
- Ver versiones deployadas
- Ver métricas y logs en tiempo real
- Hacer rollback si es necesario

```bash
# Ver logs de Cloud Run
gcloud run logs read newsai-backend --region us-central1 --limit 50

# Ver servicios
gcloud run services list --region us-central1
```

---

## 🔄 Workflow Típico

```bash
# 1. Hacer cambios en tu rama
git checkout -b feature/new-feature

# 2. Hacer commits
git add .
git commit -m "feat: nueva funcionalidad"

# 3. Push a la rama de feature
git push origin feature/new-feature

# 4. Crear Pull Request en GitHub

# 5. Merge a main (después de aprobación)

# 6. ¡Cloud Build se dispara automáticamente!

# 7. Verificar deployment
gcloud run logs read newsai-backend --region us-central1

# 8. Ver URL del servicio
gcloud run services describe newsai-backend --region us-central1 --format='value(status.url)'
```

---

## 🛑 Pausar o Eliminar Trigger

### Pausar
```bash
gcloud builds triggers update newsai-backend-deploy --disabled
```

### Reactivar
```bash
gcloud builds triggers update newsai-backend-deploy --no-disabled
```

### Eliminar
```bash
gcloud builds triggers delete newsai-backend-deploy
```

---

## 🐛 Troubleshooting

### Error: "Secret not found"
```bash
# Verificar que el secreto existe
gcloud secrets describe DATABASE_URL

# Si no existe, crear
gcloud secrets create DATABASE_URL --data-file=- < <(echo "valor")
```

### Error: "Permission denied"
```bash
# Re-ejecutar permisos del Paso 2
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/secretmanager.secretAccessor
```

### Error: "Image push failed"
```bash
# Autenticar con Docker
gcloud auth configure-docker

# Verificar GCR
gcloud container images list
```

### Build lento
- Aumentar `machineType` en `cloudbuild.yaml` a `N1_HIGHCPU_32`
- Revisar logs para ver qué paso es lento

---

## 💰 Costos

- **Cloud Build:** 120 minutos gratuitos/mes, luego $0.003 por minuto
- **Cloud Run:** Paga solo por lo que usas (sin tráfico = $0)
- **Secret Manager:** $0.06 por secreto/mes

---

## 📚 Recursos Adicionales

- [Cloud Build Documentación](https://cloud.google.com/build/docs)
- [Cloud Run Documentación](https://cloud.google.com/run/docs)
- [GitHub + Cloud Build Integration](https://cloud.google.com/build/docs/automating-builds/github)
- [Secret Manager Documentación](https://cloud.google.com/secret-manager/docs)

---

## ✅ Checklist Final

- [ ] Secretos creados en Secret Manager
- [ ] Permisos otorgados a Cloud Build
- [ ] GitHub conectado a Cloud Build
- [ ] Trigger creado para rama `main`
- [ ] `cloudbuild.yaml` está en la raíz del repositorio
- [ ] Primer push a `main` dispara un build exitoso
- [ ] Cloud Run está ejecutando la última versión
- [ ] URL del servicio funciona

---

**¡Listo! Ahora cada push a `main` desplega automáticamente a Cloud Run. 🎉**
