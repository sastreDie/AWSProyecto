import boto3
import os
import uuid
import json
import io
from datetime import datetime
from PIL import Image  # Esto funcionará gracias a tu Layer

# Clientes de AWS
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    print("Iniciando procesamiento de evento S3...")
    
    # 1. Obtener información del evento (qué archivo se subió)
    try:
        record = event['Records'][0]
        src_bucket = record['s3']['bucket']['name']
        src_key = record['s3']['object']['key'] # Ejemplo: PLAYER1/foto.png
        
        # Evitar bucles infinitos (si por error se sube al mismo bucket)
        if "thumbnails/" in src_key:
            return {'status': 'skipped', 'reason': 'Es un thumbnail'}

        print(f"Procesando archivo: {src_key} del bucket: {src_bucket}")

        # 2. Descargar la imagen a memoria (sin guardarla en disco)
        response = s3.get_object(Bucket=src_bucket, Key=src_key)
        image_content = response['Body'].read()

        # 3. Procesamiento con Pillow
        with Image.open(io.BytesIO(image_content)) as img:
            # Generar Thumbnail (128x128 max)
            img.thumbnail((128, 128))
            
            # Guardar en buffer de memoria
            buffer = io.BytesIO()
            img_format = img.format if img.format else 'PNG'
            img.save(buffer, format=img_format)
            buffer.seek(0)
            
            # 4. Subir al bucket de PROCESADOS
            dest_bucket = os.environ['PROCESSED_BUCKET']
            dest_key = f"thumbnails/{src_key}"
            
            s3.put_object(
                Bucket=dest_bucket,
                Key=dest_key,
                Body=buffer,
                ContentType=f'image/{img_format.lower()}'
            )
            print(f"Thumbnail subido a: {dest_bucket}/{dest_key}")

        # 5. Guardar Metadatos en DynamoDB
        table_name = os.environ['METADATA_TABLE']
        table = dynamodb.Table(table_name)
        
        # Intentar adivinar el ID del jugador desde la carpeta (PLAYER1/foto.png)
        player_id = src_key.split('/')[0] if '/' in src_key else 'unknown'
        
        item = {
            'screenshotId': str(uuid.uuid4()),
            'playerId': player_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'PROCESSED',
            'originalPath': f"s3://{src_bucket}/{src_key}",
            'processedPath': f"s3://{dest_bucket}/{dest_key}"
        }
        
        table.put_item(Item=item)
        print("Metadatos guardados en DynamoDB")

        return {
            'statusCode': 200,
            'body': json.dumps('Procesamiento exitoso')
        }

    except Exception as e:
        print(f"Error procesando imagen: {str(e)}")
        raise e