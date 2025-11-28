# Estimación de Costos - Screenshot Management System

## Resumen Ejecutivo

**Costo Mensual Estimado:** $15 - $50 USD/mes (uso bajo-medio)  
**Costo por 1000 usuarios activos:** ~$100 - $200 USD/mes

---

## Supuestos de Uso

### Escenario Base (Uso Bajo)
- **Usuarios activos:** 100 usuarios/mes
- **Screenshots por usuario:** 10 imágenes/mes
- **Total screenshots:** 1,000 imágenes/mes
- **Tamaño promedio:** 2 MB por imagen
- **Retención:** 30 días para raw, 1 año para processed

### Escenario Medio
- **Usuarios activos:** 1,000 usuarios/mes
- **Screenshots por usuario:** 20 imágenes/mes
- **Total screenshots:** 20,000 imágenes/mes
- **Tamaño promedio:** 2 MB por imagen

---

## Desglose de Costos por Servicio

### 1. AWS Lambda

**Pricing:**
- $0.20 por 1 millón de requests
- $0.0000166667 por GB-segundo de compute

**Uso Estimado (Escenario Base):**
- Image Uploader: 1,000 invocaciones × 512 MB × 2 seg = 1,024 GB-seg
- Profanity Filter: 1,000 invocaciones × 1024 MB × 5 seg = 5,120 GB-seg
- Image Retrieval: 5,000 invocaciones × 512 MB × 1 seg = 2,560 GB-seg

**Cálculo:**
```
Requests: 7,000 × $0.20 / 1,000,000 = $0.0014
Compute: 8,704 GB-seg × $0.0000166667 = $0.15
Total Lambda: ~$0.15/mes
```

**Escenario Medio:** ~$3.00/mes

---

### 2. Amazon S3

**Pricing:**
- Storage: $0.023 per GB/mes (Standard)
- PUT requests: $0.005 per 1,000 requests
- GET requests: $0.0004 per 1,000 requests

**Uso Estimado (Escenario Base):**
- Raw bucket: 1,000 images × 2 MB × 30 días = ~2 GB
- Processed bucket: 1,000 images × 2 MB × 365 días = ~24 GB
- PUT requests: 2,000 (upload + copy)
- GET requests: 5,000

**Cálculo:**
```
Storage: 26 GB × $0.023 = $0.60
PUT: 2,000 × $0.005 / 1,000 = $0.01
GET: 5,000 × $0.0004 / 1,000 = $0.002
Total S3: ~$0.61/mes
```

**Escenario Medio:** ~$12.00/mes

---

### 3. Amazon DynamoDB

**Pricing:**
- On-Demand: $1.25 per million write requests
- On-Demand: $0.25 per million read requests
- Storage: $0.25 per GB/mes

**Uso Estimado (Escenario Base):**
- Write requests: 2,000 (insert + update)
- Read requests: 6,000 (queries)
- Storage: ~0.1 GB (metadata)

**Cálculo:**
```
Writes: 2,000 × $1.25 / 1,000,000 = $0.0025
Reads: 6,000 × $0.25 / 1,000,000 = $0.0015
Storage: 0.1 GB × $0.25 = $0.025
Total DynamoDB: ~$0.03/mes
```

**Escenario Medio:** ~$0.60/mes

---

### 4. Amazon SNS

**Pricing:**
- $0.50 per 1 million requests
- $0.09 per GB data transfer

**Uso Estimado (Escenario Base):**
- Notifications: 2,000 messages
- Data transfer: ~0.01 GB

**Cálculo:**
```
Requests: 2,000 × $0.50 / 1,000,000 = $0.001
Data: 0.01 GB × $0.09 = $0.0009
Total SNS: ~$0.002/mes
```

**Escenario Medio:** ~$0.04/mes

---

### 5. Amazon API Gateway

**Pricing:**
- $3.50 per million API calls
- $0.09 per GB data transfer

**Uso Estimado (Escenario Base):**
- API calls: 6,000 (upload + retrieve)
- Data transfer: ~12 GB (6 GB in + 6 GB out)

**Cálculo:**
```
API Calls: 6,000 × $3.50 / 1,000,000 = $0.021
Data Transfer: 12 GB × $0.09 = $1.08
Total API Gateway: ~$1.10/mes
```

**Escenario Medio:** ~$22.00/mes

---

### 6. Amazon Cognito

**Pricing:**
- Free tier: 50,000 MAU (Monthly Active Users)
- $0.0055 per MAU después del free tier

**Uso Estimado:**
- 100 MAU (dentro del free tier)

**Cálculo:**
```
Total Cognito: $0.00/mes (free tier)
```

**Escenario Medio (1,000 MAU):** $0.00/mes (free tier)

---

### 7. Amazon CloudFront

**Pricing:**
- $0.085 per GB data transfer (primeros 10 TB)
- $0.0075 per 10,000 HTTP requests

**Uso Estimado (Escenario Base):**
- Data transfer: 10 GB (imágenes servidas)
- Requests: 5,000

**Cálculo:**
```
Data Transfer: 10 GB × $0.085 = $0.85
Requests: 5,000 × $0.0075 / 10,000 = $0.004
Total CloudFront: ~$0.85/mes
```

**Escenario Medio:** ~$17.00/mes

---

### 8. Amazon Rekognition (Opcional)

**Pricing:**
- $1.00 per 1,000 images analyzed

**Uso Estimado (Escenario Base):**
- 1,000 images analyzed

**Cálculo:**
```
Total Rekognition: 1,000 × $1.00 / 1,000 = $1.00/mes
```

**Escenario Medio:** ~$20.00/mes

**Nota:** Actualmente implementado con filtrado básico de texto. Rekognition es opcional.

---

### 9. VPC Networking

**Pricing:**
- NAT Gateway: $0.045 per hour + $0.045 per GB processed
- VPC Endpoints: $0.01 per hour per AZ

**Uso Estimado:**
- NAT Gateway: 730 horas/mes
- Data processed: 20 GB
- VPC Endpoints (S3 + DynamoDB): 2 × 730 horas

**Cálculo:**
```
NAT Gateway Hours: 730 × $0.045 = $32.85
NAT Gateway Data: 20 GB × $0.045 = $0.90
VPC Endpoints: 2 × 730 × $0.01 = $14.60
Total VPC: ~$48.35/mes
```

**Escenario Medio:** ~$65.00/mes

**⚠️ NOTA IMPORTANTE:** El NAT Gateway es el componente más caro. Considerar alternativas:
- Usar solo VPC Endpoints (elimina necesidad de NAT Gateway para S3/DynamoDB)
- Usar Lambda sin VPC si no es requerimiento estricto

---

### 10. AWS KMS

**Pricing:**
- $1.00 per customer managed key/mes
- $0.03 per 10,000 requests

**Uso Estimado:**
- 1 customer managed key
- 10,000 encrypt/decrypt requests

**Cálculo:**
```
Key: $1.00
Requests: 10,000 × $0.03 / 10,000 = $0.03
Total KMS: ~$1.03/mes
```

**Escenario Medio:** ~$1.06/mes

---

### 11. CloudWatch Logs

**Pricing:**
- $0.50 per GB ingested
- $0.03 per GB stored

**Uso Estimado (Escenario Base):**
- Logs ingested: 1 GB/mes
- Logs stored: 2 GB (retention 30 días)

**Cálculo:**
```
Ingestion: 1 GB × $0.50 = $0.50
Storage: 2 GB × $0.03 = $0.06
Total CloudWatch: ~$0.56/mes
```

**Escenario Medio:** ~$2.00/mes

---

## Resumen de Costos

### Escenario Base (100 usuarios, 1,000 screenshots/mes)

| Servicio | Costo Mensual |
|----------|---------------|
| Lambda | $0.15 |
| S3 | $0.61 |
| DynamoDB | $0.03 |
| SNS | $0.002 |
| API Gateway | $1.10 |
| Cognito | $0.00 (free tier) |
| CloudFront | $0.85 |
| Rekognition | $1.00 (opcional) |
| VPC (NAT + Endpoints) | $48.35 |
| KMS | $1.03 |
| CloudWatch | $0.56 |
| **TOTAL** | **~$53.67/mes** |
| **Sin Rekognition** | **~$52.67/mes** |

### Escenario Medio (1,000 usuarios, 20,000 screenshots/mes)

| Servicio | Costo Mensual |
|----------|---------------|
| Lambda | $3.00 |
| S3 | $12.00 |
| DynamoDB | $0.60 |
| SNS | $0.04 |
| API Gateway | $22.00 |
| Cognito | $0.00 (free tier) |
| CloudFront | $17.00 |
| Rekognition | $20.00 (opcional) |
| VPC (NAT + Endpoints) | $65.00 |
| KMS | $1.06 |
| CloudWatch | $2.00 |
| **TOTAL** | **~$142.70/mes** |
| **Sin Rekognition** | **~$122.70/mes** |

---

## Optimizaciones de Costo

### 1. Eliminar NAT Gateway (-$33/mes)
**Impacto:** Las Lambdas no podrán acceder a internet (solo a servicios AWS vía VPC Endpoints)
**Recomendación:** Si solo usas servicios AWS (S3, DynamoDB, SNS), usa VPC Endpoints y elimina NAT Gateway

**Ahorro:** ~$33/mes

### 2. Usar Lambda sin VPC (-$48/mes)
**Impacto:** Menos aislamiento de red, pero funcional
**Recomendación:** Si no es requerimiento estricto de seguridad

**Ahorro:** ~$48/mes

### 3. Desactivar Rekognition (-$1-20/mes)
**Impacto:** Solo filtrado de texto, sin análisis de imagen
**Recomendación:** Activar solo si es necesario

**Ahorro:** $1-20/mes según uso

### 4. Reducir retención de logs (-$0.20/mes)
**Impacto:** Menos histórico para debugging
**Recomendación:** Retención de 7 días en lugar de 30

**Ahorro:** ~$0.20/mes

### 5. Usar S3 Intelligent-Tiering (-$0.10/mes)
**Impacto:** Ninguno, ahorro automático
**Recomendación:** Activar para imágenes poco accedidas

**Ahorro:** ~10-30% en storage

---

## Costo por Usuario

### Escenario Base
```
$52.67 / 100 usuarios = $0.53 por usuario/mes
```

### Escenario Medio
```
$122.70 / 1,000 usuarios = $0.12 por usuario/mes
```

**Conclusión:** El costo por usuario disminuye con escala debido a costos fijos (VPC, KMS).

---

## Costo Optimizado (Sin VPC, Sin Rekognition)

### Escenario Base Optimizado

| Servicio | Costo Mensual |
|----------|---------------|
| Lambda | $0.15 |
| S3 | $0.61 |
| DynamoDB | $0.03 |
| SNS | $0.002 |
| API Gateway | $1.10 |
| Cognito | $0.00 |
| CloudFront | $0.85 |
| KMS | $1.03 |
| CloudWatch | $0.56 |
| **TOTAL OPTIMIZADO** | **~$4.33/mes** |

### Escenario Medio Optimizado

| Servicio | Costo Mensual |
|----------|---------------|
| Lambda | $3.00 |
| S3 | $12.00 |
| DynamoDB | $0.60 |
| SNS | $0.04 |
| API Gateway | $22.00 |
| Cognito | $0.00 |
| CloudFront | $17.00 |
| KMS | $1.06 |
| CloudWatch | $2.00 |
| **TOTAL OPTIMIZADO** | **~$57.70/mes** |

---

## Free Tier (Primer Año AWS)

Durante el primer año, algunos servicios tienen free tier:

- **Lambda:** 1M requests/mes + 400,000 GB-seg/mes
- **S3:** 5 GB storage + 20,000 GET + 2,000 PUT
- **DynamoDB:** 25 GB storage + 25 WCU + 25 RCU
- **API Gateway:** 1M API calls/mes (12 meses)
- **CloudWatch:** 5 GB logs + 10 métricas custom

**Costo estimado primer año (Escenario Base):** ~$35/mes (principalmente VPC)

---

## Recomendaciones Finales

### Para Desarrollo/Testing
- **Sin VPC:** $4-8/mes
- Usar free tier al máximo
- Desactivar Rekognition

### Para Producción (Bajo Volumen)
- **Con VPC optimizado:** $20-30/mes
- Solo VPC Endpoints, sin NAT Gateway
- Rekognition opcional

### Para Producción (Alto Volumen)
- **Con VPC completo:** $100-150/mes
- NAT Gateway para flexibilidad
- Rekognition activado
- Considerar Reserved Capacity para DynamoDB

---

## Monitoreo de Costos

### Configurar Alertas
1. AWS Budgets: Alerta a $50/mes
2. Cost Explorer: Revisar semanalmente
3. CloudWatch Billing Alarms

### Métricas Clave
- Costo por usuario activo
- Costo por screenshot procesado
- Costo de VPC vs beneficio de aislamiento

---

## Calculadora AWS

Para estimaciones más precisas según tu uso específico:
https://calculator.aws/

**Inputs recomendados:**
- Región: us-east-1
- Usuarios activos mensuales
- Screenshots por usuario
- Tamaño promedio de imagen
- Retención de datos

---

## Conclusión

**Costo Base Realista:** $50-60/mes con VPC completo  
**Costo Optimizado:** $5-10/mes sin VPC  
**Escalabilidad:** Costo por usuario disminuye con volumen

**Decisión clave:** ¿Es necesario el aislamiento VPC? Si no, ahorra ~$48/mes.

---

*Última actualización: Enero 2025*  
*Precios basados en región us-east-1*  
*Consultar precios actuales en: https://aws.amazon.com/pricing/*
