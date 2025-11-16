from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitor_app.models import Device # Importa o seu modelo Device

class Command(BaseCommand):
    help = 'Verifica e marca como OFFLINE os dispositivos que não enviam dados há mais tempo que o limite (timeout).'

    def handle(self, *args, **options):
        # 1. Define o limite de tempo (TIMEOUT)
        # Se o seu ESP32 envia dados a cada 60 segundos, 10 minutos é um limite seguro.
        OFFLINE_THRESHOLD = timedelta(minutes=10)
        
        # 2. Calcula o momento limite
        momento_limite = timezone.now() - OFFLINE_THRESHOLD

        # 3. Encontra dispositivos que estão ONLINE, mas não foram vistos desde o momento limite
        devices_to_update = Device.objects.filter(
            status='ONLINE',
            last_seen__lt=momento_limite
        )
        
        count = devices_to_update.count()
        
        if count > 0:
            # 4. Atualiza o status em massa
            devices_to_update.update(status='OFFLINE')
            self.stdout.write(self.style.WARNING(f'⚠️ Foram atualizados {count} dispositivos para OFFLINE (Timeout de {OFFLINE_THRESHOLD.seconds // 60} min).'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Todos os dispositivos ONLINE estão ativos dentro do limite.'))