import datetime
import json
import browser_history
import pytz
import requests
from auth_uteis import getIdToken
from dotenv import load_dotenv
import os
load_dotenv()

link_api = os.getenv("NGROK_URL")

last_sent_data = None


def get_history(token: str, id):
    global last_sent_data

    try:
        local_tz = pytz.timezone('America/Sao_Paulo')
        now_local = datetime.datetime.now(local_tz)
        today = now_local.date()  # Obtém apenas a data
        date_time_obj = datetime.datetime.combine(today, datetime.time.min)
        date_time_obj = date_time_obj.replace(tzinfo=None)
    except ValueError:
        print("Formato de data inválido! Por favor, tente novamente.")
        return

    # Obtém o histórico do navegador
    outputs = browser_history.get_history()
    H = outputs.to_csv().replace('\r', '').split('\n')[::-1][1:]

    data_list = []

    seen_urls = set()

    url_limit = 80
    conteudo_limit = 50

    for i in H:
        try:
            h = i.split(',', maxsplit=2)
            if len(h) < 3:
                continue

            date = h[0]
            url = h[1]
            content = h[2]  # Obtém o conteúdo

            date_dt = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S%z')
            date_dt = date_dt.replace(tzinfo=None)

            url = url[:url_limit]
            content = content[:conteudo_limit]

            if url not in seen_urls and date_dt > date_time_obj:
                data_list.append({
                    "url": url,
                    "dataVisitada": date_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "conteudo": content.strip()
                })
                seen_urls.add(url)

        except (IndexError, ValueError):
            continue

    if data_list and data_list != last_sent_data:
        api_url = f"{link_api}/user/f/historico-sites"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        json_data = json.dumps(data_list)
        try:
            response = requests.post(api_url, data=json_data, headers=headers)
            if response.status_code == 200:
                print("Histórico enviado com sucesso!")
                last_sent_data = data_list
            else:
                print(f"Erro ao enviar o histórico: {response.status_code}")
        except requests.RequestException as e:
            print(f"Ocorreu um erro ao enviar os dados: {e}")
    else:
        print("Nenhum dado novo para enviar.")


async def rodar_url(token):
    if token:
        id_user = getIdToken(token)
        if id_user:
            get_history(token, id_user)
        else:
            print("Erro ao pegar ID do usuário")
