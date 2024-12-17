import psutil
import win32gui
import win32process
from datetime import datetime
import json
import requests
from dotenv import load_dotenv
import os
load_dotenv()

link_api = os.getenv("NGROK_URL")

estado_anterior = []
processos_ignorados = [
    "ApplicationFrameHost.exe", "CalculatorApp.exe", "TextInputHost.exe",
    "SystemSettings.exe", "explorer.exe", "RtkUWP.exe", "svchost.exe", "csrss.exe"
]

def listar_janelas_abertas():
    janelas_abertas = []

    def callback(hwnd, janelas):
        if win32gui.IsWindowVisible(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                processo = psutil.Process(pid)
                nome_processo = processo.name()
                hora_abertura = datetime.fromtimestamp(processo.create_time()).strftime(
                    "%Y-%m-%d %H:%M:%S")  # Hora de criação do processo

                if nome_processo not in processos_ignorados:
                    janelas.append((nome_processo, hora_abertura))

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    win32gui.EnumWindows(callback, janelas_abertas)

    return janelas_abertas


def salvar_no_bd(token, processo, hora_abertura):
    api_url = f"{link_api}/user/f/apps-abertos"

    hora_inicio_iso = datetime.strptime(hora_abertura, "%Y-%m-%d %H:%M:%S").isoformat()

    data_lista = {
        "nome": processo,
        "hora_inicio": hora_inicio_iso,
        "ativo": True
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    json_data = json.dumps(data_lista)

    try:
        response = requests.post(api_url, data=json_data, headers=headers)
        if response.status_code == 200:
            print("Atividade enviada com sucesso")
        else:
            print(f"Erro ao enviar o histórico: {response.status_code}")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao enviar os dados: {e}")


def remover_janelas_bd(token, processos):
    api_url = f"{link_api}/user/f/apps-atualizar"

    print(processos)
    for processo in processos:
        nome_processo = processo[0]
        data_lista = {
            "nome": nome_processo,
            "ativo": False
        }
        print(data_lista)

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }


        json_data = json.dumps(data_lista)

        try:

            response = requests.put(api_url, data=json_data, headers=headers)
            if response.status_code == 204:
                print(f"Estado da janela '{nome_processo}' modificado para (False) com sucesso.")
            else:
                print(f"Erro ao atualizar a janela '{nome_processo}': {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Ocorreu um erro ao enviar os dados para '{nome_processo}': {e}")

async def monitorar_janelas(token: str, intervalo=5):
    global estado_anterior
    estado_atual = listar_janelas_abertas()


    novas_janelas = [janela for janela in estado_atual if janela not in estado_anterior]
    janelas_fechadas = [janela for janela in estado_anterior if janela not in estado_atual]

    if novas_janelas:
        for janela in novas_janelas:
            processo, hora_abertura = janela
            print(f"Nova janela aberta -> Processo: {processo}, Iniciado em: {hora_abertura}")
            salvar_no_bd(token, processo, hora_abertura)

    if janelas_fechadas:
        remover_janelas_bd(token, janelas_fechadas)


    estado_anterior = estado_atual


def remover_janelas_inativas(lista_apps, token):
    lista = []
    for janela in lista_apps:
        processo, _ = janela
        print(f"Janela fechada -> Processo: {processo}, Iniciado em: {_}")
        lista.append({"nome": processo})

    api_url = f"{link_api}/user/f/apps-atualizar"

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    json_data = json.dumps(lista)

    try:
        response = requests.put(api_url, data=json_data, headers=headers)
        if response.status_code == 200:
            print("Estado da janela modificada pra (False) com sucesso")
        else:
            print(f"Erro ao enviar o histórico: {response.status_code}")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao enviar os dados: {e}")


def on_exit(token):
    try:

        remover_janelas_bd(token, estado_anterior)
        print("Monitorador encerrado. Atividades atualizadas.")
    except Exception as e:
        print(f"Ocorreu um erro ao encerrar o monitorador: {e}")
