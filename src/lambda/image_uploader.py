"""
Lambda Function: Image Uploader
Procesa la carga de capturas de pantalla, valida formato y almacena en S3
Versión mejorada con validaciones robustas y mejor manejo de errores
"""
import json
import boto3
import base64
import uuid
from datetime import datetime
from decimal import Decimal
import os

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

RAW_BUCKET = os.environ['RAW_BUCKET']
METADATA_TABLE = os.environ['METADATA_TABLE']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_FILE_SIZE = 1024  # 1KB

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Validate required fields
        if 'image' not in body or 'filename' not in body:
            return response(400, {'error': 'Missing required fields: image and filename'})
        
        filename = body['filename']
        image_data = body['image']
        game_title = body.get('game_title', 'Unknown')
        description = body.get('description', '')
        
        # Validate filename
        if not filename or len(filename) > 255:
            return response(400, {'error': 'Invalid filename length'})
        
        # Validate file extension
        if '.' not in filename:
            return response(400, {'error': 'Filename must have an extension'})
        
        extension = filename.split('.')[-1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return response(400, {'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'})
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            print(f"Base64 decode error: {str(e)}")
            return response(400, {'error': 'Invalid base64 image data'})
        
        # Validate file size
        file_size = len(image_bytes)
        if file_size < MIN_FILE_SIZE:
            return response(400, {'error': f'File too small. Min size: {MIN_FILE_SIZE} bytes'})
        if file_size > MAX_FILE_SIZE:
            return response(400, {'error': f'File too large. Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB'})
        
        # Generate unique ID
        screenshot_id = str(uuid.uuid4())
        timestamp = int(datetime.utcnow().timestamp())
        s3_key = f"raw/{user_id}/{screenshot_id}.{extension}"
        
        # Upload to S3 Raw Bucket
        s3_client.put_object(
            Bucket=RAW_BUCKET,
            Key=s3_key,
            Body=image_bytes,
            ContentType=f'image/{extension}',
            Metadata={
                'user_id': user_id,
                'screenshot_id': screenshot_id,
                'upload_timestamp': timestamp
            }
        )
        
        # Store metadata in DynamoDB
        table = dynamodb.Table(METADATA_TABLE)
        table.put_item(
            Item={
                'screenshot_id': screenshot_id,
                'user_id': user_id,
                'filename': filename,
                'game_title': game_title,
                'description': description,
                'upload_timestamp': Decimal(str(timestamp)),
                'status': 'PENDING',
                'raw_s3_key': s3_key,
                'file_size': file_size,
                'extension': extension
            }
        )
        
        # Send SNS notification for profanity filtering
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps({
                'screenshot_id': screenshot_id,
                'user_id': user_id,
                's3_key': s3_key,
                'bucket': RAW_BUCKET
            }),
            Subject='New Screenshot for Profanity Filter'
        )
        
        return response(200, {
            'message': 'Screenshot uploaded successfully. Processing...',
            'screenshot_id': screenshot_id,
            'status': 'PENDING',
            'file_size': file_size
        })
        
    except KeyError as e:
        print(f"Missing key: {str(e)}")
        return response(400, {'error': f'Missing required field: {str(e)}'})
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': 'Internal server error'})

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
