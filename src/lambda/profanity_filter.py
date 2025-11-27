"""
Lambda Function: Profanity Filter
Analiza capturas de pantalla para detectar contenido inapropiado usando AWS Rekognition
Versión mejorada con detección de contenido visual y texto en imágenes
"""
import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

RAW_BUCKET = os.environ['RAW_BUCKET']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']
METADATA_TABLE = os.environ['METADATA_TABLE']
NOTIFICATION_TOPIC_ARN = os.environ['NOTIFICATION_TOPIC_ARN']

# Lista de palabras prohibidas (ejemplo básico)
PROFANITY_LIST = [
    # Groserías comunes
    'fuck', 'shit', 'damn', 'bitch', 'ass', 'bastard', 'crap',
    'piss', 'dick', 'cock', 'pussy', 'whore', 'slut',
    
    # Contenido inapropiado
    'badword1', 'badword2', 'offensive', 'inappropriate',
    'nsfw', 'adult', 'porn', 'sex', 'nude', 'naked',
    
    # Violencia
    'violence', 'gore', 'blood', 'hate', 'kill', 'murder', 'death',
    
    # Trampas y spam
    'spam', 'hack', 'cheat', 'exploit', 'bot', 'aimbot', 'wallhack'
]

# Configuración de Rekognition
MIN_CONFIDENCE_MODERATION = 50.0  # Umbral para detectar contenido
REJECT_CONFIDENCE_THRESHOLD = 55.0  # Umbral para rechazar (bajado para capturar smoking)

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
            image_bytes = response['Body'].read()
            
            # Get metadata from DynamoDB
            table = dynamodb.Table(METADATA_TABLE)
            item = table.get_item(Key={'screenshot_id': screenshot_id})['Item']
            
            # Perform comprehensive content check
            is_appropriate, rejection_reasons = check_content(item, image_bytes, bucket, s3_key)
            
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
                        ':timestamp': Decimal(str(int(datetime.utcnow().timestamp())))
                    }
                )
                
                status_message = 'Screenshot approved and ready for viewing'
            else:
                # Update metadata as rejected
                table.update_item(
                    Key={'screenshot_id': screenshot_id},
                    UpdateExpression='SET #status = :status, rejection_reasons = :reasons, processed_timestamp = :timestamp',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'REJECTED',
                        ':reasons': rejection_reasons,
                        ':timestamp': Decimal(str(int(datetime.utcnow().timestamp())))
                    }
                )
                
                status_message = f'Screenshot rejected: {", ".join(rejection_reasons)}'
            
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

def verify_is_video_game(image_bytes):
    """
    Verifica si la imagen es un screenshot de videojuego
    Retorna: True si es videojuego, False si es foto real
    """
    try:
        # Usar DetectLabels para identificar el contenido
        labels_response = rekognition_client.detect_labels(
            Image={'Bytes': image_bytes},
            MaxLabels=50,
            MinConfidence=30.0
        )
        
        labels = labels_response.get('Labels', [])
        print(f"Labels detected: {json.dumps([{'Name': l['Name'], 'Confidence': l['Confidence']} for l in labels], default=str)}")
        
        # Buscar indicadores de videojuego
        video_game_indicators = [
            'video game', 'game', 'gaming', 'screenshot', 'screen',
            'computer game', 'video gaming', 'pc game', 'console game',
            'pixel art', 'retro game', '8-bit', '16-bit', 'arcade'
        ]
        
        # Buscar indicadores de foto real (que queremos rechazar)
        real_photo_indicators = [
            'person', 'human', 'people', 'man', 'woman', 'face',
            'portrait', 'selfie', 'photography', 'photo'
        ]
        
        game_confidence = 0.0
        real_photo_confidence = 0.0
        
        for label in labels:
            label_name = label['Name'].lower()
            confidence = label['Confidence']
            
            # Verificar indicadores de videojuego
            for indicator in video_game_indicators:
                if indicator in label_name:
                    game_confidence = max(game_confidence, confidence)
                    print(f"Video game indicator found: {label['Name']} - {confidence:.1f}%")
            
            # Verificar indicadores de foto real
            for indicator in real_photo_indicators:
                if indicator in label_name:
                    real_photo_confidence = max(real_photo_confidence, confidence)
                    print(f"Real photo indicator found: {label['Name']} - {confidence:.1f}%")
        
        print(f"Game confidence: {game_confidence:.1f}%, Real photo confidence: {real_photo_confidence:.1f}%")
        
        # Decisión: Si tiene alta confianza de foto real Y baja de videojuego → Rechazar
        if real_photo_confidence > 70.0 and game_confidence < 50.0:
            print("Detected as real photo, not a video game")
            return False
        
        # Si tiene indicadores de videojuego → Aprobar
        if game_confidence >= 50.0:
            print("Detected as video game screenshot")
            return True
        
        # Si no está claro, ser permisivo (aprobar)
        print("Unclear if video game or not, allowing by default")
        return True
        
    except Exception as e:
        print(f"Error verifying video game: {str(e)}")
        # Si falla la detección, ser permisivo
        return True

def check_content(metadata, image_bytes, bucket, s3_key):
    """
    Verifica si el contenido es apropiado usando AWS Rekognition
    Retorna: (is_appropriate: bool, rejection_reasons: list)
    """
    rejection_reasons = []
    
    # 1. Verificar que sea un videojuego (PRIMER FILTRO)
    is_video_game = verify_is_video_game(image_bytes)
    if not is_video_game:
        rejection_reasons.append("Not a video game screenshot - real photo detected")
        print("Image rejected: Not a video game screenshot")
        # No retornar aquí, seguir verificando por si acaso
    
    print(f"Video game verification: {'PASSED' if is_video_game else 'FAILED'}")
    
    # 2. Check text fields for profanity
    text_to_check = f"{metadata.get('description', '')} {metadata.get('game_title', '')}".lower()
    
    for word in PROFANITY_LIST:
        if word in text_to_check:
            print(f"Profanity in metadata detected: {word}")
            rejection_reasons.append(f"Inappropriate text in description: {word}")
    
    # 2. AWS Rekognition - Detect Moderation Labels (contenido inapropiado)
    try:
        # Primero intentar con threshold bajo para ver TODO lo que detecta
        moderation_response_all = rekognition_client.detect_moderation_labels(
            Image={'Bytes': image_bytes},
            MinConfidence=0.0  # Ver TODO
        )
        
        all_labels = moderation_response_all.get('ModerationLabels', [])
        print(f"ALL moderation labels detected (any confidence): {json.dumps(all_labels, default=str)}")
        
        # Ahora filtrar por el threshold configurado
        moderation_response = rekognition_client.detect_moderation_labels(
            Image={'Bytes': image_bytes},
            MinConfidence=MIN_CONFIDENCE_MODERATION
        )
        
        moderation_labels = moderation_response.get('ModerationLabels', [])
        print(f"Moderation labels found (>{MIN_CONFIDENCE_MODERATION}% confidence): {len(moderation_labels)}")
        
        for label in moderation_labels:
            confidence = label['Confidence']
            label_name = label['Name']
            parent_name = label.get('ParentName', '')
            
            print(f"Moderation label: {label_name} ({parent_name}) - Confidence: {confidence:.2f}%")
            
            # Rechazar si supera el umbral
            if confidence >= REJECT_CONFIDENCE_THRESHOLD:
                reason = f"Inappropriate visual content: {label_name}"
                if parent_name:
                    reason += f" ({parent_name})"
                reason += f" - {confidence:.1f}% confidence"
                rejection_reasons.append(reason)
        
        # Log all moderation labels for debugging
        if moderation_labels:
            print(f"All moderation labels detected: {json.dumps(moderation_labels, default=str)}")
            
    except Exception as moderation_error:
        print(f"DetectModerationLabels error: {str(moderation_error)}")
        # Continuar sin detección de moderación visual
    
    # 3. AWS Rekognition - Detect Text (texto en la imagen)
    # NOTA: Requiere permiso rekognition:DetectText (pendiente de aprobación de seguridad)
    try:
        text_response = rekognition_client.detect_text(
            Image={'Bytes': image_bytes}
        )
        
        detected_texts = []
        for text_detection in text_response.get('TextDetections', []):
            if text_detection['Type'] == 'LINE' and text_detection['Confidence'] > 80:
                detected_text = text_detection['DetectedText'].lower()
                detected_texts.append(detected_text)
                print(f"Text detected in image: {detected_text}")
        
        # Verificar palabras prohibidas en el texto detectado
        for detected_text in detected_texts:
            for profanity in PROFANITY_LIST:
                if profanity in detected_text:
                    rejection_reasons.append(f"Offensive text in image: '{profanity}'")
                    print(f"Profanity in image text: {profanity}")
                    break
                    
    except Exception as text_error:
        print(f"DetectText not available (permission pending): {str(text_error)}")
        # Continuar sin detección de texto
    
    is_appropriate = len(rejection_reasons) == 0
    
    return is_appropriate, rejection_reasons
