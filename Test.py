import boto3
import json
from email.parser import BytesParser
from email.policy import default
import os

# Initialisation des clients AWS
dynamodb = boto3.resource('dynamodb')
# Le nom de la table est une bonne pratique de le mettre en variable d'environnement
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'NewsletterSummaries')
table = dynamodb.Table(table_name)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Traite un e-mail entrant et le stocke dans une base de données DynamoDB.
    """
    try:
        # Récupération des informations de l'e-mail depuis l'événement SES
        ses_data = event['Records'][0]['ses']
        message_id = ses_data['mail']['messageId']
        bucket_name = os.environ.get('SES_EMAIL_BUCKET') # Le nom de votre bucket SES
        
        # Récupérer le contenu brut de l'e-mail depuis S3
        response = s3_client.get_object(Bucket=bucket_name, Key=message_id)
        raw_email = response['Body'].read()
        
        # Analyser le contenu de l'e-mail
        msg = BytesParser(policy=default).parsebytes(raw_email)
        
        sender = str(msg.get('From', 'Inconnu'))
        subject = str(msg.get('Subject', 'Sans sujet'))
        
        # Le format de date n'est pas standard pour le tri, on le convertit.
        # Utiliser un timestamp ou une chaîne ISO 8601 est une bonne pratique.
        # On va utiliser le timestamp pour le tri ultérieur.
        received_date = int(ses_data['mail']['timestamp'] / 1000)
        
        html_body = None
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':
                charset = part.get_content_charset()
                # Gérer le cas où le charset est inconnu
                if charset:
                    html_body = part.get_payload(decode=True).decode(charset)
                else:
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                break
        
        if not html_body:
            text_body = None
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset()
                    if charset:
                        text_body = part.get_payload(decode=True).decode(charset)
                    else:
                        text_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
            html_body = f'<pre>{text_body}</pre>' if text_body else ''

        # Écrire l'e-mail dans la base de données
        table.put_item(
           Item={
               'emailId': message_id,
               'sender': sender,
               'subject': subject,
               'receivedDate': received_date, # Utilisez le timestamp
               'bodyHtml': html_body
           }
        )

        return {
            'statusCode': 200,
            'body': json.dumps('E-mail enregistré avec succès.')
        }
        
    except Exception as e:
        print(f"Erreur lors du traitement de l'e-mail: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erreur lors du traitement de l'e-mail: {str(e)}")
        }

