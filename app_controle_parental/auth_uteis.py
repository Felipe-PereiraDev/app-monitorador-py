import datetime
import json
import os
import jwt
import requests
from dotenv import load_dotenv
import os
load_dotenv()

link_api = os.getenv("NGROK_URL")


def getIdToken(token: str) -> str:
    try:
        decoded_payload = jwt.decode(token, options={"verify_signature": False})
        print("Payload decodificado:", decoded_payload)  # Depuração
        return decoded_payload.get('sub')
    except jwt.ExpiredSignatureError:
        print("Token expirado")
    except jwt.InvalidTokenError as e:
        print(f"Token inválido: {e}")
    return None


def getIdRespToken(token: str) -> str:
    try:
        decoded_payload = jwt.decode(token, options={"verify_signature": False})
        print("Payload decodificado:", decoded_payload)
        return decoded_payload.get('idResp')
    except jwt.ExpiredSignatureError:
        print("Token expirado")
    except jwt.InvalidTokenError as e:
        print(f"Token inválido: {e}")
    return None


def load_token_from_file():
    if os.path.exists("token.txt"):
        with open("token.txt", "r") as f:
            data = json.load(f)
            expires_at = datetime.datetime.fromisoformat(data["expires_at"])
            if expires_at > datetime.datetime.now():
                return data["token"]
            else:
                print("Token expirado, realizando novo login.")
    return None


def save_token_to_file(token: str, expires_in: int):
    data = {
        "token": token,
        "expires_at": (datetime.datetime.now() + datetime.timedelta(seconds=expires_in)).isoformat()
    }
    with open("token.txt", "w") as f:
        json.dump(data, f)


def fazer_login(email, senha):
    login = {"email": email, "senha": senha}
    json_login = json.dumps(login)

    response = requests.post(f"{link_api}/auth/login/f", data=json_login,
                             headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        print("Login efetuado com sucesso")
        token = response.json().get("accessToken")
        expiresIn = response.json().get("expiresIn")
        save_token_to_file(token, expiresIn)
        return token
    elif response.status_code == 401:
        print("Email ou senha incorreto")
    else:
        print("Erro:", response.status_code)
