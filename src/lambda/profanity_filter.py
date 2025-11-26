"""
Lambda Function: Profanity Filter
Analiza capturas de pantalla para detectar contenido inapropiado
"""
import json
import boto3
import os
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

RAW_BUCKET = os.environ['RAW_BUCKET']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
METADATA_TABLE = os.environ['METADATA_TABLE']
NOTIFICATION_TOPIC_ARN = os.environ['NOTIFICATION_TOPIC_ARN']

# Lista de palabras prohibidas (ejemplo básico)
PROFANITY_LIST = [
    'badword1', 'badword2', 'offensive', 'inappropriate',
    'spam', 'hack', 'cheat', 'exploit'
]

def lambda_handler(event, context):
    try:
        # Parse SNS message
        for record in event['Records']:
            message = json.loads(record['Sns']['Message'])
            screenshot_id = message['screenshot_id']
            user_id = message['user_id']
            s3_key = message['s3_key']
            bucket = message['bucket']
            
            print(f"Processing screenshot: {screenshot_id}")
            
            # Get image from S3
            response = s3_client.get_object(Bucket=bucket, Key=s3_key)
            image_data = response['Body'].read()
            
            # Get metadata from DynamoDB
            table = dynamodb.Table(METADATA_TABLE)
            item = table.get_item(Key={'screenshot_id': screenshot_id})['Item']
            
            # Perform profanity check
            is_appropriate = check_content(item, image_data)
            
            if is_appropriate:
                # Move to processed bucket
                processed_key = s3_key.replace('raw/', 'processed/')
                s3_client.copy_object(
                    Bucket=PROCESSED_BUCKET,
                    CopySource={'Bucket': bucket, 'Key': s3_key},
                    Key=processed_key
                )
                
                # Update metadata
                table.update_item(
                    Key={'screenshot_id': screenshot_id},
                    UpdateExpression='SET #status = :status, processed_s3_key = :key, processed_timestamp = :timestamp',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'APPROVED',
                        ':key': processed_key,
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                status_message = 'Screenshot approved and ready for viewing'
            else:
                # Update metadata as rejected
                table.update_item(
                    Key={'screenshot_id': screenshot_id},
                    UpdateExpression='SET #status = :status, rejection_reason = :reason, processed_timestamp = :timestamp',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'REJECTED',
                        ':reason': 'Inappropriate content detected',
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                
                status_message = 'Screenshot rejected due to inappropriate content'
            
            # Send notification to user
            sns_client.publish(
                TopicArn=NOTIFICATION_TOPIC_ARN,
                Message=json.dumps({
                    'user_id': user_id,
                    'screenshot_id': screenshot_id,
                    'status': 'APPROVED' if is_appropriate else 'REJECTED',
                    'message': status_message
                }),
                Subject='Screenshot Processing Complete'
            )
            
            print(f"Screenshot {screenshot_id}: {'APPROVED' if is_appropriate else 'REJECTED'}")
        
        return {'statusCode': 200, 'body': 'Processing complete'}
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}

def check_content(metadata, image_data):
    """
    Verifica si el contenido es apropiado
    En producción, aquí se integraría con Amazon Rekognition
    """
    # Check text fields for profanity
    text_to_check = f"{metadata.get('description', '')} {metadata.get('game_title', '')}".lower()
    
    for word in PROFANITY_LIST:
        if word in text_to_check:
            print(f"Profanity detected: {word}")
            return False
    
    # Simulación de análisis de imagen
    # En producción: usar Amazon Rekognition para detectar contenido inapropiado
    # rekognition = boto3.client('rekognition')
    # response = rekognition.detect_moderation_labels(Image={'Bytes': image_data})
    
    return True
