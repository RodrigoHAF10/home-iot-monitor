from django.urls import path
from . import views

urlpatterns = [
    # Rota para a Home: /monitor/ (Página de Gerenciamento)
    path('', views.home_page, name='home'), 
    
    # Rota DINÂMICA para o Dashboard: /monitor/dashboard/RES_001/
    # <str:device_id> captura o ID único do dispositivo (ex: RES_001)
    path('dashboard/<str:device_id>/', views.dashboard_nivel, name='dashboard_device'), 
    
    # Rota CORRETA para exportação de Relatórios CSV
    path('relatorios/exportar/', views.exportar_relatorio_csv, name='exportar_csv'), 
    
    # Rota para deletar dispositivo
    path('device/delete/<int:device_id>/', views.delete_device, name='delete_device'),
]