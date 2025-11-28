# Guía de Implementación - Sistema de Screenshots

## Arquitectura

Este sistema procesa capturas de pantalla de videojuegos con 3 funciones Lambda:

1. **ImageUploader** - Recibe uploads vía API Gateway
2. **ProfanityFilter** - Filtra contenido inapropiado
3. **ImageRetrieval** - Devuelve imágenes a usuarios

## Prerequisitos

- AWS CLI configurado
- Permisos para desplegar CloudFormation
- Layer de Pillow ya subido a Lambda
- Equipo de seguridad debe aprobar/crear roles IAM

## Paso 1: Roles IAM (Equipo de Seguridad)

Envía `iac/iam-stack.yaml` al equipo de seguridad para que creen los roles necesarios.

**Permisos requeridos por Lambda:**

### ImageUploader
```
- s3:PutObject en bucket raw
- dynamodb:PutItem, GetItem en tabla metadata
- sns:Publish en topic de filtrado
- logs:* para CloudWatch
```

### ProfanityFilter
```
- s3:GetObject en bucket raw
- s3:PutObject, CopyObject en bucket processed
- dynamodb:GetItem, UpdateItem en tabla metadata
- sns:Publish en topic de notificaciones
- rekognition:DetectModerationLabels (opcional)
- logs:* para CloudWatch
```

### ImageRetrieval
```
- dynamodb:Query, Scan, GetItem en tabla metadata
- s3:GetObject en bucket processed
- logs:* para CloudWatch
```

**Solicita los ARNs de los roles creados.**

## Paso 2: Desplegar Infraestructura

```bash
# Despliega buckets S3, DynamoDB, SNS
aws cloudformation create-stack \
  --stack-name gaming-screenshots-infra \
  --template-body file://iac/infrastructure-stack.yaml \
  --parameters ParameterKey=ProjectName,ParameterValue=screenshot-system

# Espera a que termine
aws cloudformation wait stack-create-complete --stack-name gaming-screenshots-infra
```

**Recursos creados:**
- 2 buckets S3 (raw y processed)
- 1 tabla DynamoDB (metadata)
- 2 topics SNS (filter y notifications)

## Paso 3: Empaquetar Funciones Lambda

```bash
cd src/lambda

# Empaqueta cada función
zip -r ../../image_uploader.zip image_uploader.py
zip -r ../../profanity_filter.zip profanity_filter.py
zip -r ../../image_retrieval.zip image_retrieval.py

cd ../..
```

## Paso 4: Crear Funciones Lambda

Reemplaza `ROLE_ARN` con los ARNs que te dio el equipo de seguridad.

```bash
# ImageUploader
aws lambda create-function \
  --function-name ImageUploader \
  --runtime python3.12 \
  --role ROLE_ARN_IMAGE_UPLOADER \
  --handler image_uploader.lambda_handler \
  --zip-file fileb://image_uploader.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    RAW_BUCKET=screenshot-system-raw-screenshots,
    METADATA_TABLE=screenshot-system-metadata,
    SNS_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT:screenshot-system-filter-topic
  }"

# ProfanityFilter
aws lambda create-function \
  --function-name ProfanityFilter \
  --runtime python3.12 \
  --role ROLE_ARN_PROFANITY_FILTER \
  --handler profanity_filter.lambda_handler \
  --zip-file fileb://profanity_filter.zip \
  --timeout 60 \
  --memory-size 1024 \
  --environment Variables="{
    RAW_BUCKET=screenshot-system-raw-screenshots,
    PROCESSED_BUCKET=screenshot-system-processed-screenshots,
    METADATA_TABLE=screenshot-system-metadata,
    NOTIFICATION_TOPIC_ARN=arn:aws:sns:REGION:ACCOUNT:screenshot-system-notification-topic
  }"

# ImageRetrieval
aws lambda create-function \
  --function-name ImageRetrieval \
  --runtime python3.12 \
  --role ROLE_ARN_IMAGE_RETRIEVAL \
  --handler image_retrieval.lambda_handler \
  --zip-file fileb://image_retrieval.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{
    PROCESSED_BUCKET=screenshot-system-processed-screenshots,
    METADATA_TABLE=screenshot-system-metadata
  }"
```

## Paso 5: Agregar Layer de Pillow

Obtén el ARN de tu layer existente y agrégalo a ProfanityFilter:

```bash
aws lambda update-function-configuration \
  --function-name ProfanityFilter \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:pillow-layer:VERSION
```

## Paso 6: Configurar Triggers

### SNS Trigger para ProfanityFilter
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT:screenshot-system-filter-topic \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:REGION:ACCOUNT:function:ProfanityFilter

aws lambda add-permission \
  --function-name ProfanityFilter \
  --statement-id sns-invoke \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:REGION:ACCOUNT:screenshot-system-filter-topic
```

### API Gateway (opcional - para exponer las funciones)
```bash
# Crear API REST
aws apigateway create-rest-api \
  --name ScreenshotAPI \
  --description "API for screenshot management"

# Configurar recursos y métodos (POST /upload, GET /screenshots)
# Ver documentación de API Gateway para detalles completos
```

## Paso 7: Verificar Deployment

```bash
# Listar funciones Lambda
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `Image`) || starts_with(FunctionName, `Profanity`)].FunctionName'

# Ver logs de una función
aws logs tail /aws/lambda/ImageUploader --follow

# Probar una función
aws lambda invoke \
  --function-name ImageUploader \
  --payload '{"body": "{\"test\": true}"}' \
  response.json
```

## Variables de Entorno Requeridas

### ImageUploader
- `RAW_BUCKET` - Nombre del bucket S3 raw
- `METADATA_TABLE` - Nombre de la tabla DynamoDB
- `SNS_TOPIC_ARN` - ARN del topic SNS para filtrado

### ProfanityFilter
- `RAW_BUCKET` - Bucket S3 raw
- `PROCESSED_BUCKET` - Bucket S3 processed
- `METADATA_TABLE` - Tabla DynamoDB
- `NOTIFICATION_TOPIC_ARN` - ARN del topic SNS para notificaciones

### ImageRetrieval
- `PROCESSED_BUCKET` - Bucket S3 processed
- `METADATA_TABLE` - Tabla DynamoDB
- `CLOUDFRONT_DOMAIN` - (Opcional) Dominio de CloudFront
- `CLOUDFRONT_KEY_PAIR_ID` - (Opcional) Key pair ID de CloudFront

## Troubleshooting

### Error: Access Denied
- Verifica que los roles IAM tengan los permisos correctos
- Revisa que los nombres de recursos coincidan

### Error: Module not found (PIL)
- Asegúrate de que el layer de Pillow esté agregado a la función
- Verifica que el layer sea compatible con Python 3.12

### Lambda Timeout
- Aumenta el timeout en la configuración de Lambda
- Revisa los logs en CloudWatch para identificar el cuello de botella

### DynamoDB Throttling
- Aumenta la capacidad de lectura/escritura de la tabla
- Considera usar on-demand pricing

## Costos Estimados (uso moderado)

- Lambda: ~$5-10/mes
- S3: ~$1-5/mes (depende del almacenamiento)
- DynamoDB: ~$1-3/mes
- SNS: ~$0.50/mes
- Rekognition: ~$1 por 1000 imágenes (si se activa)

## Próximos Pasos

1. Configurar API Gateway con autenticación (Cognito)
2. Agregar CloudFront para CDN
3. Activar Rekognition para detección real de contenido
4. Implementar notificaciones a usuarios
5. Agregar métricas y alarmas en CloudWatch
