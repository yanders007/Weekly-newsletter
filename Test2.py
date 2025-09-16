import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
import json
import os
from boto3.dynamodb.conditions import Attr

# Initialisation des clients AWS
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'NewsletterSummaries')
table = dynamodb.Table(table_name)
ses_client = boto3.client('ses', region_name=os.environ.get('AWS_REGION'))

SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

def lambda_handler(event, context):
    """
    Génère un e-mail de résumé à partir des newsletters de la semaine et l'envoie.
    """
    try:
        # Calculer le timestamp d'il y a une semaine
        one_week_ago_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
        
        # Utilisation d'un scan avec un FilterExpression pour ne récupérer que les items récents
        response = table.scan(
            FilterExpression=Attr('receivedDate').gte(one_week_ago_timestamp)
        )
        
        newsletters = response.get('Items', [])
        
        # Gérer la pagination si le volume de données dépasse 1 Mo
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('receivedDate').gte(one_week_ago_timestamp),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            newsletters.extend(response.get('Items', []))

        if not newsletters:
            return {
                'statusCode': 200,
                'body': json.dumps("Pas de nouvelles newsletters à résumer cette semaine.")
            }
        
        # Construction du corps HTML de l'e-mail
        html_body = "<h1>Synthèse hebdomadaire de vos newsletters 📰</h1>"
        html_body += f"<p>Voici un résumé des {len(newsletters)} newsletters reçues cette semaine.</p>"
        
        for newsletter in newsletters:
            sender = newsletter.get('sender', 'Inconnu')
            subject = newsletter.get('subject', 'Sans sujet')
            body = newsletter.get('bodyHtml', 'Contenu non disponible')
            
            html_body += f"""
            <hr style="border-top: 1px solid #ccc;">
            <div style="margin-bottom: 20px;">
                <h2 style="color: #0056b3;">{subject}</h2>
                <p style="font-style: italic; color: #666;">De : {sender}</p>
                <div>
                    {body}
                </div>
            </div>
            """
        
        # Envoi de l'e-mail
        response = ses_client.send_email(
            Destination={'ToAddresses': [RECIPIENT_EMAIL]},
            Message={
                'Body': {'Html': {'Charset': 'UTF-8', 'Data': html_body}},
                'Subject': {'Charset': 'UTF-8', 'Data': 'Votre résumé hebdomadaire de newsletters'},
            },
            Source=SENDER_EMAIL,
        )
        print("E-mail de résumé envoyé ! Message ID:", response['MessageId'])

        # Supprimer les e-mails de la base de données
        with table.batch_writer() as batch:
            for newsletter in newsletters:
                batch.delete_item(Key={'emailId': newsletter['emailId']})

        return {
            'statusCode': 200,
            'body': json.dumps('E-mail de résumé envoyé et base de données nettoyée.')
        }

    except ClientError as e:
        print(f"Erreur SES: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erreur SES: {e.response['Error']['Message']}")
        }
    except Exception as e:
        print(f"Erreur lors de la génération du résumé: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erreur lors de la génération du résumé: {str(e)}")
        }

