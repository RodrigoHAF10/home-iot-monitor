# core/views.py
from django.shortcuts import render
from .models import LeituraNivel

def dashboard_nivel(request):
    # Busca a última leitura de cada reservatório
    reservatorios = LeituraNivel.objects.order_by('reservatorio_id', '-timestamp').distinct('reservatorio_id')
    
    context = {
        'ultimas_leituras': reservatorios
    }
    return render(request, 'core/dashboard.html', context)