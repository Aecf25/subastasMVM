from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField

class Usuario(AbstractUser):
    birthday = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    personId = models.CharField(max_length=50)
    name = models.CharField(max_length=50, null=True, blank=True)
    photoPerson = CloudinaryField('photoUser',folder='person_photos/', null=True, blank=True)
    cartera = models.IntegerField(
        default = 0.00
    )
    codigo_recuperacion = models.CharField(max_length=10, null=True, blank=True)
    codigo_expiracion = models.DateTimeField(null=True, blank=True)
    historial_cartera = models.JSONField(default=list, blank=True)
    historial_subastas_ganadas = models.JSONField(default=list, blank=True)
    participaciones_subastas = models.IntegerField(default=0, blank=True)
    pujas_realizadas= models.IntegerField(default=0, blank=True)
    connected = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class VehicleUser(models.Model):
        usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name= 'vehiculos')
        ownerName = models.CharField(max_length=50)
        typeCar = models.CharField(max_length=50)
        brandCar = models.CharField(max_length=50)
        vehicleId = models.CharField(max_length=50)
        photoVehicle = CloudinaryField('photoVehicle',folder='vehicle_photos/', null=True, blank=True)
        
        def __str__(self):
            return f"{self.brandCar} - {self.vehicleId}"
        
class BidFormat(models.Model):
     imgBid = CloudinaryField('photoBid',folder='subastas_photos/',null=True, blank=True)
     title = models.CharField(max_length=50)
     direction1 = models.CharField(max_length=150)
     direction2 = models.CharField(max_length=150)
     timeLimit = models.DateTimeField()
     price = models.IntegerField()
     winner = models.CharField(max_length=50, blank= True, default= '')
     notificated = models.BooleanField(default=False)
     created = models.DateTimeField(auto_now_add=True)
     ESTADOS = [
        ('activa', 'Activa'),
        ('finalizada', 'Finalizada'),
        ('exitosa', 'Exitosa'),
        ('cancelada', 'Cancelada'),
     ]
     estado = models.CharField(max_length=20, choices=ESTADOS, default='activa')
     historial_pujas_activa = models.JSONField(default=list, blank=True)

     def __str__(self):
          return f"{self.title} - {self.price}"
     
class BidParticipation(models.Model):
    subasta = models.ForeignKey(BidFormat, on_delete=models.CASCADE, related_name="participantes")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="participaciones")
    cantidad = models.IntegerField()  
    fecha = models.DateTimeField(auto_now=True)
    vehiculo_info = models.JSONField(null=True, blank=True)

    class Meta:
        unique_together = ('usuario', 'subasta') #Solo 1 participacion por subasta
        verbose_name = 'Participación en subasta'
        verbose_name_plural = 'Participaciones en subasta'

    def __str__(self):
        return f"{self.usuario.username} apostó {self.cantidad} en {self.subasta.title}"

class Noticias(models.Model):
     title = models.CharField(max_length=70)
     body = models.TextField()
     creator = models.CharField(max_length=70)
     date = models.DateTimeField(auto_now=True)
     portada = CloudinaryField('photoNews',folder='noticias_photos/', null=True, blank=True)
     
     def __str__(self):
          return f"Noticia: {self.title}, creada el {self.date} por {self.creator}"
     
class UserLoginRecord(models.Model):
    user = models.ForeignKey(Usuario, on_delete= models.CASCADE)
    date = models.DateField()

    class Meta:
          unique_together = ('user', 'date')

    def __str__(self):
     return f'{self.user.username} - {self.date}'