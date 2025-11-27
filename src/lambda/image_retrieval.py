"""
Lambda Function: Image Retrieval
Recupera capturas de pantalla del usuario con URLs firmadas
Versión mejorada con GSI para queries eficientes y soporte CloudFront
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

METADATA_TABLE = os.environ['METADATA_TABLE']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')

# Configuración
DEFAULT_LIMIT = 50
MAX_LIMIT = 100
URL_EXPIRATION = 3600  # 1 hora

def lambda_handler(event, context):
    try:
        # Get user ID from authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Parse query parameters
        params = event.get('queryStringParameters', {}) or {}
        status_filter = params.get('status', 'APPROVED')
        limit = min(int(params.get('limit', DEFAULT_LIMIT)), MAX_LIMIT)
        
        # Determine query method based on path
        path = event.get('path', '')
        
        if '/all' in path:
            # Admin endpoint - get all screenshots (requires admin role check)
            screenshots = get_all_screenshots(status_filter, limit)
        else:
            # User endpoint - get user's screenshots
            screenshots = get_user_screenshots(user_id, status_filter, limit)
        
        return response_success(200, {
            'count': len(screenshots),
            'screenshots': screenshots
        })
        
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return response_success(400, {'error': str(e)})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response_success(500, {'error': 'Internal server error'})

def get_user_screenshots(user_id, status_filter, limit):
    """
    Obtiene screenshots de un usuario específico usando GSI
    """
    table = dynamodb.Table(METADATA_TABLE)
    
    try:
        # Query usando GSI user-index (más eficiente que scan)
        response = table.query(
            IndexName='user-index',
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False,  # Orden descendente por timestamp
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Filtrar por status si se especifica
        if status_filter:
            items = [item for item in items if item.get('status') == status_filter]
        
    except Exception as e:
        print(f"GSI query failed, falling back to scan: {str(e)}")
        # Fallback a scan si GSI no existe
        response = table.scan(
            FilterExpression=Key('user_id').eq(user_id),
            Limit=limit
        )
        items = response.get('Items', [])
        items = [item for item in items if item.get('status') == status_filter]
        items.sort(key=lambda x: x.get('upload_timestamp', 0), reverse=True)
    
    # Formatear screenshots
    screenshots = []
    for item in items:
        screenshot = format_screenshot_item(item)
        screenshots.append(screenshot)
    
    return screenshots

def get_all_screenshots(status_filter, limit):
    """
    Obtiene todos los screenshots usando GSI status-index
    """
    table = dynamodb.Table(METADATA_TABLE)
    
    try:
        # Query usando GSI status-index
        response = table.query(
            IndexName='status-index',
            KeyConditionExpression=Key('status').eq(status_filter),
            ScanIndexForward=False,
            Limit=limit
        )
        
        items = response.get('Items', [])
        
    except Exception as e:
        print(f"GSI query failed, falling back to scan: {str(e)}")
        # Fallback a scan
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        items = [item for item in items if item.get('status') == status_filter]
        items.sort(key=lambda x: x.get('upload_timestamp', 0), reverse=True)
    
    # Formatear screenshots
    screenshots = []
    for item in items:
        screenshot = format_screenshot_item(item)
        screenshots.append(screenshot)
    
    return screenshots

def format_screenshot_item(item):
    """
    Formatea un item de DynamoDB y genera URL firmada
    """
    screenshot = {
        'screenshot_id': item['screenshot_id'],
        'user_id': item['user_id'],
        'game_title': item.get('game_title', 'Unknown'),
        'description': item.get('description', ''),
        'filename': item.get('filename', ''),
        'upload_timestamp': int(item.get('upload_timestamp', 0)),
        'status': item['status'],
        'file_size': int(item.get('file_size', 0)),
        'extension': item.get('extension', '')
    }
    
    # Agregar timestamp de procesamiento si existe
    if 'processed_timestamp' in item:
        screenshot['processed_timestamp'] = int(item['processed_timestamp'])
    
    # Generate signed URL if approved
    if item['status'] == 'APPROVED' and 'processed_s3_key' in item:
        url = generate_signed_url(item['processed_s3_key'])
        if url:
            screenshot['url'] = url
    
    # Agregar razones de rechazo si aplica
    if item['status'] == 'REJECTED' and 'rejection_reasons' in item:
        screenshot['rejection_reasons'] = item['rejection_reasons']
    
    return screenshot

def generate_signed_url(s3_key):
    """
    Genera URL firmada para acceso temporal a la imagen
    Usa CloudFront si está disponible, sino S3 presigned URL
    """
    try:
        # Usar CloudFront si está configurado
        if CLOUDFRONT_DOMAIN:
            url = f"https://{CLOUDFRONT_DOMAIN}/{s3_key}"
            print(f"Generated CloudFront URL for {s3_key}")
            return url
        else:
            # Generar URL firmada de S3
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': PROCESSED_BUCKET,
                    'Key': s3_key
                },
                ExpiresIn=URL_EXPIRATION
            )
            print(f"Generated S3 presigned URL for {s3_key}")
            return url
    except Exception as e:
        print(f"Error generating signed URL for {s3_key}: {str(e)}")
        return None

def response_success(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(body)
    }
