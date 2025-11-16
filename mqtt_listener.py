# monitor/mqtt_listener.py (COMPLETO com LWT e Tratamento de Status)

import os
import django
import json
import paho.mqtt.client as mqtt
from datetime import datetime
from django.utils import timezone

# 1. Configurar o ambiente Django
# IMPORTANTE: Mude 'iot_monitor.settings' para o nome correto do seu projeto.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_monitor.settings') 
django.setup()

# Importar os modelos APÓS o setup do Django
from monitor_app.models import Device, SensorData 

# 2. Configurações do Broker MQTT
MQTT_BROKER = "localhost" 
MQTT_PORT = 1883
# Tópicos de subscrição
MQTT_TOPIC_NIVEL = "iot/nivel/reservatorio" # Tópico para os dados JSON de nível
MQTT_TOPIC_STATUS = "iot/status/#"         # NOVO: Tópico para mensagens de status (LWT)

# 3. Funções de Callback do MQTT

def on_connect(client, userdata, flags, rc):
    """
    Função chamada quando o script se conecta ao broker.
    """
    if rc == 0:
        print(f"✅ Conectado ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}. Retorno: {rc}")
        
        # Inscreve-se nos tópicos
        client.subscribe(MQTT_TOPIC_NIVEL)
        print(f"Subscrito em Dados: {MQTT_TOPIC_NIVEL}")
        
        client.subscribe(MQTT_TOPIC_STATUS)
        print(f"Subscrito em Status (LWT): {MQTT_TOPIC_STATUS}")
    else:
        print(f"❌ Falha na conexão, código de retorno: {rc}")

def on_message(client, userdata, msg):
    """
    Função chamada quando uma mensagem é recebida do broker.
    Separa o tratamento de status e o tratamento de dados de nível.
    """
    try:
        payload_str = msg.payload.decode()
        
        # === 1. LÓGICA PARA ATUALIZAÇÃO DE STATUS (LWT) ===
        # O tópico deve ser no formato 'iot/status/DEVICE_ID'
        if msg.topic.startswith('iot/status/'):
            # Obtém o DEVICE_ID do tópico (a terceira parte)
            device_id = msg.topic.split('/')[2] 
            status = payload_str.strip().upper() # Deve ser 'ONLINE' ou 'OFFLINE'
            
            try:
                device = Device.objects.get(device_id=device_id)
                device.status = status
                device.last_seen = timezone.now()
                device.save()
                print(f"➡️ STATUS LWT ATUALIZADO: {device.name} -> {status}")
                return # Encerra, pois a mensagem era apenas de status

            except Device.DoesNotExist:
                print(f"⚠️ ERRO DE STATUS: Dispositivo {device_id} não encontrado no DB.")
                return

        # === 2. LÓGICA PARA DADOS DE NÍVEL (Se não for status, é dado) ===
        if msg.topic == MQTT_TOPIC_NIVEL:
            data = json.loads(payload_str)
            device_id = data.get('device_id')
            nivel = data.get('nivel')

            if not device_id or nivel is None:
                print("❌ ERRO: Payload JSON incompleto. Requer 'device_id' e 'nivel'.")
                return

            # Encontrar ou Criar o Dispositivo
            device, created = Device.objects.get_or_create(
                device_id=device_id,
                defaults={'name': f"Sensor-{device_id}"}
            )

            # Salvar o Registro de Sensor
            SensorData.objects.create(
                device=device,
                nivel=float(nivel),
                data_registro=timezone.now()
            )
            
            # Garante que ao receber dados, o status seja sempre ONLINE
            device.status = 'ONLINE'
            device.last_seen = timezone.now()
            device.save()
            
            print(f"✅ SUCESSO: Nível {nivel}% de '{device.name}' salvo. Status forçado para ONLINE.")
        
    except json.JSONDecodeError:
        print(f"❌ ERRO JSON: Payload inválido (não é um JSON válido): {payload_str}")
    except Exception as e:
        print(f"❌ ERRO INESPERADO ao processar mensagem: {e}")


# 4. Inicializar e rodar o loop principal

if __name__ == '__main__':
    print("Iniciando Listener MQTT...")
    
    # Cria a instância do cliente MQTT
    client = mqtt.Client(client_id="django_mqtt_listener")
    
    # Associa as funções de callback
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Conecta ao broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Inicia o loop em segundo plano para que ele escute as mensagens
        client.loop_forever() 

    except KeyboardInterrupt:
        print("\nListener MQTT encerrado pelo usuário (Ctrl+C).")
        client.disconnect()
    except Exception as e:
        print(f"Ocorreu um erro ao tentar conectar ou rodar o listener: {e}")