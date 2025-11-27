"""
Lambda Function: Generate Upload URL
Genera URLs pre-firmadas para subir imágenes directamente a S3
"""
import json
import boto3
import uuid
import os
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

RAW_BUCKET = os.environ['RAW_BUCKET']
METADATA_TABLE = os.environ['METADATA_TABLE']

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Validate required fields
        if 'filename' not in body:
            return response(400, {'error': 'Missing filename'})
        
        filename = body['filename']
        game_title = body.get('game_title', 'Unknown')
        description = body.get('description', '')
        content_type = body.get('content_type', 'image/png')
        
        # Validate file extension
        extension = filename.split('.')[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return response(400, {'error': f'Invalid file type. Allowed: {ALLOWED_EXTENSIONS}'})
        
        # Generate unique ID
        screenshot_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        s3_key = f"raw/{user_id}/{screenshot_id}.{extension}"
        
        # Generate pre-signed URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': RAW_BUCKET,
                'Key': s3_key,
                'ContentType': content_type,
                'Metadata': {
                    'user_id': user_id,
                    'screenshot_id': screenshot_id,
                    'upload_timestamp': timestamp
                }
            },
            ExpiresIn=300  # URL válida por 5 minutos
        )
        
        # Store initial metadata in DynamoDB
        table = dynamodb.Table(METADATA_TABLE)
        table.put_item(
            Item={
                'screenshot_id': screenshot_id,
                'user_id': user_id,
                'filename': filename,
                'game_title': game_title,
                'description': description,
                'upload_timestamp': timestamp,
                'status': 'PENDING_UPLOAD',
                'raw_s3_key': s3_key,
                'extension': extension
            }
        )
        
        return response(200, {
            'screenshot_id': screenshot_id,
            'upload_url': presigned_url,
            's3_key': s3_key,
            'expires_in': 300
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return response(500, {'error': 'Internal server error', 'details': str(e)})

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }
