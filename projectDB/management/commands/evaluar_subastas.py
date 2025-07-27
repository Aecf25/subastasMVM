from django.core.management.base import BaseCommand
from django.utils import timezone
from projectDB.models import BidFormat, BidParticipation, FCMToken, Usuario
from django.contrib.auth import get_user_model
from projectDB.utils.fcm_utils import enviar_notificacion_fcm
from datetime import timedelta

class Command(BaseCommand):
    help = 'Evalúa subastas vencidas y activa la evaluación automática'

    def handle(self, *args, **options):
        ahora = timezone.now()
        dentro_de_una_hora = ahora + timedelta(hours=1, minutes=1)
        
        subastas_activas_vencidas = BidFormat.objects.filter(estado='activa', timeLimit__lte=ahora)
        for subasta in subastas_activas_vencidas:
            print(f"Evaluando subasta {subasta.id} - {subasta.title}")

            puja = BidParticipation.objects.filter(subasta=subasta).order_by('cantidad').first()
            if not puja:
                subasta.estado = 'cancelada'
                subasta.save()
                print(f"Subasta {subasta.id} cancelada porque no hubo participantes.")
                continue

            ganador = puja.usuario
            subasta.estado = 'finalizada'
            subasta.winner = ganador.username
            subasta.save()

            tokens = FCMToken.objects.filter(user=ganador).values_list('token', flat=True)
            for token in tokens:
                enviar_notificacion_fcm(
                token,
                "¡Felicidades! Ganaste la subasta",
                f"Has ganado la subasta '{subasta.title}'.",
                data={"subasta_id": str(subasta.id), "tipo": "ganador_subasta"}
                )

            historial_subasta = {
                'subasta_id': subasta.id,
                'title': subasta.title,
                'cantidad': puja.cantidad,
                'fecha': ahora.isoformat(),
                'pagado': False,
            }
            ganador.historial_subastas_ganadas.append(historial_subasta)

            ganador.cartera += puja.cantidad

            historial_cartera = {
                'subasta_id': subasta.id,
                'title': subasta.title,
                'cantidad': puja.cantidad,
                'fecha': ahora.isoformat(),
                'descripcion': f'Ganador de la subasta número {subasta.id}',
            }
            ganador.historial_cartera.append(historial_cartera)
            ganador.save()
            print(f"Subasta {subasta.id} finalizada. Ganador: {ganador.username}")

        subastas_por_vencer = BidFormat.objects.filter(
            estado='activa', 
            timeLimit__gt=ahora,
            timeLimit__lte=dentro_de_una_hora,
            notificado_expiracion = False
            )
        for subasta in subastas_por_vencer:
            usuarios = Usuario.objects.all()
            for usuario in usuarios:
                tokens = FCMToken.objects.filter(user=usuario).values_list('token', flat=True)
                for token in tokens:
                    enviar_notificacion_fcm(
                        token,
                        "⏰ Subasta por finalizar",
                        f"La subasta '{subasta.title}' finaliza en menos de 1 hora. ¡Aprovecha para participar!",
                        data={
                            "tipo": "subasta_por_finalizar",
                            "subasta_id": str(subasta.id),
                            "title": subasta.title
                        }
                    )
            subasta.notificado_expiracion = True
            subasta.save()
            print(f"🔔 Subasta {subasta.id} notificada como por expirar.")

       

    

