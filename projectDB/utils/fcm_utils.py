import os
import json
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from projectDB.models import FCMToken

SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
PROJECT_ID = "mvm-subastas"  

def get_authorized_session():
    if os.environ.get('RENDER') == 'true':
        firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS')
        credentials_dict = json.loads(firebase_credentials_json)
        creds = service_account.Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
    else:
        creds = service_account.Credentials.from_service_account_file(
            os.path.join(os.path.dirname(__file__), '../keys/firebase-service-account.json'),
            scopes=SCOPES
        )
    return AuthorizedSession(creds)

def enviar_notificacion_fcm(token_fcm, titulo, cuerpo, data=None):
    session = get_authorized_session()
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    message = {
        "message": {
            "token": token_fcm,
            "notification": {
                "title": titulo,
                "body": cuerpo,
            },
            "android": {
                "notification": {
                    "sound": "default",
                    "channel_id": "high_importance_channel",
                }
            },
            "data": data or {},
        }
    }
    response = session.post(url, json=message)
    
    if response.status_code == 200:
        print(f"✅ Notificación enviada a token: {token_fcm}")
    elif response.status_code == 404 or "Invalid registration token" in response.text:
        print(f"⚠️ Token inválido, eliminando: {token_fcm}")
        FCMToken.objects.filter(token=token_fcm).delete()
    else:
        print(f"❌ Error enviando a {token_fcm}: {response.status_code} {response.text}")

def notificar_usuarios(usuarios, titulo, mensaje, data=None):
    for user in usuarios:
        tokens = FCMToken.objects.filter(user=user).values_list('token', flat=True)
        for token in tokens:
            enviar_notificacion_fcm(token, titulo, mensaje, data)
