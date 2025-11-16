#include <WiFi.h>
#include <PubSubClient.h>
#include <DNSServer.h>
#include <WebServer.h>
#include <WiFiManager.h> 
#include <ArduinoJson.h> 

// Pino usado para forçar o reset das configurações do WiFiManager
#define PIN_RESET_CONFIG 0 

// =================================================================
// 0. CONFIGURAÇÕES GERAIS (AJUSTAR!)
// =================================================================

// --- CONFIGURAÇÃO MQTT ---
char mqtt_server[40] = "192.168.18.229"; // IP do seu PC com o Broker
const int MQTT_PORT = 1883;
const char* MQTT_USER = ""; 
const char* MQTT_PASSWORD = ""; 

// 🚨 TÓPICOS AJUSTADOS para combinar com o Python
const char* MQTT_TOPIC_NIVEL = "iot/nivel/reservatorio"; // Tópico para dados de nível
const char* MQTT_TOPIC_STATUS_BASE = "iot/status/"; // Tópico base para status LWT

// ID do Dispositivo e ID do Cliente MQTT
const char* device_id = "MCD-01"; 
const char* clientID = "ESP32_MCD-01";

// Intervalo de tempo entre cada envio de dados (em milissegundos)
const long INTERVALO_LEITURA_MS = 10000; // 10 segundos
unsigned long ultimoTempoPublicacao = 0;

// =================================================================
// 1. CONFIGURAÇÕES DO SENSOR E CALIBRAÇÃO 🌊
// =================================================================

// Pinos do sensor ultrassônico
#define PIN_TRIG 5
#define PIN_ECHO 18 

// Distância mínima do sensor para ser considerado "cheio" (padrão 20.0 cm)
const float DISTANCIA_MINIMA = 20.0; 

// --- DADOS DO RESERVATÓRIO (🚨 AJUSTE ESTES VALORES MANUAIS 🚨) ---
const float LARGURA_TANQUE_CM = 80.0; 
const float COMPRIMENTO_TANQUE_CM = 80.0; 
// Distância do sensor ao fundo do tanque (Tanque Vazio) (Exemplo: 120.0)
const float DISTANCIA_SENSOR_FUNDO_CM = 120.0; 
// --- FIM DOS AJUSTES MANUAIS ---

// Altura útil máxima (calculada)
const float ALTURA_UTIL_MAX_CM = DISTANCIA_SENSOR_FUNDO_CM - DISTANCIA_MINIMA;

// Capacidade Total (L): (Altura útil * Largura * Comprimento) / 1000
const float CAPACIDADE_TOTAL_L = (ALTURA_UTIL_MAX_CM * LARGURA_TANQUE_CM * COMPRIMENTO_TANQUE_CM) / 1000.0;

// Variáveis de estado global
float distancia_medida_filtrada = 0.0;
float nivel_percentual = 0.0; 
float litros_atuais = 0.0; 

// =================================================================
// 2. FUNÇÕES DE CONEXÃO E CONFIGURAÇÃO
// =================================================================

WiFiClient espClient;
PubSubClient client(espClient);

// Função para gerar o tópico de status completo (ex: iot/status/MCD-01)
char mqtt_status_topic[60];

void setup_wifi() {
    WiFiManager wm;
    
    // Parâmetro customizado para o IP do Broker
    WiFiManagerParameter custom_mqtt_server("server", "MQTT Server IP", mqtt_server, 40);

    wm.addParameter(&custom_mqtt_server);
    
    const char* ap_ssid = "Monitor_Caixa_Config"; 
    
    if (digitalRead(PIN_RESET_CONFIG) == LOW) {
      Serial.println("Reset de configuracoes solicitado via GPIO 0.");
      wm.resetSettings();
      delay(1000);
    }
    
    Serial.println("Iniciando WiFiManager...");
    
    // Tenta conectar automaticamente, ou inicia o portal de configuração
    if (!wm.autoConnect(ap_ssid)) {
        Serial.println("Falha ao conectar e atingiu o timeout, reiniciando...");
        delay(3000);
        ESP.restart();
    } 
    
    // Pega o IP do Broker que foi configurado (seja o default ou o salvo)
    strcpy(mqtt_server, custom_mqtt_server.getValue());
    
    Serial.println("WiFi conectado!");
    Serial.print("Endereço IP Local: ");
    Serial.println(WiFi.localIP());
    Serial.print("MQTT Broker: ");
    Serial.println(mqtt_server);
}

// FUNÇÃO RECONNECT COM LWT (LAST WILL AND TESTAMENT)
void reconnect() {
    // Constrói o tópico de status (ex: iot/status/MCD-01)
    snprintf(mqtt_status_topic, 60, "%s%s", MQTT_TOPIC_STATUS_BASE, device_id);

    while (!client.connected()) {
        Serial.print("Tentando conexão MQTT...");
        
        // 🚨 LWT ajustado para "OFFLINE" (igual ao Python)
        if (client.connect(clientID, MQTT_USER, MQTT_PASSWORD, mqtt_status_topic, 0, true, "OFFLINE")) {
            Serial.println("conectado.");
            
            // Publica status ONLINE (Com Retain = true, para ser o último estado)
            client.publish(mqtt_status_topic, "ONLINE", true);
            Serial.print("Status ONLINE publicado em: ");
            Serial.println(mqtt_status_topic);
            delay(100); // Pequeno delay para garantir processamento
        } else {
            Serial.print("falhou, rc=");
            Serial.print(client.state());
            Serial.println(" Tentando novamente em 5 segundos");
            delay(5000);
        }
    }
}

// =================================================================
// 3. FUNÇÕES DE MEDIÇÃO ULTRASSÔNICA E CÁLCULO DE NÍVEL
// =================================================================

float medirDistancia() {
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);

    long duracao = pulseIn(PIN_ECHO, HIGH, 30000); 

    if (duracao == 0) return -1; 

    float distancia = (duracao * 0.0343) / 2; 
    return distancia;
}

void calcularNivel() {
    float altura_agua;
    float altura_util_maxima = ALTURA_UTIL_MAX_CM;

    if (altura_util_maxima <= 0.1) {
        nivel_percentual = 0.0;
        litros_atuais = 0.0;
        return;
    }

    if (distancia_medida_filtrada <= DISTANCIA_MINIMA) {
        altura_agua = altura_util_maxima;
        nivel_percentual = 100.0;
    } else if (distancia_medida_filtrada >= DISTANCIA_SENSOR_FUNDO_CM) {
        altura_agua = 0.0;
        nivel_percentual = 0.0;
    } else {
        altura_agua = DISTANCIA_SENSOR_FUNDO_CM - distancia_medida_filtrada;
        nivel_percentual = (altura_agua / altura_util_maxima) * 100.0;
    }

    if (nivel_percentual < 0.0) nivel_percentual = 0.0;
    if (nivel_percentual > 100.0) nivel_percentual = 100.0;

    litros_atuais = (nivel_percentual / 100.0) * CAPACIDADE_TOTAL_L;
}

float lerNivelSensor() {
    float medicoes[10];
    int medicoes_validas = 0;

    for (int i = 0; i < 10; i++) {
        float dist = medirDistancia();
        if (dist > 0 && dist < 400) { 
            medicoes[medicoes_validas] = dist;
            medicoes_validas++;
        }
        delay(50); 
    }

    if (medicoes_validas >= 7) { 
        // Lógica de ordenação (Bubble Sort simplificado)
        for (int i = 0; i < medicoes_validas - 1; i++) {
            for (int j = i + 1; j < medicoes_validas; j++) {
                if (medicoes[i] > medicoes[j]) {
                    float temp = medicoes[i];
                    medicoes[i] = medicoes[j];
                    medicoes[j] = temp;
                }
            }
        }

        // Média das 3 medições centrais
        float soma = 0;
        int inicio = (medicoes_validas - 3) / 2; 
        for (int i = inicio; i < inicio + 3; i++) {
            soma += medicoes[i];
        }
        distancia_medida_filtrada = soma / 3.0;
        
        calcularNivel();
        
        Serial.print("Distância filtrada: "); Serial.print(distancia_medida_filtrada, 1);
        Serial.print(" cm | Nível: "); Serial.print(nivel_percentual, 1); Serial.print("% | Litros: "); Serial.println(litros_atuais, 1);

    } else {
        Serial.print("Poucas medições válidas (< 7, foram "); Serial.print(medicoes_validas); Serial.println("). Mantendo valor anterior.");
        if (distancia_medida_filtrada > 0.0) calcularNivel();
    }
    
    return nivel_percentual;
}

// =================================================================
// 4. FUNÇÃO DE PUBLICAÇÃO DE DADOS AJUSTADA
// =================================================================

void publish_data() {
    // Checa se o WiFi está ativo antes de tentar publicar
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi desconectado. Pulando publicação.");
      return;
    }
    
    float nivel_agua_percentual = lerNivelSensor(); 
    
    StaticJsonDocument<256> doc; 

    // 🚨 PAYLOAD AJUSTADO para combinar com o Python
    doc["device_id"] = device_id;
    doc["nivel"] = nivel_agua_percentual;
    // 🚨 REMOVIDOS campos extras para simplificar o payload
    // O Python espera apenas 'device_id' e 'nivel'
    
    char jsonBuffer[256]; 
    serializeJson(doc, jsonBuffer);

    Serial.print("Publicando dados MQTT no tópico "); Serial.print(MQTT_TOPIC_NIVEL); Serial.print(": ");
    Serial.println(jsonBuffer);

    if (client.publish(MQTT_TOPIC_NIVEL, jsonBuffer)) {
        Serial.println("Publicação MQTT bem-sucedida.");
    } else {
        Serial.println("Falha na publicação MQTT. (Broker nao alcancavel?)");
    }
}

// =================================================================
// 5. SETUP E LOOP
// =================================================================

void setup() {
    Serial.begin(115200);
    delay(100);
    
    pinMode(PIN_RESET_CONFIG, INPUT_PULLUP);
    
    // Inicialização dos pinos do sensor
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_ECHO, INPUT);
    digitalWrite(PIN_TRIG, LOW); 

    // Inicialização do WiFi (via WiFiManager)
    setup_wifi();

    // Inicialização do MQTT (usando o IP configurado)
    client.setServer(mqtt_server, MQTT_PORT);
    
    Serial.print("Capacidade do tanque configurada para "); Serial.print(CAPACIDADE_TOTAL_L, 1); Serial.println(" Litros.");
}

void loop() {
    // Garante que o cliente MQTT está conectado. Se não estiver, chama reconnect()
    if (!client.connected()) {
        reconnect();
    }
    client.loop(); // Processa mensagens pendentes

    unsigned long agora = millis();
    if (agora - ultimoTempoPublicacao >= INTERVALO_LEITURA_MS) {
        ultimoTempoPublicacao = agora;
        publish_data();
    }
}