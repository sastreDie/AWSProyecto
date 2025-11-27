"""
Test de Integración - Usa AWS REAL
ADVERTENCIA: Este test crea recursos reales en AWS y puede generar costos
"""
import json
import base64
import sys
import os
import time
from pathlib import Path

# Configurar variables de entorno con tus recursos REALES
# MODIFICA ESTOS VALORES CON TUS RECURSOS DE AWS
os.environ['RAW_BUCKET'] = 'screenshot-system-raw-screenshots'  # Cambia esto
os.environ['PROCESSED_BUCKET'] = 'screenshot-system-processed-screenshots'  # Cambia esto
os.environ['METADATA_TABLE'] = 'screenshot-system-metadata'  # Cambia esto
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:screenshot-system-filter-topic'  # Cambia esto
os.environ['NOTIFICATION_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:screenshot-system-notification-topic'  # Cambia esto

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda'))

import boto3
from image_uploader import lambda_handler as uploader_handler
from profanity_filter import lambda_handler as filter_handler
from image_retrieval import lambda_handler as retrieval_handler

# Clientes AWS reales
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def create_test_image():
    """Crea una imagen PNG de prueba simple"""
    from PIL import Image
    import io
    
    # Crear imagen de 100x100 con texto
    img = Image.new('RGB', (100, 100), color='blue')
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()

def load_real_image(image_path):
    """Carga una imagen real desde el disco"""
    if not os.path.exists(image_path):
        print(f"⚠️  Imagen no encontrada: {image_path}")
        return None
    
    with open(image_path, 'rb') as f:
        return f.read()

def test_full_workflow():
    """Test completo: Upload -> Filter -> Retrieval"""
    print("\n" + "="*60)
    print("🧪 TEST DE INTEGRACIÓN COMPLETO")
    print("="*60)
    
    # 1. Crear o cargar imagen
    print("\n📸 Paso 1: Preparando imagen...")
    
    # Opción A: Usar imagen real si existe
    test_image_path = "tests/test_image.png"
    image_bytes = load_real_image(test_image_path)
    
    # Opción B: Crear imagen de prueba si no existe
    if not image_bytes:
        print("   Creando imagen de prueba con Pillow...")
        try:
            image_bytes = create_test_image()
        except ImportError:
            print("   ⚠️  Pillow no instalado. Usando PNG mínimo...")
            # PNG mínimo válido (1x1 pixel)
            image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    print(f"   ✅ Imagen lista ({len(image_bytes)} bytes)")
    
    # 2. Test ImageUploader
    print("\n📤 Paso 2: Subiendo imagen (ImageUploader)...")
    
    upload_event = {
        'body': json.dumps({
            'image': image_base64,
            'filename': 'integration_test.png',
            'game_title': 'Test Game',
            'description': 'Integration test screenshot'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'integration-test-user'
                }
            }
        }
    }
    
    try:
        upload_response = uploader_handler(upload_event, {})
        print(f"   Status: {upload_response['statusCode']}")
        
        if upload_response['statusCode'] != 200:
            print(f"   ❌ Error: {upload_response['body']}")
            return False
        
        body = json.loads(upload_response['body'])
        screenshot_id = body['screenshot_id']
        print(f"   ✅ Screenshot ID: {screenshot_id}")
        
    except Exception as e:
        print(f"   ❌ Error en upload: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Verificar en S3
    print("\n☁️  Paso 3: Verificando en S3...")
    try:
        s3_key = f"raw/integration-test-user/{screenshot_id}.png"
        s3.head_object(Bucket=os.environ['RAW_BUCKET'], Key=s3_key)
        print(f"   ✅ Archivo encontrado en S3: {s3_key}")
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar S3: {e}")
    
    # 4. Verificar en DynamoDB
    print("\n💾 Paso 4: Verificando en DynamoDB...")
    try:
        table = dynamodb.Table(os.environ['METADATA_TABLE'])
        item = table.get_item(Key={'screenshot_id': screenshot_id})
        
        if 'Item' in item:
            print(f"   ✅ Metadata encontrada:")
            print(f"      Status: {item['Item']['status']}")
            print(f"      User: {item['Item']['user_id']}")
        else:
            print(f"   ⚠️  Item no encontrado en DynamoDB")
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar DynamoDB: {e}")
    
    # 5. Test ProfanityFilter (simular SNS trigger)
    print("\n🔍 Paso 5: Ejecutando filtro de profanidad...")
    
    filter_event = {
        'Records': [
            {
                'Sns': {
                    'Message': json.dumps({
                        'screenshot_id': screenshot_id,
                        'user_id': 'integration-test-user',
                        's3_key': s3_key,
                        'bucket': os.environ['RAW_BUCKET']
                    })
                }
            }
        ]
    }
    
    try:
        filter_response = filter_handler(filter_event, {})
        print(f"   Status: {filter_response['statusCode']}")
        print(f"   ✅ Filtro ejecutado")
        
        # Esperar un poco para que se procese
        time.sleep(2)
        
    except Exception as e:
        print(f"   ⚠️  Error en filtro: {e}")
    
    # 6. Verificar estado después del filtro
    print("\n📊 Paso 6: Verificando estado final...")
    try:
        item = table.get_item(Key={'screenshot_id': screenshot_id})
        
        if 'Item' in item:
            final_status = item['Item']['status']
            print(f"   ✅ Status final: {final_status}")
            
            if final_status == 'APPROVED':
                print(f"   ✅ Screenshot APROBADO")
                if 'processed_s3_key' in item['Item']:
                    print(f"   ✅ Procesado en: {item['Item']['processed_s3_key']}")
            elif final_status == 'REJECTED':
                print(f"   ⚠️  Screenshot RECHAZADO")
                if 'rejection_reason' in item['Item']:
                    print(f"      Razón: {item['Item']['rejection_reason']}")
        
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar estado: {e}")
    
    # 7. Test ImageRetrieval
    print("\n📥 Paso 7: Recuperando screenshots (ImageRetrieval)...")
    
    retrieval_event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'integration-test-user'
                }
            }
        },
        'queryStringParameters': {
            'status': 'APPROVED',
            'limit': '10'
        }
    }
    
    try:
        retrieval_response = retrieval_handler(retrieval_event, {})
        print(f"   Status: {retrieval_response['statusCode']}")
        
        if retrieval_response['statusCode'] == 200:
            body = json.loads(retrieval_response['body'])
            print(f"   ✅ Screenshots encontrados: {body['count']}")
            
            if body['count'] > 0:
                for screenshot in body['screenshots'][:3]:  # Mostrar primeros 3
                    print(f"      - {screenshot['screenshot_id']}: {screenshot['status']}")
                    if 'url' in screenshot:
                        print(f"        URL: {screenshot['url'][:80]}...")
        
    except Exception as e:
        print(f"   ⚠️  Error en retrieval: {e}")
    
    print("\n" + "="*60)
    print("✅ TEST DE INTEGRACIÓN COMPLETADO")
    print("="*60)
    print("\n⚠️  LIMPIEZA: Recuerda eliminar los recursos de prueba:")
    print(f"   - S3: {s3_key}")
    print(f"   - DynamoDB: screenshot_id={screenshot_id}")
    
    return True

def cleanup_test_data(screenshot_id):
    """Limpia los datos de prueba (opcional)"""
    print("\n🧹 Limpiando datos de prueba...")
    
    try:
        # Eliminar de S3
        s3_key = f"raw/integration-test-user/{screenshot_id}.png"
        s3.delete_object(Bucket=os.environ['RAW_BUCKET'], Key=s3_key)
        print(f"   ✅ Eliminado de S3: {s3_key}")
        
        # Eliminar de DynamoDB
        table = dynamodb.Table(os.environ['METADATA_TABLE'])
        table.delete_item(Key={'screenshot_id': screenshot_id})
        print(f"   ✅ Eliminado de DynamoDB: {screenshot_id}")
        
    except Exception as e:
        print(f"   ⚠️  Error en limpieza: {e}")

if __name__ == '__main__':
    print("\n⚠️  ADVERTENCIA: Este test usa AWS REAL")
    print("   - Asegúrate de configurar las variables de entorno correctamente")
    print("   - Verifica que tienes credenciales AWS configuradas")
    print("   - Este test puede generar costos mínimos en AWS")
    
    response = input("\n¿Continuar? (y/n): ")
    
    if response.lower() == 'y':
        try:
            test_full_workflow()
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Test cancelado")
