"""
Test local para ImageUploader Lambda
Simula el evento de API Gateway
"""
import json
import base64
import sys
import os

# Configurar variables de entorno ANTES de importar
os.environ['RAW_BUCKET'] = 'test-raw-bucket'
os.environ['METADATA_TABLE'] = 'test-metadata-table'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:test-topic'

# Agregar el path de las lambdas
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Mock de boto3 para testing local
class MockS3:
    def put_object(self, **kwargs):
        print(f"[MOCK S3] Subiendo a bucket: {kwargs['Bucket']}, key: {kwargs['Key']}")
        return {'ETag': 'mock-etag'}

class MockDynamoDB:
    def Table(self, name):
        return MockTable(name)

class MockTable:
    def __init__(self, name):
        self.name = name
    
    def put_item(self, Item):
        print(f"[MOCK DynamoDB] Guardando en tabla {self.name}:")
        print(json.dumps(Item, indent=2, default=str))
        return {}

class MockSNS:
    def publish(self, **kwargs):
        print(f"[MOCK SNS] Publicando a topic: {kwargs['TopicArn']}")
        print(f"Mensaje: {kwargs['Message']}")
        return {'MessageId': 'mock-message-id'}

# Reemplazar boto3 con mocks
import boto3
boto3.client = lambda service: MockS3() if service == 's3' else MockSNS()
boto3.resource = lambda service: MockDynamoDB()

# Ahora importar la función
from image_uploader import lambda_handler

def test_upload_success():
    """Test de upload exitoso"""
    print("\n=== TEST: Upload Exitoso ===\n")
    
    # Crear una imagen fake en base64 (1x1 pixel PNG)
    fake_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    image_base64 = base64.b64encode(fake_image).decode('utf-8')
    
    event = {
        'body': json.dumps({
            'image': image_base64,
            'filename': 'test_screenshot.png',
            'game_title': 'Test Game',
            'description': 'Test description'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'screenshot_id' in body
    print("\n✅ Test pasado!")

def test_upload_missing_fields():
    """Test de validación - campos faltantes"""
    print("\n=== TEST: Campos Faltantes ===\n")
    
    event = {
        'body': json.dumps({
            'filename': 'test.png'
            # Falta 'image'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 400
    print("\n✅ Test pasado!")

def test_upload_invalid_extension():
    """Test de validación - extensión inválida"""
    print("\n=== TEST: Extensión Inválida ===\n")
    
    event = {
        'body': json.dumps({
            'image': 'fake_base64_data',
            'filename': 'test.exe',  # Extensión no permitida
            'game_title': 'Test Game'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 400
    print("\n✅ Test pasado!")

if __name__ == '__main__':
    print("🧪 Iniciando tests de ImageUploader...\n")
    
    try:
        test_upload_success()
        test_upload_missing_fields()
        test_upload_invalid_extension()
        
        print("\n" + "="*50)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
