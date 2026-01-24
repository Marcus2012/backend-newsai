# 📡 Ejemplos de Uso de la API

## 🔑 Autenticación

### 1. Login y obtener Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Respuesta exitosa:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800
}
```

**Guardar el token para usar en requests:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 📰 Artículos

### 2. Listar Artículos

```bash
curl -X GET "http://localhost:8000/admin/articles" \
  -H "Authorization: Bearer $TOKEN"
```

**Con filtro de estado:**
```bash
curl -X GET "http://localhost:8000/admin/articles?status_filter=draft" \
  -H "Authorization: Bearer $TOKEN"
```

**Con paginación:**
```bash
curl -X GET "http://localhost:8000/admin/articles?skip=0&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Inteligencia Artificial: El futuro del desarrollo",
    "description": "Las empresas tecnológicas impulsan inversión masiva...",
    "status": "draft",
    "image_url": "https://example.com/image1.jpg",
    "seo_meta": {
      "meta_title": "IA y tecnología 2024",
      "meta_description": "Descubre los últimos avances...",
      "keywords": ["IA", "tecnología", "machine learning"]
    },
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

### 3. Obtener un Artículo Específico

```bash
ARTICLE_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X GET "http://localhost:8000/admin/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Inteligencia Artificial: El futuro",
  "description": "Las empresas tecnológicas...",
  "status": "draft",
  "image_url": "https://example.com/image1.jpg",
  "seo_meta": {
    "meta_title": "IA 2024",
    "meta_description": "Avances en inteligencia artificial",
    "keywords": ["IA", "ML", "tech"]
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 4. Editar un Artículo

```bash
ARTICLE_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X PUT "http://localhost:8000/admin/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Inteligencia Artificial: El Futuro - Actualizado",
    "description": "Nuevo contenido más detallado sobre IA...",
    "seo_meta": {
      "meta_title": "IA 2024 - Nuevas Tendencias",
      "meta_description": "Descubre los últimos avances en inteligencia artificial",
      "keywords": ["inteligencia artificial", "machine learning", "deep learning"]
    }
  }'
```

**Respuesta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Inteligencia Artificial: El Futuro - Actualizado",
  "description": "Nuevo contenido más detallado...",
  "status": "draft",
  "image_url": "https://example.com/image1.jpg",
  "seo_meta": {
    "meta_title": "IA 2024 - Nuevas Tendencias",
    "meta_description": "Descubre los últimos avances...",
    "keywords": ["inteligencia artificial", "machine learning", "deep learning"]
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z"
}
```

### 5. Publicar Artículo en WordPress

```bash
ARTICLE_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST "http://localhost:8000/admin/articles/$ARTICLE_ID/publish" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Respuesta exitosa:**
```json
{
  "status": "success",
  "wp_post_id": "12345",
  "message": "Artículo publicado en WordPress"
}
```

**En caso de error:**
```json
{
  "detail": "Error al publicar: GraphQL error"
}
```

---

## 🔧 Plantillas de Scraping

### 6. Crear Plantilla

```bash
curl -X POST http://localhost:8000/admin/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "elcomercio.pe",
    "selectors": {
      "title": "h1.titular, h1.story-header",
      "body": ".story-content p, article p",
      "image": "figure img, .featured-image img",
      "context": ".titular, .story-header, .story-summary"
    },
    "rules": {
      "image_attr": "src",
      "remove_ads": true
    },
    "version": "1.0"
  }'
```

**Respuesta:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440111",
  "domain": "elcomercio.pe",
  "selectors": {
    "title": "h1.titular, h1.story-header",
    "body": ".story-content p, article p",
    "image": "figure img, .featured-image img",
    "context": ".titular, .story-header, .story-summary"
  },
  "rules": {
    "image_attr": "src",
    "remove_ads": true
  },
  "version": "1.0",
  "active": "true",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 7. Listar Plantillas

```bash
curl -X GET http://localhost:8000/admin/templates \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440111",
    "domain": "elcomercio.pe",
    "selectors": { ... },
    "rules": { ... },
    "version": "1.0",
    "active": "true",
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440222",
    "domain": "bbc.com",
    "selectors": { ... },
    "rules": { ... },
    "version": "1.0",
    "active": "true",
    "created_at": "2024-01-14T09:15:00Z"
  }
]
```

### 8. Actualizar Plantilla

```bash
TEMPLATE_ID="660e8400-e29b-41d4-a716-446655440111"

curl -X PUT "http://localhost:8000/admin/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "selectors": {
      "title": "h1.titular",
      "body": ".story-content p",
      "image": "figure img",
      "context": ".story-summary"
    },
    "version": "1.1"
  }'
```

### 9. Probar Plantilla

```bash
TEMPLATE_ID="660e8400-e29b-41d4-a716-446655440111"
TEST_URL="https://elcomercio.pe/economia/noticia-ejemplo"

curl -X POST "http://localhost:8000/admin/templates/$TEMPLATE_ID/test?url=$TEST_URL" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta (datos extraídos):**
```json
{
  "status": "success",
  "data": {
    "title": "Economía peruana muestra recuperación",
    "body": "El PBI creció más de lo esperado...",
    "image_url": "https://elcomercio.pe/images/noticia.jpg",
    "context": "Los indicadores económicos...",
    "success": true
  }
}
```

### 10. Eliminar Plantilla

```bash
TEMPLATE_ID="660e8400-e29b-41d4-a716-446655440111"

curl -X DELETE "http://localhost:8000/admin/templates/$TEMPLATE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
{
  "status": "deleted"
}
```

---

## 🔄 Scraping Manual

### 11. Ejecutar Scraping Manual

```bash
curl -X POST http://localhost:8000/admin/scrape/run \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
{
  "status": "Scraping iniciado",
  "message": "Ver scheduler para detalles"
}
```

---

## 🏥 Health Checks

### 12. Health Check Básico

```bash
curl http://localhost:8000/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00.123456",
  "version": "1.0.0"
}
```

### 13. Readiness Check

```bash
curl http://localhost:8000/health/ready
```

**Respuesta:**
```json
{
  "status": "ready",
  "services": {
    "database": "ok",
    "scrapegraph": "ok",
    "gemini": "ok"
  }
}
```

---

## 🔐 Manejo de Errores

### Error: Token expirado (401)

```bash
curl -X GET http://localhost:8000/admin/articles \
  -H "Authorization: Bearer $OLD_TOKEN"
```

**Respuesta:**
```json
{
  "detail": "Token expirado"
}
```

**Solución:** Hacer login nuevamente

### Error: Credenciales inválidas (401)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "contraseña_incorrecta"
  }'
```

**Respuesta:**
```json
{
  "detail": "Credenciales inválidas"
}
```

### Error: Artículo no encontrado (404)

```bash
curl -X GET "http://localhost:8000/admin/articles/id-inexistente" \
  -H "Authorization: Bearer $TOKEN"
```

---

**Respuesta:**
```json
{
  "detail": "Artículo no encontrado"
}
```

### Error: No se puede editar artículo publicado (400)

```bash
curl -X PUT "http://localhost:8000/admin/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Nuevo"}'
```

**Respuesta:**
```json
{
  "detail": "No se puede editar un artículo publicado"
}
```

---

## 🧪 Scripts de Testing

### Testing con cURL

```bash
#!/bin/bash

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Listar artículos
curl -s -X GET "http://localhost:8000/admin/articles" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

### Testing con Python

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "admin123"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Listar artículos
articles = requests.get(f"{BASE_URL}/admin/articles", headers=headers)
print(json.dumps(articles.json(), indent=2))

# Editar artículo
if articles.json():
    article_id = articles.json()[0]["id"]
    update = requests.put(
        f"{BASE_URL}/admin/articles/{article_id}",
        headers=headers,
        json={
            "title": "Nuevo título",
            "description": "Nueva descripción"
        }
    )
    print("Actualizado:", update.json())
```

### Testing con Postman

1. **Crear environment en Postman:**
   - Variable `base_url` = `http://localhost:8000`
   - Variable `token` = (se llena después del login)

2. **POST /auth/login**
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
   - Tests (después de request):
   ```javascript
   pm.environment.set("token", pm.response.json().access_token);
   ```

3. **GET /admin/articles**
   - Headers: `Authorization: Bearer {{token}}`
   - Params: `status_filter=draft`

---

## 📊 Casos de Uso Comunes

### Flujo completo: Scraping → Edición → Publicación

```bash
#!/bin/bash

# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | \
  python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "✓ Login exitoso"

# 2. Listar borradores
ARTICLES=$(curl -s -X GET "http://localhost:8000/admin/articles?status_filter=draft" \
  -H "Authorization: Bearer $TOKEN")

ARTICLE_ID=$(echo $ARTICLES | python -c "import sys, json; print(json.load(sys.stdin)[0]['id'])")

echo "✓ Artículo encontrado: $ARTICLE_ID"

# 3. Editar artículo
curl -s -X PUT "http://localhost:8000/admin/articles/$ARTICLE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Título mejorado",
    "description": "Descripción actualizada",
    "seo_meta": {
      "meta_title": "Meta actualizado",
      "meta_description": "Descripción meta",
      "keywords": ["palabra1", "palabra2"]
    }
  }' > /dev/null

echo "✓ Artículo editado"

# 4. Publicar en WordPress
RESULT=$(curl -s -X POST "http://localhost:8000/admin/articles/$ARTICLE_ID/publish" \
  -H "Authorization: Bearer $TOKEN")

WP_ID=$(echo $RESULT | python -c "import sys, json; print(json.load(sys.stdin)['wp_post_id'])")

echo "✓ Publicado en WordPress con ID: $WP_ID"
```

---

## 📝 Notas Importantes

1. **Todos los requests requieren Bearer token** (excepto `/auth/login`)
2. **El token expira en 8 horas** (480 minutos)
3. **Los artículos publicados no se pueden editar**
4. **Las plantillas son por dominio** (un dominio = una plantilla)
5. **El scraping automático se ejecuta a las 8 AM UTC y cada 6 horas**

---

## ⚽ Sportmonks (Fútbol)

### 1. Info de liga (Premier League)

```bash
curl -X GET "http://localhost:8000/leagues/premier-league"
```

### 2. Tabla de posiciones (Premier League)

```bash
curl -X GET "http://localhost:8000/standings/premier-league"
```

### 3. Partidos por fecha (Premier League)

```bash
curl -X GET "http://localhost:8000/fixtures/premier-league?date=2026-01-23"
```

### 4. Serie A (info, tabla y fixtures)

```bash
curl -X GET "http://localhost:8000/leagues/serie-a"
curl -X GET "http://localhost:8000/standings/serie-a"
curl -X GET "http://localhost:8000/fixtures/serie-a?date=2026-01-23"
```

---

**¡Listo para hacer requests contra la API!** 🚀