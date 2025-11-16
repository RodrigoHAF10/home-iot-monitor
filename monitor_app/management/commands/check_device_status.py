from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from monitor_app.models import Device

class Command(BaseCommand):
    help = 'Checks the last_seen timestamp of devices and updates their status to OFFLINE if inactive.'

    def handle(self, *args, **options):
        # Define the threshold for considering a device offline (e.g., 30 seconds)
        OFFLINE_THRESHOLD_SECONDS = 30
        offline_threshold = timezone.now() - timedelta(seconds=OFFLINE_THRESHOLD_SECONDS)

        self.stdout.write(self.style.SUCCESS(f"Checking for devices inactive for more than {OFFLINE_THRESHOLD_SECONDS} seconds..."))

        # Get all devices that are currently ONLINE
        online_devices = Device.objects.filter(status='ONLINE')

        for device in online_devices:
            if device.last_seen < offline_threshold:
                device.status = 'OFFLINE'
                device.save()
                self.stdout.write(self.style.WARNING(f"Device '{device.name}' (ID: {device.device_id}) set to OFFLINE due to inactivity."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Device '{device.name}' (ID: {device.device_id}) is ONLINE and active."))
        
        self.stdout.write(self.style.SUCCESS("Device status check complete."))
