from django.contrib import admin
from .models import Device, SensorData # <-- CORREÇÃO AQUI: Usa os nomes corretos do models.py

# 1. Registro e Personalização do Model SensorData
@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    # Campos a serem exibidos na lista do admin
    list_display = ('device', 'nivel', 'data_registro')
    
    # Filtros laterais para facilitar a busca
    list_filter = ('device', 'data_registro')
    
    # Campos que podem ser pesquisados
    search_fields = ('device__name', 'nivel')
    
    # Adiciona uma navegação hierárquica por data
    date_hierarchy = 'data_registro'

# 2. Registro e Personalização do Model Device
@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    # Campos a serem exibidos na lista do admin
    list_display = ('name', 'device_id')
    
    # Campos que podem ser pesquisados
    search_fields = ('name', 'device_id')