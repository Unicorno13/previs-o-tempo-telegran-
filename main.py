import requests
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")  # sua chave do OpenWeather

# Cidades e coordenadas (ABC Paulista + SP)
CIDADES = {
    "São Paulo": {"lat": -23.5505, "lon": -46.6333},
    "São Bernardo do Campo": {"lat": -23.691, "lon": -46.564},
    "Diadema": {"lat": -23.681, "lon": -46.620},
    "Santo André": {"lat": -23.663, "lon": -46.538},
    "Ribeirão Pires": {"lat": -23.713, "lon": -46.387},
    "Mauá": {"lat": -23.667, "lon": -46.461},
}

# Função para enviar mensagem pelo Telegram
def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERRO] Falha ao enviar mensagem: {e}")

# Função para pegar previsão do OpenWeather
def pegar_previsao(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=10)
        dados = r.json()
        temp = dados["main"]["temp"]
        temp_min = dados["main"]["temp_min"]
        temp_max = dados["main"]["temp_max"]
        umidade = dados["main"]["humidity"]
        clima = dados["weather"][0]["description"].capitalize()
        vento = dados["wind"]["speed"]
        chuva = dados.get("rain", {}).get("1h", 0)
        return {
            "temp": temp,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "umidade": umidade,
            "clima": clima,
            "vento": vento,
            "chuva": chuva,
        }
    except Exception as e:
        print(f"[ERRO] Falha ao obter previsão: {e}")
        return None

# Função para criar alerta
def criar_alerta(previsao):
    alertas = []
    if previsao["temp"] >= 40:
        alertas.append("🔥 Temperatura muito alta!")
    if previsao["umidade"] < 30:
        alertas.append("🌵 Tempo seco! UR < 30%")
    if previsao["chuva"] >= 10:
        alertas.append("💧 Possível alagamento! Chuva intensa")
    if "trovoada" in previsao["clima"].lower():
        alertas.append("⚡ Possíveis raios!")
    if previsao["vento"] >= 15:
        alertas.append("💨 Ventos fortes!")
    return "\n".join(alertas)

# Função principal
def main():
    ult_temps = {cidade: None for cidade in CIDADES}
    while True:
        for cidade, coord in CIDADES.items():
            previsao = pegar_previsao(coord["lat"], coord["lon"])
            if previsao:
                # Verifica mudança grande de temperatura
                ultima_temp = ult_temps[cidade]
                if ultima_temp is None or abs(previsao["temp"] - ultima_temp) >= 3:
                    ult_temps[cidade] = previsao["temp"]
                    
                    data = datetime.now().strftime("%d/%m/%Y %H:%M")
                    mensagem = f"🌤️ <b>Previsão do dia - {cidade}</b>\n📅 {data}\n"
                    mensagem += f"🌡️ Temperatura: {previsao['temp_min']}°C - {previsao['temp_max']}°C (Atual: {previsao['temp']}°C)\n"
                    mensagem += f"💧 Umidade relativa do ar: {previsao['umidade']}%\n"
                    mensagem += f"🌥️ Condição do céu: {previsao['clima']}\n"
                    mensagem += f"💨 Vento: {previsao['vento']} m/s\n"
                    mensagem += f"🌧️ Chuva na última hora: {previsao['chuva']} mm\n"

                    alertas = criar_alerta(previsao)
                    if alertas:
                        mensagem += f"\n⚠️ <b>Alertas:</b>\n{alertas}"

                    enviar_telegram(mensagem)
        print("[INFO] Previsão enviada. Aguardando próxima atualização...")
        time.sleep(90 * 60)  # aguarda 90 minutos

if __name__ == "__main__":
    main()
