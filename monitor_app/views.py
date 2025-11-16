from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import SensorData, Device 
from django.db.models import Count
from datetime import datetime
import csv
from django.utils import timezone
import json 

def home_page(request):
    """Página inicial com resumo dos dados do IoT e gerenciamento de dispositivos."""
    if request.method == 'POST':
        name = request.POST.get('name')
        # Capturamos o device_id que é o ID Único/MQTT Topic
        device_id_str = request.POST.get('device_id')
        device_type = request.POST.get('device_type')
        
        if name and device_id_str and device_type:
            # Assumindo que 'device_id' no modelo Device é o campo que armazena o ID Único (RES_001)
            Device.objects.create(
                name=name,
                device_id=device_id_str, 
                device_type=device_type
            )
            return redirect('home')

    # Para exibir o último registro geral e a lista de devices
    devices = Device.objects.all()
    total_dispositivos = devices.count()
    ultimo_registro = SensorData.objects.order_by('-data_registro').first()
    
    # --- NOVO: Encontra o ID do primeiro dispositivo para o link Dashboard na navbar ---
    # Isso evita o erro NoReverseMatch na base.html
    first_device = devices.first()
    first_device_id = first_device.device_id if first_device else None

    context = {
        'total_dispositivos': total_dispositivos,
        'ultimo_registro': ultimo_registro,
        'devices': devices,
        'device_type_choices': Device.DEVICE_TYPE_CHOICES,
        'first_device_id': first_device_id, # Variável adicionada ao contexto
    }
    return render(request, 'home.html', context)

# ----------------------------------------------------------------------
# FUNÇÃO DO DASHBOARD AJUSTADA PARA FILTRAR POR DEVICE_ID
# ----------------------------------------------------------------------
def dashboard_nivel(request, device_id):
    """
    Exibe o dashboard de nível, filtrando os dados pelo ID Único do dispositivo.
    O device_id é o parâmetro string vindo da URL (Ex: 'RES_001').
    """
    
    # 1. Busca o objeto Device pelo ID Único (device_id)
    target_device = get_object_or_404(Device, device_id=device_id)
    
    # 2. Dados para a Tabela (Relatórios Recentes) - FILTRADOS
    registros = SensorData.objects.select_related('device').filter(
        device__device_id=device_id # Filtra pelo ID Único do dispositivo
    ).order_by('-data_registro')[:50]
    
    # 3. Dados para o Gráfico (Todos os registros) - FILTRADOS
    dados_historicos = SensorData.objects.select_related('device').filter(
        device__device_id=device_id # Filtra pelo ID Único do dispositivo
    ).order_by('data_registro').all()

    labels = []
    data = []

    for registro in dados_historicos:
        data_local = timezone.localtime(registro.data_registro)
        # Formato de label para o eixo X
        labels.append(data_local.strftime('%d/%m %H:%M'))
        data.append(registro.nivel)

    # Serializar as listas para strings JSON
    chart_labels_json = json.dumps(labels)
    chart_data_json = json.dumps(data)

    context = {
        'target_device': target_device, # Passa o objeto Device para o template
        'registros': registros,       
        'chart_labels': chart_labels_json, 
        'chart_data': chart_data_json,    
    }
    return render(request, 'dashboard.html', context)


def exportar_relatorio_csv(request):
    """Exporta todos os dados de SensorData para um arquivo CSV."""
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="relatorio_iot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['ID Registro', 'Dispositivo', 'Nível (%)', 'Data/Hora'])

    dados = SensorData.objects.select_related('device').order_by('data_registro').all()
    for registro in dados:
        writer.writerow([
            registro.id,
            registro.device.name if registro.device else 'Desconhecido',
            registro.nivel,
            timezone.localtime(registro.data_registro).strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response

def delete_device(request, device_id):
    """Exclui um dispositivo."""
    # Note que esta view usa o ID do banco de dados (primary key), não o device_id (string/MQTT ID)
    device = get_object_or_404(Device, id=device_id) 
    device.delete()
    return redirect('home')