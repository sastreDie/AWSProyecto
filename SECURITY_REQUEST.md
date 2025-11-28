# Solicitud de Roles IAM - Sistema de Screenshots

## Resumen del Proyecto

Sistema de gestión de capturas de pantalla de videojuegos que permite a usuarios subir, filtrar y recuperar imágenes mediante funciones Lambda.

**Componentes:**
- 3 funciones Lambda (ImageUploader, ProfanityFilter, ImageRetrieval)
- 2 buckets S3 (raw y processed)
- 1 tabla DynamoDB (metadata)
- 2 topics SNS (notificaciones)

---

## Roles IAM Requeridos

### 1. Role: ImageUploaderRole

**Propósito:** Recibir uploads de usuarios vía API Gateway y almacenar en S3 raw

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permisos requeridos:**

| Servicio | Acciones | Recursos | Justificación |
|----------|----------|----------|---------------|
| S3 | `s3:PutObject`<br>`s3:PutObjectAcl` | `arn:aws:s3:::${PROJECT}-raw-screenshots/*` | Subir imágenes originales al bucket raw |
| DynamoDB | `dynamodb:PutItem`<br>`dynamodb:GetItem` | `arn:aws:dynamodb:${REGION}:${ACCOUNT}:table/${PROJECT}-metadata` | Guardar metadata de screenshots |
| SNS | `sns:Publish` | `arn:aws:sns:${REGION}:${ACCOUNT}:${PROJECT}-filter-topic` | Notificar al filtro de profanidad |
| CloudWatch Logs | `logs:CreateLogGroup`<br>`logs:CreateLogStream`<br>`logs:PutLogEvents` | `arn:aws:logs:${REGION}:${ACCOUNT}:log-group:/aws/lambda/*` | Logging y debugging |

---

### 2. Role: ProfanityFilterRole

**Propósito:** Analizar contenido y mover imágenes aprobadas a bucket processed

**Trust Policy:** (igual que ImageUploaderRole)

**Permisos requeridos:**

| Servicio | Acciones | Recursos | Justificación |
|----------|----------|----------|---------------|
| S3 (Read) | `s3:GetObject` | `arn:aws:s3:::${PROJECT}-raw-screenshots/*` | Leer imágenes del bucket raw |
| S3 (Write) | `s3:PutObject`<br>`s3:CopyObject` | `arn:aws:s3:::${PROJECT}-processed-screenshots/*` | Copiar imágenes aprobadas a bucket processed |
| DynamoDB | `dynamodb:GetItem`<br>`dynamodb:UpdateItem` | `arn:aws:dynamodb:${REGION}:${ACCOUNT}:table/${PROJECT}-metadata` | Actualizar status (APPROVED/REJECTED) |
| SNS | `sns:Publish` | `arn:aws:sns:${REGION}:${ACCOUNT}:${PROJECT}-notification-topic` | Notificar resultado a usuarios |
| Rekognition | `rekognition:DetectModerationLabels` | `*` | (Opcional) Detectar contenido inapropiado en imágenes |
| CloudWatch Logs | `logs:CreateLogGroup`<br>`logs:CreateLogStream`<br>`logs:PutLogEvents` | `arn:aws:logs:${REGION}:${ACCOUNT}:log-group:/aws/lambda/*` | Logging y debugging |

**Nota:** Rekognition es opcional y puede omitirse para reducir costos.

---

### 3. Role: ImageRetrievalRole

**Propósito:** Recuperar screenshots del usuario con URLs firmadas

**Trust Policy:** (igual que ImageUploaderRole)

**Permisos requeridos:**

| Servicio | Acciones | Recursos | Justificación |
|----------|----------|----------|---------------|
| DynamoDB | `dynamodb:Query`<br>`dynamodb:Scan`<br>`dynamodb:GetItem` | `arn:aws:dynamodb:${REGION}:${ACCOUNT}:table/${PROJECT}-metadata`<br>`arn:aws:dynamodb:${REGION}:${ACCOUNT}:table/${PROJECT}-metadata/index/*` | Buscar screenshots por user_id |
| S3 | `s3:GetObject` | `arn:aws:s3:::${PROJECT}-processed-screenshots/*` | Generar URLs firmadas para acceso temporal |
| CloudWatch Logs | `logs:CreateLogGroup`<br>`logs:CreateLogStream`<br>`logs:PutLogEvents` | `arn:aws:logs:${REGION}:${ACCOUNT}:log-group:/aws/lambda/*` | Logging y debugging |

---

### 4. Role: ApiGatewayRole (Opcional)

**Propósito:** Permitir a API Gateway escribir logs en CloudWatch

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permisos:** Managed Policy `arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs`

---

## Principios de Seguridad Aplicados

✅ **Least Privilege:** Cada rol solo tiene permisos mínimos necesarios  
✅ **Resource Scoping:** Permisos limitados a recursos específicos del proyecto  
✅ **Separation of Duties:** Cada Lambda tiene su propio rol independiente  
✅ **No Wildcards:** Recursos específicos (excepto Rekognition que lo requiere)  

---

## Naming Convention Sugerida

Recomendamos usar el prefijo del proyecto para facilitar identificación:

```
Roles:
- screenshot-system-image-uploader-role
- screenshot-system-profanity-filter-role
- screenshot-system-image-retrieval-role
- screenshot-system-apigateway-role

Policies (inline):
- ImageUploaderPolicy
- ProfanityFilterPolicy
- ImageRetrievalPolicy
```

---

## CloudFormation Template

Adjunto el template completo en `iac/iam-stack.yaml` que pueden:

1. **Desplegar directamente** si se ajusta a sus políticas
2. **Adaptar** a su estructura de roles existente
3. **Usar como referencia** para crear los roles manualmente

**Comando para desplegar:**
```bash
aws cloudformation create-stack \
  --stack-name screenshot-system-iam \
  --template-body file://iac/iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=ProjectName,ParameterValue=screenshot-system
```

---

## Outputs Necesarios

Una vez creados los roles, necesito los siguientes ARNs para configurar las funciones Lambda:

```
ImageUploaderRoleArn: arn:aws:iam::ACCOUNT:role/...
ProfanityFilterRoleArn: arn:aws:iam::ACCOUNT:role/...
ImageRetrievalRoleArn: arn:aws:iam::ACCOUNT:role/...
ApiGatewayRoleArn: arn:aws:iam::ACCOUNT:role/... (opcional)
```

---

## Consideraciones Adicionales

### Rekognition
- **Costo:** ~$1 USD por 1000 imágenes analizadas
- **Alternativa:** Desactivar y usar solo filtrado de texto (implementado actualmente)
- **Recomendación:** Omitir permiso inicialmente, agregar después si es necesario

### DynamoDB Scan
- `dynamodb:Scan` en ImageRetrieval es ineficiente para producción
- **Recomendación:** Crear GSI (Global Secondary Index) en `user_id` y usar `dynamodb:Query`
- Puedo actualizar el código para usar Query en lugar de Scan

### CloudWatch Logs Retention
- Sugerencia: Configurar retention de 7-30 días para reducir costos

---

## Preguntas Frecuentes

**Q: ¿Por qué S3 necesita PutObjectAcl?**  
A: Para configurar permisos del objeto al subirlo. Puede omitirse si no se requiere.

**Q: ¿Por qué Rekognition usa wildcard (*)?**  
A: Es requerimiento del servicio, no soporta resource-level permissions.

**Q: ¿Necesitan acceso a otros buckets S3?**  
A: No, solo a los 2 buckets específicos del proyecto.

**Q: ¿Las Lambdas necesitan acceso a VPC?**  
A: No, todos los servicios son públicos de AWS.

---

## Proceso de Deployment

### ¿Quién ejecuta qué?

**EQUIPO DE SEGURIDAD (ustedes):**
1. Revisar este documento y el template `iac/iam-stack.yaml`
2. Aprobar o solicitar cambios en los permisos
3. **Ejecutar el IAM stack** desde su cuenta con permisos administrativos:
   ```bash
   aws cloudformation create-stack \
     --stack-name screenshot-system-iam \
     --template-body file://iac/iam-stack.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameters ParameterKey=ProjectName,ParameterValue=screenshot-system
   ```
4. Obtener los ARNs de los roles creados (outputs del stack)
5. Enviar los ARNs al equipo de desarrollo

**EQUIPO DE DESARROLLO (nosotros):**
1. Recibir los ARNs de los roles
2. Usar esos ARNs en el `infrastructure-stack.yaml`
3. Desplegar la infraestructura (Lambdas, S3, DynamoDB, etc.)

### ¿Por qué este flujo?

✅ **Separación de responsabilidades:** Seguridad controla IAM, desarrollo controla aplicación  
✅ **Cumplimiento:** Solo el equipo de seguridad tiene permisos de IAM  
✅ **Auditoría:** Todos los roles IAM son creados por un equipo centralizado  
✅ **Seguridad:** Desarrollo no puede escalar privilegios  

---

## Outputs que necesitamos

Después de ejecutar el IAM stack, por favor envíennos estos ARNs:

```
ImageUploaderRoleArn: arn:aws:iam::ACCOUNT:role/screenshot-system-image-uploader-role
ProfanityFilterRoleArn: arn:aws:iam::ACCOUNT:role/screenshot-system-profanity-filter-role
ImageRetrievalRoleArn: arn:aws:iam::ACCOUNT:role/screenshot-system-image-retrieval-role
ApiGatewayRoleArn: arn:aws:iam::ACCOUNT:role/screenshot-system-apigateway-role
```

Pueden obtenerlos con:
```bash
aws cloudformation describe-stacks \
  --stack-name screenshot-system-iam \
  --query 'Stacks[0].Outputs'
```

---

## Contacto

Para dudas o ajustes a los permisos, contactar a:
- **Desarrollador:** [Tu Nombre]
- **Email:** [Tu Email]
- **Proyecto:** Screenshot Management System

---

## Anexos

- `iac/iam-stack.yaml` - Template completo de CloudFormation
- `DEPLOYMENT_INSTRUCTIONS.md` - Guía paso a paso del deployment
- `ARCHITECTURE.md` - Diagrama de arquitectura del sistema
