# Tests

## Tests Unitarios (Mocks)

Usan simulaciones de AWS, no requieren conexión ni costos:

```bash
# Ejecutar todos los tests unitarios
python tests/run_all_tests.py

# O individuales
python tests/test_image_uploader.py
python tests/test_profanity_filter.py
python tests/test_image_retrieval.py
```

**Ventajas:**
- ✅ Rápidos
- ✅ Sin costos
- ✅ No requieren AWS configurado
- ✅ Prueban la lógica del código

## Test de Integración (AWS Real)

Usa AWS real con imágenes reales:

```bash
python tests/integration_test.py
```

**Antes de ejecutar:**

1. Configura las variables de entorno en `integration_test.py`:
   ```python
   os.environ['RAW_BUCKET'] = 'tu-bucket-raw'
   os.environ['PROCESSED_BUCKET'] = 'tu-bucket-processed'
   os.environ['METADATA_TABLE'] = 'tu-tabla-dynamodb'
   os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:...'
   ```

2. Asegúrate de tener AWS CLI configurado:
   ```bash
   aws configure
   ```

3. (Opcional) Coloca una imagen de prueba en `tests/test_image.png`

**Advertencias:**
- ⚠️ Usa recursos reales de AWS
- ⚠️ Puede generar costos mínimos
- ⚠️ Crea archivos en S3 y registros en DynamoDB
- ⚠️ Recuerda limpiar los datos de prueba después

**Lo que prueba:**
- Upload real a S3
- Escritura en DynamoDB
- Procesamiento de filtro
- Generación de URLs firmadas
- Flujo completo end-to-end

## Agregar Imagen de Prueba

Puedes usar cualquier imagen PNG/JPG:

```bash
# Copiar una imagen existente
copy C:\ruta\a\tu\imagen.png tests\test_image.png

# O descargar una
curl -o tests/test_image.png https://via.placeholder.com/150
```

Si no agregas imagen, el test creará una automáticamente con Pillow.
