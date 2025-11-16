# core/models.py
from django.db import models

class LeituraNivel(models.Model):
    reservatorio_id = models.CharField(max_length=50) # Ex: reservatorio_01
    nivel_cm = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reservatorio_id} - {self.nivel_cm} cm em {self.timestamp}"