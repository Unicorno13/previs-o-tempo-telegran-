import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

# Carrega variáveis do .env
load_dotenv()

OWM_API_KEY = os.getenv("OWM_API_KEY")
LAT = os.getenv("LAT")
LON = os.getenv("LON")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Para controlar envio diário
ultima_data_diaria = None
alerta_enviado = False

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code == 200:
            print("[INFO] Mensagem enviada com sucesso!")
        else:
            print(f"[ERRO] Falha ao enviar mensagem. Status code: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"[ERRO] Não foi possível enviar a mensagem: {e}")

def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OWM_API_KEY}&units=metric&lang=pt_br"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[ERRO] Falha ao pegar a previsão: {e}")
        return None

def generate_daily_message(data, hoje):
    previsoes = [p for p in data["list"] if p["dt_txt"].startswith(hoje)]
    if not previsoes:
        return None

    temp_min = min([p["main"]["temp_min"] for p in previsoes])
    temp_max = max([p["main"]["temp_max"] for p in previsoes])
    chuva_total = sum([p.get("rain", {}).get("3h", 0) for p in previsoes])
    chance_chuva = "Alta" if chuva_total > 10 else "Média" if chuva_total > 3 else "Baixa"

    mensagem = f"🌤️ Previsão diária ({hoje}):\n"
    mensagem += f"🌡️ Temperatura: {temp_min:.1f}°C a {temp_max:.1f}°C\n"
    mensagem += f"🌧️ Chance de chuva: {chance_chuva}\n"

    return mensagem

def check_alert(data, hoje):
    previsoes = [p for p in data["list"] if p["dt_txt"].startswith(hoje)]
    if not previsoes:
        return None

    chuva_total = sum([p.get("rain", {}).get("3h", 0) for p in previsoes])
    if chuva_total > 20:
        return "🚨 Alerta: Possibilidade de chuva forte e risco de alagamentos!"
    return None

def main_loop():
    global ultima_data_diaria, alerta_enviado
    while True:
        agora = datetime.now()
        hoje = agora.strftime("%Y-%m-%d")
        data = get_weather()
        if not data:
            time.sleep(300)
            continue

        # Mensagem diária
        if ultima_data_diaria != hoje:
            diaria = generate_daily_message(data, hoje)
            if diaria:
                send_message(diaria)
                ultima_data_diaria = hoje

        # Alerta de chuva forte
        alerta = check_alert(data, hoje)
        if alerta and not alerta_enviado:
            send_message(alerta)
            alerta_enviado = True
        elif not alerta:
            alerta_enviado = False  # reset se não houver mais risco

        # Espera 5 minutos antes de checar novamente
        time.sleep(300)

if __name__ == "__main__":
    print("[INFO] Iniciando script inteligente...")
    main_loop()
