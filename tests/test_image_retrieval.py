"""
Test local para ImageRetrieval Lambda
Simula el evento de API Gateway
"""
import json
import sys
import os

# Configurar variables de entorno ANTES de importar
os.environ['PROCESSED_BUCKET'] = 'test-processed-bucket'
os.environ['METADATA_TABLE'] = 'test-metadata-table'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Mocks
class MockDynamoDB:
    def Table(self, name):
        return MockTable(name)

class MockTable:
    def __init__(self, name):
        self.name = name
    
    def scan(self, **kwargs):
        print(f"[MOCK DynamoDB] Scanning tabla {self.name}")
        print(f"FilterExpression: {kwargs.get('FilterExpression')}")
        
        # Retornar screenshots de ejemplo
        return {
            'Items': [
                {
                    'screenshot_id': 'screenshot-1',
                    'user_id': 'test-user-123',
                    'game_title': 'Game 1',
                    'description': 'Epic moment',
                    'upload_timestamp': '2025-11-26T10:00:00Z',
                    'status': 'APPROVED',
                    'processed_s3_key': 'processed/test-user-123/screenshot-1.png',
                    'file_size': 1024000
                },
                {
                    'screenshot_id': 'screenshot-2',
                    'user_id': 'test-user-123',
                    'game_title': 'Game 2',
                    'description': 'Victory',
                    'upload_timestamp': '2025-11-26T11:00:00Z',
                    'status': 'APPROVED',
                    'processed_s3_key': 'processed/test-user-123/screenshot-2.png',
                    'file_size': 2048000
                }
            ]
        }

class MockS3:
    def generate_presigned_url(self, operation, Params, ExpiresIn):
        print(f"[MOCK S3] Generando URL firmada para: {Params['Key']}")
        return f"https://mock-s3-url.com/{Params['Key']}?expires={ExpiresIn}"

import boto3
boto3.client = lambda service: MockS3()
boto3.resource = lambda service: MockDynamoDB()

from image_retrieval import lambda_handler

def test_retrieval_success():
    """Test de recuperación exitosa"""
    print("\n=== TEST: Recuperación Exitosa ===\n")
    
    event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        },
        'queryStringParameters': {
            'status': 'APPROVED',
            'limit': '10'
        }
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert 'screenshots' in body
    assert body['count'] > 0
    assert 'url' in body['screenshots'][0]
    print("\n✅ Test pasado!")

def test_retrieval_no_params():
    """Test sin parámetros (usa defaults)"""
    print("\n=== TEST: Sin Parámetros ===\n")
    
    event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        },
        'queryStringParameters': None
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    print("\n✅ Test pasado!")

def test_retrieval_empty_results():
    """Test con resultados vacíos"""
    print("\n=== TEST: Resultados Vacíos ===\n")
    
    # Mock que retorna vacío
    original_scan = MockTable.scan
    
    def scan_empty(self, **kwargs):
        print(f"[MOCK DynamoDB] Scanning tabla {self.name} (vacío)")
        return {'Items': []}
    
    MockTable.scan = scan_empty
    
    event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-999'
                }
            }
        },
        'queryStringParameters': None
    }
    
    context = {}
    
    response = lambda_handler(event, context)
    
    print("\n=== RESPONSE ===")
    print(json.dumps(response, indent=2))
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['count'] == 0
    print("\n✅ Test pasado!")
    
    # Restaurar mock
    MockTable.scan = original_scan

if __name__ == '__main__':
    print("🧪 Iniciando tests de ImageRetrieval...\n")
    
    try:
        test_retrieval_success()
        test_retrieval_no_params()
        test_retrieval_empty_results()
        
        print("\n" + "="*50)
        print("✅ TODOS LOS TESTS PASARON")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
