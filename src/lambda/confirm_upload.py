"""
Lambda Function: Confirm Upload
Confirma que la imagen fue subida y dispara el proceso de filtrado
"""
import json
import boto3
import os

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

RAW_BUCKET = os.environ['RAW_BUCKET']
METADATA_TABLE = os.environ['METADATA_TABLE']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    try:
        # Parse request body
        body = json.loads(event['body'])
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Validate required fields
        if 'screenshot_id' not in body:
            return response(400, {'error': 'Missing screenshot_id'})
        
        screenshot_id = body['screenshot_id']
        
        # Get metadata from DynamoDB
        table = dynamodb.Table(METADATA_TABLE)
        item_response = table.get_item(Key={'screenshot_id': screenshot_id})
        
        if 'Item' not in item_response:
            return response(404, {'error': 'Screenshot not found'})
        
        item = item_response['Item']
        
        # Verify user owns this screenshot
        if item['user_id'] != user_id:
            return response(403, {'error': 'Unauthorized'})
        
        # Verify file exists in S3
        s3_key = item['raw_s3_key']
        try:
            s3_response = s3_client.head_object(Bucket=RAW_BUCKET, Key=s3_key)
            file_size = s3_response['ContentLength']
        except:
            return response(400, {'error': 'File not uploaded to S3'})
        
        # Update metadata
        table.update_item(
            Key={'screenshot_id': screenshot_id},
            UpdateExpression='SET #status = :status, file_size = :size',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'PROCESSING',
                ':size': file_size
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
            'message': 'Upload confirmed, processing started',
            'screenshot_id': screenshot_id,
            'status': 'PROCESSING'
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
