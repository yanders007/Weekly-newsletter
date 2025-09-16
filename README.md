# Weekly-newsletter
Comment ça marche ?
Le projet se décompose en deux parties principales, chacune gérée par une fonction AWS Lambda distincte : .
Ingestion des E-mails (IngestNewsletterLambda) :
Déclencheur : Un e-mail est reçu par AWS SES.
Action : AWS SES stocke l'e-mail brut dans un bucket S3 et déclenche cette fonction Lambda.
Fonction de la Lambda : Elle lit l'e-mail depuis S3, en extrait l'expéditeur, le sujet et le corps HTML, puis stocke ces informations dans une table DynamoDB.
Génération du Résumé (SummarizeNewslettersLambda) :
Déclencheur : Une règle Amazon EventBridge (CloudWatch Events) exécute cette fonction une fois par semaine (par exemple, tous les dimanches).
Fonction de la Lambda : Elle scanne la table DynamoDB pour tous les e-mails reçus au cours des 7 derniers jours. Elle génère un résumé HTML avec le contenu de chaque newsletter. Enfin, elle envoie ce résumé à votre adresse e-mail via AWS SES et supprime les e-mails de la base de données.
Prérequis
Un compte AWS avec les permissions nécessaires pour les services suivants :
AWS Lambda
Amazon S3
Amazon DynamoDB
AWS SES
Amazon EventBridge
Python 3.8 ou supérieur.
Adresse e-mail vérifiée dans AWS SES pour l'envoi et la réception d'e-mails.
Un bucket S3 configuré dans AWS SES pour stocker les e-mails entrants.
Déploiement
1. Configuration de l'environnement
Assurez-vous de définir les variables d'environnement suivantes dans les configurations de vos fonctions Lambda sur la console AWS :
DYNAMODB_TABLE_NAME : Nom de votre table DynamoDB (ex: NewsletterSummaries).
SES_EMAIL_BUCKET : Nom du bucket S3 où SES stocke les e-mails.
SENDER_EMAIL : Votre adresse e-mail vérifiée pour envoyer le résumé.
RECIPIENT_EMAIL : Votre adresse e-mail pour recevoir le résumé.
AWS_REGION : La région AWS où vous déployez les services.
2. Déploiement des fonctions Lambda
Créez une fonction Lambda et collez le code de la section "1. Fonction Lambda : Ingestion d'e-mails" (nommez-la par exemple test.py).
Créez une seconde fonction Lambda et collez le code de la section "2. Fonction Lambda : Génération du résumé" (nommez-la par exemple test2.py).
3. Configuration des déclencheurs
Pour IngestNewsletterLambda, ajoutez un déclencheur de type "SES" et liez-le à la réception d'e-mails sur l'adresse de votre choix.
Pour SummarizeNewslettersLambda, ajoutez un déclencheur de type "EventBridge (CloudWatch Events)". Créez une nouvelle règle avec un taux de planification (par exemple, cron(0 12 ? * SUN *) pour un déclenchement chaque dimanche à midi).