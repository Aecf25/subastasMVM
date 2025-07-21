from rest_framework import serializers
from .models import Usuario, VehicleUser, BidFormat, BidParticipation, Noticias
from django.contrib.auth.hashers import make_password

class VehicleUserSerializer(serializers.ModelSerializer):
    photoVehicle = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = VehicleUser
        fields = '__all__'

    def validate(self, data):
        user = data.get('usuario')
        vehicleId = data.get('vehicleId')

        if isinstance(user, int):
            from .models import Usuario
            user = Usuario.objects.get(id=user)

        if VehicleUser.objects.filter(usuario = user, vehicleId= vehicleId).exists():
            raise serializers.ValidationError({
                'vehicleId': 'Este usuario ya tiene registrado un vehiculo con esta placa.'
            })
        
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    vehiculos = VehicleUserSerializer(many=True, read_only=True)
    photoPerson = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Usuario
        fields = '__all__'

    def validate(self, data):
        if Usuario.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({"username": "El username ya está en uso."})
        if Usuario.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "El email ya está en uso."})
        if Usuario.objects.filter(personId=data.get('personId')).exists():
            raise serializers.ValidationError({"personId": "El personId ya está en uso."})
        return data

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])

        validated_data['is_superuser'] = False
        validated_data['is_staff'] = False
        validated_data['is_active'] = True

        return super().create(validated_data)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'user', 'photoPerson', 'personId', 'phone', 'birthday']

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleUser
        fields = ['id', 'photoVehicle', 'vehicleId', 'typeCar', 'brandCar', 'ownerName']

class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidFormat
        fields = ['id', 'imgBid', 'title', 'direction1', 'direction2', 'timeLimit', 'price', 'winner', 'notificated', 'created', 'estado', 'historial_pujas_activa']
        extra_kwargs = {
            'winner': {'required': False},
            'estado': {'required': False},
            'historial_pujas_activa': {'required': False}
        }

class BidParticipationSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source='usuario.username', read_only=True)
    email = serializers.CharField(source='usuario.email', read_only=True)
    photoPerson = serializers.SerializerMethodField()
    subasta_nombre = serializers.CharField(source='subasta.title', read_only=True) 

    class Meta:
        model = BidParticipation
        fields = ['id', 'subasta', 'subasta_nombre' ,'usuario', 'username' , 'email', 'cantidad', 'fecha', 'photoPerson','vehiculo_info']
        read_only_fields = ['fecha', 'username', 'email', 'photoPerson']

    def get_photoPerson(self, obj):
        request = self.context.get('request')
        if obj.usuario.photoPerson:
            url = obj.usuario.photoPerson.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None
    
class NoticiasMVMSubastas(serializers.ModelSerializer):
    class Meta:
        model = Noticias
        fields = '__all__'
