import os
import tempfile
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    # Detectar si estamos en producción (Render)
    if os.environ.get('RENDER') == 'true':
        firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS')
        if not firebase_credentials_json:
            raise Exception("Variable FIREBASE_CREDENTIALS no encontrada en entorno de producción")

        # Crear archivo temporal para la credencial JSON
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_file.write(firebase_credentials_json.encode('utf-8'))
            temp_file.flush()
            cred = credentials.Certificate(temp_file.name)

        app = firebase_admin.initialize_app(cred)
        return app
    else:
        # Entorno local: cargar archivo JSON físico
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path_local = os.path.join(BASE_DIR, 'keys', 'mvm-subastas-firebase-adminsdk-fbsvc-73f08d9323.json')
        cred = credentials.Certificate(path_local)
        app = firebase_admin.initialize_app(cred)
        return app
