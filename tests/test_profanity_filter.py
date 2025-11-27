"""
Test local para ProfanityFilter Lambda
Simula el evento de SNS
"""
import json
import sys
import os

# Configurar variables de entorno ANTES de importar
os.environ['RAW_BUCKET'] = 'test-raw-bucket'
os.environ['PROCESSED_BUCKET'] = 'test-processed-bucket'
os.environ['METADATA_TABLE'] = 'test-metadata-table'
os.environ['NOTIFICATION_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:test-topic'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Mocks
class MockS3:
    def get_object(self, **kwargs):
        print(f"[MOCK S3] Obteniendo de bucket: {kwargs['Bucket']}, key: {kwargs['Key']}")
        # Retornar imagen fake
        class Body:
            def read(self):
                return b'fake_image_data'
        return {'Body': Body()}
    
    def copy_object(self, **kwargs):
        print(f"[MOCK S3] Copiando a bucket: {kwargs['Bucket']}, key: {kwargs['Key']}")
        return {}

class MockDynamoDB:
    def Table(self, name):
        return MockTable(name)

class MockTable:
    def __init__(self, name):
        self.name = name
    
    def get_item(self, Key):
        print(f"[MOCK DynamoDB] Obteniendo item: {Key}")
        return {
            'Item': {
                'screenshot_id': Key['screenshot_id'],
                'user_id': 'test-user-123',
                'description': 'Clean description',
                'game_title': 'Test Game',
                'status': 'PROCESSING'
            }
        }
    
    def update_item(self, **kwargs):
        print(f"[MOCK DynamoDB] Actualizando item en tabla {self.name}")
        print(f"UpdateExpression: {kwargs.get('UpdateExpression')}")
        print(f"Values: {kwargs.get('ExpressionAttributeValues')}")
        return {}

class MockSNS:
    def publish(self, **kwargs):
        print(f"[MOCK SNS] Publicando notificación")
        print(f"Mensaje: {kwargs['Message']}")
        return {'MessageId': 'mock-message-id'}

import boto3
boto3.client = lambda service: MockS3() if service == 's3' else MockSNS()
boto3.resource = lambda service: MockDynamoDB()

from profanity_filter import lambda_handler

def test_filter_approved():
    """Test de contenido aprobado"""
    print("\n=== TEST: Contenido Aprobado ===\n")
    
    event = {
        'Records': [
            {
                'Sns': {
                    'Message': json.dumps({
                        'screenshot_id': 'test-screenshot-123',
                        'user_id': 'test-user-123',
                        's3_key': 'raw/test-user-123/test.png',
                        'bucket': 'test-raw-bucket'
                    })
                }
            }
        ]
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    print("\n✅ Test pasado!")

def test_filter_rejected():
    """Test de contenido rechazado (profanidad)"""
    print("\n=== TEST: Contenido Rechazado ===\n")
    
    # Mock que retorna contenido con profanidad
    original_get_item = MockTable.get_item
    
    def get_item_with_profanity(self, Key):
        return {
            'Item': {
                'screenshot_id': Key['screenshot_id'],
                'user_id': 'test-user-123',
                'description': 'This contains badword1',  # Palabra prohibida
                'game_title': 'Test Game',
                'status': 'PROCESSING'
            }
        }
    
    MockTable.get_item = get_item_with_profanity
    
    event = {
        'Records': [
            {
                'Sns': {
                    'Message': json.dumps({
                        'screenshot_id': 'test-screenshot-456',
                        'user_id': 'test-user-123',
                        's3_key': 'raw/test-user-123/test.png',
                        'bucket': 'test-raw-bucket'
                    })
                }
            }
        ]
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    print("\n✅ Test pasado!")
    
    # Restaurar mock original
    MockTable.get_item = original_get_item

if __name__ == '__main__':
    print("🧪 Iniciando tests de ProfanityFilter...\n")
    
    try:
        test_filter_approved()
        test_filter_rejected()
        
        print("\n" + "="*50)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
