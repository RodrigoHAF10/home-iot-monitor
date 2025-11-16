from django.db import models
from django.utils import timezone

class Device(models.Model):
    """
    Representa um dispositivo IoT (sensor) que envia dados.
    Isto permite agrupar os dados por dispositivo.
    """
    DEVICE_TYPE_CHOICES = [
        ('NIVEL', 'Sensor de Nível'),
        ('PRESSAO', 'Sensor de Pressão'),
        ('VAZAO', 'Sensor de Vazão'),
        ('VALVULA', 'Válvula Solenoide'),
    ]

    STATUS_CHOICES = [
        ('ONLINE', 'Online'),
        ('OFFLINE', 'Offline'),
        ('ERROR', 'Com Erro'),
    ]

    # Nome do dispositivo, mostrado no Dashboard
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nome do Dispositivo"
    )
    # Identificador único (pode ser o ID MQTT)
    device_id = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name="ID Único"
    )
    # Tipo de dispositivo
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='SENSOR',
        verbose_name="Tipo de Dispositivo"
    )
    # Status do dispositivo
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OFFLINE',
        verbose_name="Status"
    )
    # Última vez que o dispositivo foi visto
    last_seen = models.DateTimeField(
        default=timezone.now,
        verbose_name="Última Vez Visto"
    )

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"

    def __str__(self):
        return self.name

class SensorData(models.Model):
    """
    Armazena os registros de nível de água enviados pelos dispositivos.
    """
    # Relação: Um registro pertence a um Device
    device = models.ForeignKey(
        Device, 
        on_delete=models.CASCADE,
        verbose_name="Dispositivo"
    )
    
    # O nível de água registrado (em porcentagem)
    nivel = models.FloatField(
        help_text="Nível de água em porcentagem (0-100)",
        verbose_name="Nível (%)"
    ) 
    
    # O carimbo de data/hora do registro (usado para o gráfico e relatório)
    data_registro = models.DateTimeField(
        auto_now_add=True, # Define automaticamente na criação
        verbose_name="Data e Hora do Registro"
    ) 

    class Meta:
        # Ordena por data mais recente primeiro
        ordering = ['-data_registro']
        verbose_name = "Registro de Sensor"
        verbose_name_plural = "Registros de Sensor"

    def __str__(self):
        return f"Nível {self.nivel}% - {self.device.name}"