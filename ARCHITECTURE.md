# Arquitectura del Sistema - Screenshot Management

## Diagrama de Flujo

```
Usuario → API Gateway → ImageUploader Lambda
                              ↓
                         S3 Raw Bucket
                              ↓
                         SNS Topic (Filter)
                              ↓
                    ProfanityFilter Lambda
                         ↙         ↘
                  APPROVED      REJECTED
                      ↓              ↓
              S3 Processed    DynamoDB (status)
                      ↓
                 DynamoDB
                      ↓
            ImageRetrieval Lambda
                      ↓
                  Usuario
```

## Componentes

### 1. ImageUploader Lambda
**Propósito:** Recibir y validar capturas de pantalla

**Trigger:** API Gateway (POST /upload)

**Proceso:**
1. Valida autenticación del usuario (Cognito)
2. Decodifica imagen base64
3. Valida formato y tamaño
4. Sube a S3 Raw Bucket
5. Guarda metadata en DynamoDB (status: PROCESSING)
6. Publica mensaje a SNS para iniciar filtrado

**Inputs:**
```json
{
  "image": "base64_encoded_image",
  "filename": "screenshot.png",
  "game_title": "Game Name",
  "description": "Optional description"
}
```

**Outputs:**
```json
{
  "screenshot_id": "uuid",
  "status": "PROCESSING"
}
```

### 2. ProfanityFilter Lambda
**Propósito:** Filtrar contenido inapropiado

**Trigger:** SNS Topic (mensaje de ImageUploader)

**Proceso:**
1. Recibe notificación SNS con screenshot_id
2. Descarga imagen de S3 Raw
3. Analiza contenido:
   - Revisa texto (descripción, título) contra lista de palabras prohibidas
   - (Opcional) Usa Rekognition para análisis de imagen
4. Si APROBADO:
   - Copia imagen a S3 Processed
   - Actualiza DynamoDB (status: APPROVED)
5. Si RECHAZADO:
   - Actualiza DynamoDB (status: REJECTED, reason)
6. Publica notificación a usuario vía SNS

**Configuración:**
- Lista de palabras prohibidas en código
- Rekognition (comentado por defecto para ahorrar costos)

### 3. ImageRetrieval Lambda
**Propósito:** Recuperar screenshots del usuario

**Trigger:** API Gateway (GET /screenshots)

**Proceso:**
1. Valida autenticación del usuario
2. Query DynamoDB por user_id
3. Filtra por status (default: APPROVED)
4. Genera URLs firmadas de S3 (válidas por 1 hora)
5. Retorna lista de screenshots con URLs

**Query Parameters:**
- `status` - Filtrar por status (APPROVED, REJECTED, PROCESSING)
- `limit` - Número máximo de resultados (default: 50)

**Output:**
```json
{
  "count": 10,
  "screenshots": [
    {
      "screenshot_id": "uuid",
      "game_title": "Game Name",
      "description": "Description",
      "upload_timestamp": "2025-11-26T10:00:00Z",
      "status": "APPROVED",
      "url": "https://s3.amazonaws.com/signed-url",
      "file_size": 1024000
    }
  ]
}
```

## Almacenamiento

### S3 Buckets

**Raw Bucket** (`screenshot-system-raw-screenshots`)
- Almacena imágenes originales sin procesar
- Estructura: `raw/{user_id}/{screenshot_id}.{ext}`
- Lifecycle: Eliminar después de 7 días (opcional)

**Processed Bucket** (`screenshot-system-processed-screenshots`)
- Almacena imágenes aprobadas
- Estructura: `processed/{user_id}/{screenshot_id}.{ext}`
- Lifecycle: Retención indefinida o según política

### DynamoDB Table

**Tabla:** `screenshot-system-metadata`

**Schema:**
```
screenshot_id (String, Partition Key)
user_id (String, GSI)
filename (String)
game_title (String)
description (String)
upload_timestamp (String, ISO 8601)
processed_timestamp (String, ISO 8601)
status (String) - PROCESSING | APPROVED | REJECTED
raw_s3_key (String)
processed_s3_key (String)
rejection_reason (String, opcional)
file_size (Number)
extension (String)
```

**Índices:**
- GSI: user_id + upload_timestamp (para queries por usuario)

## Mensajería (SNS)

### Filter Topic
- **Propósito:** Notificar a ProfanityFilter cuando hay nueva imagen
- **Subscribers:** ProfanityFilter Lambda

### Notification Topic
- **Propósito:** Notificar a usuarios sobre resultado del procesamiento
- **Subscribers:** Email, SMS, o Lambda para notificaciones push

## Seguridad

### IAM Roles
- Cada Lambda tiene su propio rol con permisos mínimos necesarios
- Principio de least privilege

### Autenticación
- API Gateway integrado con Cognito User Pool
- JWT tokens para autenticación

### Acceso a S3
- Buckets privados (no public access)
- URLs firmadas con expiración (1 hora)
- CloudFront con OAI para CDN (opcional)

### Validaciones
- Tamaño máximo de archivo: 10MB
- Formatos permitidos: jpg, jpeg, png, gif, webp
- Rate limiting en API Gateway

## Escalabilidad

### Lambda
- Auto-scaling automático
- Concurrency limits configurables
- Reserved concurrency para funciones críticas

### DynamoDB
- On-demand pricing (auto-scaling)
- O provisioned con auto-scaling

### S3
- Escalabilidad ilimitada
- CloudFront para distribución global (opcional)

## Monitoreo

### CloudWatch Logs
- Logs de cada Lambda
- Retention: 7-30 días

### CloudWatch Metrics
- Invocaciones de Lambda
- Errores y throttling
- Latencia
- Costos

### Alarmas Recomendadas
- Lambda errors > 5% en 5 minutos
- DynamoDB throttling
- S3 bucket size > threshold
- API Gateway 5xx errors

## Optimizaciones Futuras

### Performance
1. Agregar CloudFront para CDN
2. Implementar caching en DynamoDB con DAX
3. Usar S3 Transfer Acceleration para uploads

### Funcionalidad
1. Thumbnails automáticos (usar Pillow en ProfanityFilter)
2. Múltiples resoluciones de imagen
3. Búsqueda por game_title o tags
4. Sistema de likes/comentarios

### Costos
1. S3 Intelligent-Tiering para archivos antiguos
2. Lifecycle policies para eliminar raw después de procesamiento
3. Reserved capacity en Lambda para funciones de alto uso

## Limitaciones Actuales

1. **No hay thumbnails** - Las imágenes se sirven en tamaño completo
2. **Rekognition desactivado** - Solo filtrado básico de texto
3. **No hay CDN** - URLs directas de S3 (más lentas globalmente)
4. **Scan en DynamoDB** - Ineficiente para muchos usuarios (necesita GSI)
5. **Sin notificaciones push** - Solo SNS topics configurados

## Dependencias Externas

- **Pillow Layer:** Requerido para ProfanityFilter si se procesa imagen
- **boto3:** Incluido en runtime de Lambda
- **AWS SDK:** Para interacción con servicios AWS
