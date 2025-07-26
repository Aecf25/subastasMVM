from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.status import HTTP_400_BAD_REQUEST
from .models import Usuario, VehicleUser, BidFormat, BidParticipation, Noticias, UserLoginRecord, FCMToken
from .serializers import UsuarioSerializer, BidSerializer, BidParticipationSerializer, NoticiasMVMSubastas
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import VehicleUserSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from .permissions import IsAdminOrUpdatePriceOnly
from django.utils.crypto import get_random_string
import string 
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from datetime import date
from django.db.models import Count
from django.db.models.functions import ExtractWeek, ExtractYear, ExtractMonth
from django.core.management import call_command
import io
from django.db import IntegrityError
from projectDB.utils.fcm_utils import enviar_notificacion_fcm, notificar_usuarios


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register(request):
    serializer = UsuarioSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        print("❌ Errores de validación:", serializer.errors)
        print("📦 Datos recibidos:", dict(request.data))
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'detail': 'Campos vacíos'}, status=HTTP_400_BAD_REQUEST)
    
    try:
        user = Usuario.objects.get(username=username)
        if check_password(password, user.password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'detail': 'Contraseña incorrecta'}, status=400)
    except Usuario.DoesNotExist:
        return Response({'detail': 'Usuario no encontrado'}, status=400)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile(request):
    user = request.user  # usuario autenticado por el JWT
    if request.method == 'GET':
        serializer = UsuarioSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UsuarioSerializer(user, data=request.data, partial=True)  # partial=True para actualización parcial
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Perfil actualizado correctamente'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

@api_view(['GET'])
def user_list(request):
    users = Usuario.objects.all()
    serializer = UsuarioSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def agregar_vehiculo_por_username(request):
    username = request.data.get('usuario')
    try:
        usuario = Usuario.objects.get(username=username)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=404)

    data = request.data
    data['usuario'] = usuario.id

    # Combinamos los datos y los archivos
    serializer = VehicleUserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    else:
        
        return Response({'error': serializer.errors}, status=400)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    serializer = UsuarioSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_data_view(request):
    user = request.user

    try:
        user_data = UsuarioSerializer(user).data
        return Response(user_data)

    except Usuario.DoesNotExist:
        return Response({'error': 'Perfil de usuario no encontrado.'}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_users_by_day(request):
    data = UserLoginRecord.objects.values('date').annotate(count=Count('user')).order_by('date')
    resultado = [{'date': item['date'], 'count': item['count']} for item in data]
    return Response(resultado)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_users_by_week(request):
    data = UserLoginRecord.objects.annotate(
        year = ExtractYear('date'),
        week = ExtractWeek('date'),
    ).values('year', 'week').annotate(count=Count('user')).order_by('year', 'week')
    resultado = [{'year': item['year'], 'week': item['week'], 'count': item['count']} for item in data]
    return Response(resultado)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_users_by_month(request):
    data= UserLoginRecord.objects.annotate(
        year = ExtractYear('date'),
        month = ExtractMonth('date'),
    ).values('year', 'month').annotate(count= Count('user')).order_by('year', 'month')
    resultado = [{'year': item['year'], 'month': item['month'], 'count': item['count']} for item in data]
    return Response(resultado)


class BidViewSet(viewsets.ModelViewSet):
    queryset = BidFormat.objects.all()
    serializer_class = BidSerializer
    permission_classes = [IsAdminOrUpdatePriceOnly]


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def editar_subasta(request, subasta_id):
    try:
        subasta = BidFormat.objects.get(id=subasta_id)
    except BidFormat.DoesNotExist:
        return Response({'error': 'Subasta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    
    user = request.user
    data = request.data
    
    if user.is_staff or user.is_superuser:
        # Admin: puede actualizar opcionalmente varios campos sin que se borren si no vienen
        fields = ['title', 'price', 'direction1', 'direction2', 'timeLimit' ,'estado']
        for field in fields:
            if field in data:
                value = data[field]
                if value not in [None, '']:
                    setattr(subasta, field, data[field])
        subasta.save()
        serializer = BidSerializer(subasta)
        return Response({'mensaje': 'Subasta actualizada por admin.', 'data': serializer.data}, status=status.HTTP_200_OK)
    
    else:
        # Usuario normal: solo puede cambiar estado a "exitosa"
        nuevo_estado = data.get('estado')
        if nuevo_estado == 'exitosa':
            subasta.estado = 'exitosa'
            subasta.save()
            serializer = BidSerializer(subasta)
            return Response({'mensaje': 'Estado cambiado a exitosa.', 'data': serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No tienes permiso para modificar ese campo o valor.'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_last_login(request):
    user = request.user
    today = date.today()
    user.last_login = now()
    user.save(update_fields=["last_login"])

    UserLoginRecord.objects.get_or_create(user=user, date=today)

    return Response({'mensaje': f'Último inicio de sesión: {user.last_login}'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def realizar_apuesta(request):
    user = request.user
    subasta_id = request.data.get('subasta')
    cantidad = request.data.get('cantidad')

    if not subasta_id or not cantidad:
        return Response({'error': 'El ID de la subasta y la Puja $ es requerido.'}, status=400)
  
    try:
        subasta = BidFormat.objects.get(id=subasta_id)
    except BidFormat.DoesNotExist:
        return Response({'error': 'Subasta no encontrada.'}, status=404)
    
    if cantidad >= subasta.price:
        return Response({"error": f"La puja debe de ser MENOR a la actual: ${subasta.price}"}, status = 400)
    
    data = request.data.copy()
    data['usuario'] = user.id

    try:
        participacion = BidParticipation.objects.get(usuario=user, subasta = subasta)
        serializer = BidParticipationSerializer(participacion, data=data)
        accion = "actualizada"

    except BidParticipation.DoesNotExist:
        serializer = BidParticipationSerializer(data=data)
        accion = "creada"

    if serializer.is_valid():
        serializer.save()

        if accion == 'creada':
            user.participaciones_subastas +=1
            user.pujas_realizadas +=1
            user.save()
        if accion == 'actualizada':
            user.pujas_realizadas +=1
            user.save()

        subasta.price = cantidad

        if accion == 'creada':
            mensaje = 'ha ofertado'
        else:
            mensaje = 'ha contra-ofertado'
        
        entrada_historial = {
            'usuario_id': user.id,
            'nombre': user.get_full_name() or user.username,
            'cantidad': cantidad,
            'mensaje': mensaje,
            'fecha': timezone.now().isoformat()
        }

        historial = subasta.historial_pujas_activa or []
        historial.append(entrada_historial)
        subasta.historial_pujas_activa = historial

        subasta.save()
        return Response({
            'mensaje': f'Participación {accion} correctamente.',
            'data': serializer.data
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ver_participantes_subasta(request, subasta_id):
    try:
        participaciones = BidParticipation.objects.filter(subasta=subasta_id)
        serializer = BidParticipationSerializer(participaciones, many=True,  context={'request': request})
        return Response(serializer.data)
    except:
        return Response({"error": "Subasta no encontrada."}, status=404)
    
@api_view(['POST'])
def enviar_codigo(request):
    from django.utils import timezone
    from datetime import timedelta

    email = request.data.get('email')
    try:
        user = Usuario.objects.get(email = email)
        codigo = get_random_string(length=6, allowed_chars= string.ascii_letters + string.digits)
        user.codigo_recuperacion = codigo
        user.codigo_expiracion = timezone.now() + timedelta(minutes=30)
        user.save()

        send_mail(
            'Codigo de Recuperación',
            f"Tu Codigo de recuperacion es: {codigo}",
            'mvmsubastas@gmail.com',
            [email],
            fail_silently=False
        )
        return Response({'mensaje': 'Código enviado'}, status=200)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'El correo no está registrado.'}, status=404)
    
@api_view(['POST'])
def verificar_codigo(request):
    from django.utils import timezone
    email = request.data.get('email')
    codigo = request.data.get('codigo')

    try:
        user = Usuario.objects.get(email = email)

        if user.codigo_expiracion and timezone.now() > user.codigo_expiracion:
            user.codigo_recuperacion = None
            user.codigo_expiracion = None
            user.save()
            return Response({'error': 'El código ha expirado'}, status=400)
        
        if user.codigo_recuperacion == codigo:
            return Response({'mensaje': 'Codigo válido'}, status=200)
        else:
            return Response({'mensaje': 'Codigo inválido'}, status=400)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'Correo no encontrado'}, status=404)
    
@api_view(['POST'])
def cambiar_contraseña(request):
    email = request.data.get('email')
    nueva_contraseña = request.data.get('nueva_contraseña')
    try:
        user = Usuario.objects.get(email = email)
        user.set_password(nueva_contraseña)
        user.codigo_recuperacion = None
        user.save()
        return Response({'mensaje': 'Contraseña actualizada correctamente'}, status=200)
    except Usuario.DoesNotExist:
        return Response({'mensaje': 'Correo no encontrado'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluar_subasta(request, subasta_id):
    try:
        subasta = BidFormat.objects.get(id=subasta_id)
    except BidFormat.DoesNotExist:
        return Response({'error': 'Subasta no encontrada'}, status=404)

    if not request.user.is_staff:
        return Response({'error': 'El usuario debe ser un admin.'}, status=403)

    if subasta.estado != 'activa':
        return Response({'error': 'La subasta ya ha sido evaluada.'}, status=400)

    # Obtener parámetro opcional 'ganador' desde la URL
    username_ganador = request.query_params.get('ganador', None)

    if username_ganador:
        try:
            ganador = get_user_model().objects.get(username=username_ganador)
        except get_user_model().DoesNotExist:
            return Response({'error': f'Usuario "{username_ganador}" no existe.'}, status=404)

        # Verificar que participó en la subasta
        puja = BidParticipation.objects.filter(subasta=subasta, usuario=ganador).first()
        if not puja:
            return Response({'error': f'El usuario "{username_ganador}" no participó en la subasta.'}, status=400)
    else:
        # Seleccionar ganador automáticamente por puja más baja
        puja = BidParticipation.objects.filter(subasta=subasta).order_by('cantidad').first()
        if not puja:
            subasta.estado = 'cancelada'
            subasta.save()
            return Response({'mensaje': 'Subasta cancelada. No hubo participantes.'}, status=200)
        ganador = puja.usuario

    # Declarar ganador
    subasta.estado = 'finalizada'
    subasta.winner = ganador.username
    subasta.save()

    token_obj = FCMToken.objects.filter(user=ganador).first()
    if token_obj:
        enviar_notificacion_fcm(
            token_obj.token,
            "¡Felicidades! Ganaste la subasta",
            f"Has ganado la subasta '{subasta.title}'.",
            data={"subasta_id": str(subasta.id), "tipo": "ganador_subasta"}
        )

    fecha_actual = timezone.now() 
    historial_subasta = {
        'subasta_id': subasta.id,
        'title': subasta.title,
        'cantidad': puja.cantidad,
        'fecha': fecha_actual.isoformat(),
        'pagado': False,
    }
    ganador.historial_subastas_ganadas.append(historial_subasta)

    ganador.cartera += puja.cantidad

    historial_cartera = {
        'subasta_id': subasta.id,
        'title': subasta.title,
        'cantidad': puja.cantidad,
        'fecha': fecha_actual.isoformat(),
        'descripcion': f'Ganador de la subasta número {subasta.id}',
    }
    ganador.historial_cartera.append(historial_cartera)
    ganador.save()

    mensaje = f'El ganador de la subasta {subasta.title} es: {ganador.username}.'
    return Response({'mensaje': mensaje}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_subasta(request, subasta_id):
    try:
        subasta = BidFormat.objects.get(id = subasta_id)
    except:
        return Response({'error': 'Subasta no encontrada'}, status=404)
    
    if not request.user.is_staff:
        return Response({'error': 'No autorizado'}, status=403)
    if subasta.estado != 'activa':
        return Response({'error': 'Solo se puede cancelar una subasta activa'}, status=400)

    subasta.estado = 'cancelada'
    subasta.save()
    return Response({'message': 'Subasta cancelada manualmente'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_notificacion_subasta(request, subasta_id):
    try:
        subasta = BidFormat.objects.get(id=subasta_id)
    except BidFormat.DoesNotExist:
        return Response({'error': 'Subasta no encontrada'}, status=404)

    if subasta.winner != request.user.username:
        return Response({'error': 'No autorizado para confirmar esta subasta.'}, status=403)

    if subasta.notificated:
        return Response({'mensaje': 'Ya confirmaste esta subasta.'}, status=200)

    subasta.notificated = True
    subasta.save()

    return Response({'mensaje': 'Notificación confirmada correctamente.'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_entrega_subasta(request, subasta_id):
    try:
        subasta = BidFormat.objects.get(id=subasta_id)
    except:
        return Response({'error': 'Subasta no encontrada'}, status=404)

    if subasta.estado != 'finalizada':
        return Response({'error': 'Subasta aún no ha sido finalizada'}, status=400)

    if subasta.winner != request.user.username:
        return Response({'error': 'Solo el ganador puede marcar la entrega'}, status=403)

    subasta.estado = 'exitosa'
    subasta.save()
    return Response({'message': 'Subasta marcada como exitosa'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actualizar_estado_conexion(request, userId):
    try:
        user = Usuario.objects.get(id=userId)
    except Usuario.DoesNotExist:
        return Response({'error': 'Error el usuario no existe'}, status= 404)
    
    connected = request.data.get('connected')

    if connected is None or not isinstance(connected, bool):
        return Response({'error': 'Campo "connected" inválido o ausente. Debe ser booleano.'}, status=400)

    user.connected = connected
    user.save()

    return Response({'message': f'el usuario {userId} se encuentra {connected}'}, status=200)

@api_view(['POST'])
@parser_classes([MultiPartParser])
def agregarNoticia(request):
    print('DATA RECIBIDA:', request.data)
    serializer = NoticiasMVMSubastas(data=request.data)
    if serializer.is_valid():
        noticia = serializer.save()
        
        # Obtener todos los usuarios para notificar
        usuarios = Usuario.objects.all()
        
        titulo = "Nueva noticia creada"
        mensaje = f"Se ha publicado una noticia: {noticia.title}"
        data = {
            "tipo": "nueva_noticia",
            "noticia_id": str(noticia.id),
            "title": noticia.title,
        }
        
        # Enviar notificaciones a todos los usuarios
        notificar_usuarios(usuarios, titulo, mensaje, data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        print('ERRORES DEL SERIALIZER:', serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def obtenerNoticias(request):
    noticias = Noticias.objects.all().order_by('-date')
    serializer = NoticiasMVMSubastas(noticias, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
def borrar_noticia(request, id):
    try:
        noticia = Noticias.objects.get(id=id)
        noticia.delete()
        return Response({'mensaje' : 'Noticia eliminada correctamente'}, status= status.HTTP_204_NO_CONTENT)
    except:
        return Response({'error': 'Noticia no encontrada'}, status= status.HTTP_404_BAD_REQUEST)

@api_view(['GET'])  # o POST si quieres
def evaluar_subastas_view(request):
    if request.query_params.get("clave") != "5487996asd5a5sd4AAsd2a4": 
        return Response({"detail": "No autorizado"}, status=403)

    buffer = io.StringIO()
    call_command('evaluar_subastas', stdout=buffer)
    return Response({'output': buffer.getvalue()})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subastas_ganadas_no_notificadas(request):
    user = request.user
    subastas = BidFormat.objects.filter(
        winner = user.username,
        estado = 'finalizada',
        notificated = False
    ).values('id', 'title', 'price')

    return Response({'subastas': list(subastas)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_subastas_como_notificadas(request):
    user = request.user
    ids = request.data.get('ids', [])
    BidFormat.objects.filter(id__in=ids, winner=user.username).update(notificated=True)
    
    return Response({'message': 'Subastas marcadas como notificadas'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_token_fcm(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token requerido'}, status=400)

    try:
        # Opción 1: Crear solo si no existe combinación user-token
        obj, created = FCMToken.objects.get_or_create(user=request.user, token=token)
        return Response({'detail': 'Token registrado correctamente'})
    except IntegrityError:
        return Response({'error': 'Token ya registrado'}, status=400)
    except Exception as e:
        print(f'Error al registrar token FCM: {e}')
        return Response({'error': 'Error interno del servidor'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def eliminar_token_fcm(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token requerido'}, status=400)

    deleted, _ = FCMToken.objects.filter(user=request.user, token=token).delete()
    if deleted:
        return Response({'detail': 'Token FCM eliminado correctamente'})
    else:
        return Response({'detail': 'Token no encontrado'}, status=404)

#.\venv\Scripts\Activate
#python manage.py runserver 0.0.0.0:8000