from django.core.management.base import BaseCommand
from django.utils import timezone
from models import BidFormat, BidParticipation
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Evalúa subastas vencidas y activa la evaluación automática'

    def handle(self, *args, **options):
        ahora = timezone.now()
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
            subasta.notificated = True
            subasta.save()

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
