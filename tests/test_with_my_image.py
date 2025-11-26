"""
Test simple con tu imagen específica
"""
import json
import base64
import sys
import os

# Configurar variables de entorno
os.environ['RAW_BUCKET'] = 'test-raw-bucket'
os.environ['METADATA_TABLE'] = 'test-metadata-table'
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789:test-topic'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambda'))

# Mocks simples
class MockS3:
    def put_object(self, **kwargs):
        print(f"✅ [S3] Imagen subida exitosamente")
        print(f"   Bucket: {kwargs['Bucket']}")
        print(f"   Key: {kwargs['Key']}")
        print(f"   Tamaño: {len(kwargs['Body'])} bytes")
        print(f"   Tipo: {kwargs['ContentType']}")
        return {'ETag': 'mock-etag'}

class MockDynamoDB:
    def Table(self, name):
        return MockTable(name)

class MockTable:
    def __init__(self, name):
        self.name = name
    
    def put_item(self, Item):
        print(f"\n✅ [DynamoDB] Metadata guardada:")
        print(f"   Screenshot ID: {Item['screenshot_id']}")
        print(f"   User ID: {Item['user_id']}")
        print(f"   Game: {Item['game_title']}")
        print(f"   Descripción: {Item['description']}")
        print(f"   Tamaño: {Item['file_size']} bytes")
        print(f"   Status: {Item['status']}")
        return {}

class MockSNS:
    def publish(self, **kwargs):
        print(f"\n✅ [SNS] Notificación enviada para procesamiento")
        return {'MessageId': 'mock-message-id'}

import boto3
boto3.client = lambda service: MockS3() if service == 's3' else MockSNS()
boto3.resource = lambda service: MockDynamoDB()

from image_uploader import lambda_handler

def test_my_image():
    """Test con tu imagen específica"""
    
    # CAMBIA ESTA RUTA A DONDE ESTÁ TU IMAGEN
    image_path = input("\n📁 Ingresa la ruta completa de tu imagen: ").strip()
    
    # Quitar comillas si las pegó
    image_path = image_path.strip('"').strip("'")
    
    if not os.path.exists(image_path):
        print(f"\n❌ Error: No se encontró la imagen en: {image_path}")
        return
    
    print(f"\n📸 Cargando imagen: {image_path}")
    
    # Leer la imagen
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    print(f"✅ Imagen cargada: {len(image_bytes)} bytes")
    
    # Detectar extensión
    extension = os.path.splitext(image_path)[1].lower().replace('.', '')
    if not extension:
        extension = 'png'
    
    print(f"📝 Extensión detectada: {extension}")
    
    # Convertir a base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    print(f"✅ Convertida a base64: {len(image_base64)} caracteres")
    
    # Crear evento simulado
    event = {
        'body': json.dumps({
            'image': image_base64,
            'filename': f'mi_screenshot.{extension}',
            'game_title': 'ACME Labs Game',
            'description': 'Screenshot de prueba con mi imagen real'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123'
                }
            }
        }
    }
    
    print("\n" + "="*60)
    print("🚀 EJECUTANDO LAMBDA CON TU IMAGEN")
    print("="*60 + "\n")
    
    try:
        # Ejecutar la función Lambda
        response = lambda_handler(event, {})
        
        print("\n" + "="*60)
        print("📊 RESULTADO")
        print("="*60)
        print(f"\nStatus Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"\n✅ ¡ÉXITO! Screenshot procesado")
            print(f"\nScreenshot ID: {body['screenshot_id']}")
            print(f"Status: {body['status']}")
            print(f"Mensaje: {body['message']}")
            
            print("\n" + "="*60)
            print("✅ TU IMAGEN FUNCIONÓ CORRECTAMENTE")
            print("="*60)
            print("\n📝 Resumen:")
            print(f"   - Imagen validada: ✅")
            print(f"   - Formato aceptado: ✅ ({extension})")
            print(f"   - Tamaño válido: ✅ ({len(image_bytes)} bytes)")
            print(f"   - Subida a S3: ✅ (simulado)")
            print(f"   - Guardada en DynamoDB: ✅ (simulado)")
            print(f"   - Notificación enviada: ✅ (simulado)")
            
        else:
            print(f"\n❌ Error: {response['body']}")
            body = json.loads(response['body'])
            if 'error' in body:
                print(f"Detalle: {body['error']}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_image_validation():
    """Prueba las validaciones con tu imagen"""
    
    image_path = input("\n📁 Ingresa la ruta de tu imagen: ").strip().strip('"').strip("'")
    
    if not os.path.exists(image_path):
        print(f"❌ Imagen no encontrada")
        return
    
    print("\n" + "="*60)
    print("🔍 VALIDANDO TU IMAGEN")
    print("="*60)
    
    # Leer imagen
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    file_size = len(image_bytes)
    extension = os.path.splitext(image_path)[1].lower().replace('.', '')
    
    # Validaciones
    print(f"\n📏 Tamaño: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size <= max_size:
        print(f"   ✅ Tamaño válido (máximo: 10 MB)")
    else:
        print(f"   ❌ Tamaño excedido (máximo: 10 MB)")
    
    print(f"\n📝 Extensión: .{extension}")
    allowed = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    if extension in allowed:
        print(f"   ✅ Formato válido")
    else:
        print(f"   ❌ Formato no permitido. Permitidos: {allowed}")
    
    # Verificar que sea imagen válida
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        print(f"\n🖼️  Dimensiones: {img.width} x {img.height} pixels")
        print(f"   Modo: {img.mode}")
        print(f"   Formato: {img.format}")
        print(f"   ✅ Imagen válida")
        
    except ImportError:
        print(f"\n⚠️  Pillow no instalado, no se puede validar formato")
    except Exception as e:
        print(f"\n❌ Error al leer imagen: {e}")

if __name__ == '__main__':
    print("="*60)
    print("🧪 TEST CON TU IMAGEN ESPECÍFICA")
    print("="*60)
    print("\nOpciones:")
    print("1. Probar upload completo con tu imagen")
    print("2. Solo validar tu imagen")
    
    choice = input("\nElige opción (1 o 2): ").strip()
    
    if choice == '1':
        test_my_image()
    elif choice == '2':
        test_image_validation()
    else:
        print("Opción inválida")
