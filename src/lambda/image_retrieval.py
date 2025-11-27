"""
Lambda Function: Image Retrieval
Recupera capturas de pantalla del usuario con URLs firmadas de CloudFront
"""
import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
cloudfront_client = boto3.client('cloudfront')

METADATA_TABLE = os.environ['METADATA_TABLE']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
CLOUDFRONT_DOMAIN = os.environ.get('CLOUDFRONT_DOMAIN', '')
CLOUDFRONT_KEY_PAIR_ID = os.environ.get('CLOUDFRONT_KEY_PAIR_ID', '')

def lambda_handler(event, context):
    try:
        # Get user ID from authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Parse query parameters
        params = event.get('queryStringParameters', {}) or {}
        status_filter = params.get('status', 'APPROVED')
        limit = int(params.get('limit', 50))
        
        # Query DynamoDB for user's screenshots
        table = dynamodb.Table(METADATA_TABLE)
        
        # Scan with filter (en producción usar GSI para mejor performance)
        response = table.scan(
            FilterExpression=Key('user_id').eq(user_id) & Key('status').eq(status_filter),
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Generate signed URLs for approved screenshots
        screenshots = []
        for item in items:
            screenshot = {
                'screenshot_id': item['screenshot_id'],
                'game_title': item.get('game_title', 'Unknown'),
                'description': item.get('description', ''),
                'upload_timestamp': item['upload_timestamp'],
                'status': item['status'],
                'file_size': item.get('file_size', 0)
            }
            
            # Generate signed URL if approved
            if item['status'] == 'APPROVED' and 'processed_s3_key' in item:
                url = generate_signed_url(item['processed_s3_key'])
                screenshot['url'] = url
            
            screenshots.append(screenshot)
        
        # Sort by timestamp (most recent first)
        screenshots.sort(key=lambda x: x['upload_timestamp'], reverse=True)
        
        return response_success(200, {
            'count': len(screenshots),
            'screenshots': screenshots
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return response_success(500, {'error': 'Internal server error'})

def generate_signed_url(s3_key, expiration=3600):
    """
    Genera URL firmada para acceso temporal a la imagen
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': PROCESSED_BUCKET,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        return url
    except Exception as e:
        print(f"Error generating signed URL: {str(e)}")
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
