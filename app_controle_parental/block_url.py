import json
import os
import requests
from auth_uteis import getIdToken, getIdRespToken
from dotenv import load_dotenv
import os
load_dotenv()

link_api = os.getenv("NGROK_URL")


# Função para carregar as URLs bloqueadas de um arquivo
async def load_blocked_urls():
    try:
        with open("blocked_urls.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Função para adicionar uma URL ao arquivo hosts
async def block_url_in_hosts(url):
    hosts_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"  # Caminho do arquivo hosts no Window
    entries = [
        f"127.0.0.1 {url}\n",
        f"127.0.0.1 www.{url}\n"
    ]

    try:
        with open(hosts_path, "a") as hosts_file:
            hosts_file.writelines(entries)
            print(f"URLs bloqueadas no hosts: {url}, www.{url}")

        flush_dns()
        with open(hosts_path, "r") as hosts_file:
            lines = hosts_file.readlines()
            if any(f"127.0.0.1 {url}" in line or f"127.0.0.1 www.{url}" in line for line in lines):
                print(f"URL {url} bloqueada com sucesso.")
                flush_dns()
            else:
                print(f"Falha ao bloquear URL {url}.")
    except PermissionError:
        print("Erro: Você precisa de permissões administrativas para modificar o arquivo hosts.")


# Função para bloquear uma URL (adiciona à lista de bloqueio)
async def block_url(url):
    blocked_urls = await load_blocked_urls()
    if url not in blocked_urls:
        blocked_urls.append(url)
        with open("blocked_urls.json", "w") as f:
            json.dump(blocked_urls, f)
        print(f"URL bloqueada: {url}")
        await block_url_in_hosts(url)
        return {'url': url}
    else:
        print(f"URL {url} já está bloqueada")
        return {'url': url}


# Função  obter URLs a partir da API
async def fetch_blocked_urls(id_resp, token):
    api_url = f"{link_api}/user/f/{id_resp}/bloquear-url"
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url=api_url, headers=headers)

        if response.status_code == 200:
            blocked_urls = [(item['url'], item['id']) for item in
                            response.json()]  # Retorna uma lista de tuplas (url, id)
            return blocked_urls
        else:
            print(f"Erro ao buscar URLs bloqueadas: {response.status_code}")
            return []

    except requests.ConnectionError:
        print("Erro de conexão: Verifique se a API está rodando e acessível.")
        return []

    except requests.Timeout:
        print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
        return []

    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a API: {e}")
        return []


async def is_url_blocked(url):
    blocked_urls = await load_blocked_urls()
    return url in blocked_urls


def flush_dns():
    os.system("ipconfig /flushdns")


async def update_blocked_urls(id_resp, payload, token):
    api_url = f"{link_api}/user/f/{id_resp}/bloquear-url"
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        response = requests.put(url=api_url, headers=headers, json=payload)

        if response.status_code == 204:
            print("URLs bloqueadas com sucesso.")
        else:
            print(f"Erro ao atualizar URLs bloqueadas: {response.status_code}")

    except requests.ConnectionError:
        print("Erro de conexão: Verifique se a API está rodando e acessível.")
    except requests.Timeout:
        print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a API: {e}")


async def rodar_block_url(token):
    if token:
        id_filho = getIdToken(token)
        id_resp = getIdRespToken(token)
        blocked_urls_from_api = await fetch_blocked_urls(id_resp, token)  # Adicionei await aqui

        if id_filho and id_resp:
            if blocked_urls_from_api:
                payload = []
                for url, url_id in blocked_urls_from_api:
                    result = await block_url(url)  # Adicionei await aqui
                    if result:
                        payload.append(result)
                flush_dns()
                await update_blocked_urls(id_resp, payload, token)  # Adicionei await aqui
        else:
            print("Erro ao pegar ID do usuário")


async def fetch_url_para_desbloquear(token):
    api_url = f"{link_api}/user/f/desbloquear-url"
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url=api_url, headers=headers)

        if response.status_code == 200:
            blocked_urls = [item['url'] for item in response.json()]  # Retorna uma lista de URLs
            return blocked_urls
        else:
            print(f"Erro ao buscar URLs bloqueadas: {response.status_code}")
            return []

    except requests.ConnectionError:
        print("Erro de conexão: Verifique se a API está rodando e acessível.")
        return []

    except requests.Timeout:
        print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
        return []

    except requests.RequestException as e:
        print(f"Ocorreu um erro ao acessar a API: {e}")
        return []


async def unblock_url_in_hosts(url):
    hosts_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"  # Caminho do arquivo hosts no Windows

    try:
        with open(hosts_path, "r") as hosts_file:
            lines = hosts_file.readlines()
        if any(f"127.0.0.1 {url}" in line or f"127.0.0.1 www.{url}" in line for line in lines):
            lines = [line for line in lines if f"127.0.0.1 {url}" not in line and f"127.0.0.1 www.{url}" not in line]

            with open(hosts_path, "w") as hosts_file:
                hosts_file.writelines(lines)

            print(f"URL desbloqueada no hosts: {url}, www.{url}")
            flush_dns()
        else:
            print(f"A URL {url} não estava bloqueada no arquivo hosts.")

    except PermissionError:
        print("Erro: Você precisa de permissões administrativas para modificar o arquivo hosts.")

    except FileNotFoundError:
        print(f"Erro: O arquivo hosts não foi encontrado em {hosts_path}.")

    except IOError as e:
        print(f"Ocorreu um erro ao acessar o arquivo hosts: {e}")


async def unblock_url(url):
    blocked_urls = await load_blocked_urls()

    if url in blocked_urls:
        blocked_urls.remove(url)  # Remove a URL da lista
        with open("blocked_urls.json", "w") as f:
            json.dump(blocked_urls, f)

        print(f"URL desbloqueada: {url}")
        flush_dns()
        await unblock_url_in_hosts(url)
        return {'url': url}
    else:
        print(f"URL {url} não está bloqueada.")
        return None


async def update_unblocked_urls(urls, token):
    api_url = f"{link_api}/user/f/desbloquear-url"
    for url in urls:
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.delete(url=api_url, headers=headers, json={"url": url["url"]})

            if response.status_code == 204:
                print("URLs desbloqueadas com sucesso.")
            else:
                print(f"Erro ao atualizar URLs desbloqueadas: {response.status_code}")

        except requests.ConnectionError:
            print("Erro de conexão: Verifique se a API está rodando e acessível.")
        except requests.Timeout:
            print("O tempo de conexão foi excedido. Tente novamente mais tarde.")
        except requests.RequestException as e:
            print(f"Ocorreu um erro ao acessar a API: {e}")


# Função principal para rodar o desbloqueio de URLs
async def rodar_unblock_url(token):
    if token:
        id_filho = getIdToken(token)
        blocked_urls_from_api = await fetch_url_para_desbloquear(token)
        if id_filho:
            if blocked_urls_from_api:
                urls = []
                for url in blocked_urls_from_api:
                    result = await unblock_url(url)
                    if result:
                        urls.append(result)

                flush_dns()
                await update_unblocked_urls(urls, token)
        else:
            print("Erro ao pegar ID do usuário")
