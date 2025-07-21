import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DBDjango.settings')
django.setup()

User = get_user_model()

username = 'admin'
email = 'admin@example.com'
password = 'admin1234'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superusuario creado.")
else:
    print("ℹ️ El superusuario ya existe.")

# Borra el script para que no se ejecute de nuevo
try:
    os.remove(__file__)
    print("Script eliminado para no volver a ejecutarse.")
except Exception as e:
    print(f"No se pudo eliminar el script: {e}")