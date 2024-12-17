import time
import flet as ft
from historico_urls import rodar_url
from block_url import rodar_block_url, rodar_unblock_url
from auth_uteis import load_token_from_file, save_token_to_file
from atividade_apps import monitorar_janelas, on_exit
import asyncio
import schedule
import requests
import jwt
import os
from dotenv import load_dotenv
import json
import threading

load_dotenv()
link_api = os.getenv("NGROK_URL")

ultima_mensagem = None


def atualizar_mensagem(page, mensagem_texto, sucesso=True):
    global ultima_mensagem
    # Remove a última mensagem, se existir
    if ultima_mensagem:
        page.remove(ultima_mensagem)

    # Cria nova mensagem
    cor = ft.colors.GREEN if sucesso else ft.colors.RED
    ultima_mensagem = ft.Text(mensagem_texto, color=cor)

    # Adiciona nova mensagem à página
    page.add(ultima_mensagem)
    page.update()


async def executar_funcoes_assincronas(token):
    await rodar_url(token)
    await rodar_block_url(token)
    await monitorar_janelas(token=token)
    await rodar_unblock_url(token)


def executar_funcoes(token):
    asyncio.run(executar_funcoes_assincronas(token))


def iniciar_monitoramento(token):
    # Iniciar as funções agendadas de monitoramento
    schedule.every(5).seconds.do(lambda: executar_funcoes(token))


# Função para obter o ID a partir do token
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


class AppLogin:

    @staticmethod
    def login_filho(page):
        email_field = ft.TextField(
            hint_text="email do filho",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.EMAIL,
            height=40,
            border_color="#58AF9B",
            color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.EMAIL
        )
        senha_field = ft.TextField(
            hint_text="senha",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.LOCK, height=40,
            border_color="#58AF9B", color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD, password=True,
            can_reveal_password=True
        )

        def login_acao(e):
            email = email_field.value
            senha = senha_field.value
            print(f"Email: {email}, Senha: {senha}")
            login = {"email": email, "senha": senha}
            json_login = json.dumps(login)

            response = requests.post(f"{link_api}/auth/login/f", data=json_login,
                                     headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                atualizar_mensagem(page, "Login efetuado com sucesso!")

                token = response.json().get("accessToken")

                expiresIn = response.json().get("expiresIn")

                save_token_to_file(token, expiresIn)
                iniciar_monitoramento(token)
                page.controls.clear()
                AppLogin.tela_pos_login(page, "Maria Joaquina", True, "Felipe")
                page.update()


            elif response.status_code == 401:
                atualizar_mensagem(page, "E-mail ou senha incorretos.", sucesso=False)
                print("Email ou senha incorreto")
            else:
                print("Erro:", response.status_code)
            page.add(email_field, senha_field, ft.ElevatedButton(text="Login", on_click=login_acao))

        def show_register_filho(e):
            page.controls.clear()
            page.add(AppLogin._registrar_conta_filho(page))
            page.update()

        login_filho = ft.Container(
            width=600,
            height=350,
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=600 * 0.40,
                        height=350,
                        bgcolor="#58AF9B",
                        border_radius=ft.border_radius.only(
                            top_left=12,
                            top_right=0,
                            bottom_left=12,
                            bottom_right=0
                        ),
                        padding=ft.padding.only(
                            top=50,
                            left=15,
                            right=5,
                        ),
                        content=ft.Column(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Container(
                                            width=80,
                                            height=80,
                                            border=ft.border.all(1, ft.colors.WHITE),
                                            border_radius=5
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    width=600 * 0.40
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            value="REGISTRAR CONTA",
                                            size=18,
                                            weight=ft.FontWeight.W_900,
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.JUSTIFY
                                        ),
                                        ft.Text(
                                            value="Caso não tenha uma conta, faça o resgistro clicando no botão abaixo",
                                            size=12,
                                            weight="bold",
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.JUSTIFY
                                        ),
                                    ],
                                    spacing=0
                                ),
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            text="REGISTRAR",
                                            color=ft.colors.WHITE,
                                            bgcolor="#58AF9B",
                                            elevation=0,
                                            on_click=show_register_filho,
                                            style=ft.ButtonStyle(
                                                side=ft.BorderSide(
                                                    width=1,
                                                    color=ft.colors.WHITE
                                                )
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            spacing=25
                        )
                    ),

                    ft.Container(
                        width=600 * 0.6,
                        height=350,
                        padding=ft.padding.only(
                            top=50,
                            left=12,
                            right=20,
                        ),
                        content=ft.Column(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            value="LOGIN DO FILHO",
                                            color="#58AF9B",
                                            size=18,
                                            weight="bold",
                                            font_family="Poppins"
                                        ),
                                        ft.Column(
                                            controls=[
                                                email_field,
                                                senha_field,
                                                ft.Row(
                                                    controls=[
                                                        ft.TextButton(text="esqueci minha senha",
                                                                      style=ft.ButtonStyle(
                                                                          color=ft.colors.BLUE,
                                                                      ),
                                                                      )
                                                    ],
                                                    alignment=ft.MainAxisAlignment.END
                                                ),
                                                ft.ElevatedButton(
                                                    text='LOGIN',
                                                    width=600 * 0.60,
                                                    height=40,
                                                    bgcolor="#58AF9B",
                                                    style=ft.ButtonStyle(
                                                        side=ft.BorderSide(
                                                            width=1,
                                                            color=ft.colors.WHITE
                                                        )
                                                    ),
                                                    color=ft.colors.WHITE,
                                                    on_click=login_acao
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )
        return login_filho

    @staticmethod
    def _registrar_conta_filho(page):

        nome_field = ft.TextField(
            hint_text="nome",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.EMAIL,
            height=40,
            border_color="#58AF9B",
            color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.EMAIL
        )

        email_field = ft.TextField(
            hint_text="email do filho",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.EMAIL,
            height=40,
            border_color="#58AF9B",
            color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.EMAIL
        )
        senha_field = ft.TextField(
            hint_text="senha",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.LOCK,
            height=40,
            border_color="#58AF9B",
            color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
            password=True,
            can_reveal_password=True
        )
        confirm_senha_field = ft.TextField(
            hint_text="confirme sua senha",
            hint_style=ft.TextStyle(
                size=15,
                color="#b3b3b3"
            ),
            prefix_icon=ft.icons.LOCK,
            height=40,
            border_color="#58AF9B",
            color=ft.colors.BLACK,
            keyboard_type=ft.KeyboardType.VISIBLE_PASSWORD,
            password=True,
            can_reveal_password=True
        )



        def registrar_acao(e):
            nome = nome_field.value
            email = email_field.value
            senha = senha_field.value
            confirm_senha = confirm_senha_field.value
            if senha == confirm_senha and nome:
                json_register = {"nome": nome, "email": email, "senha": senha}
                print(f" email: {email}   senha {senha}  senha_confirm: {confirm_senha}")
                response = requests.post(f"{link_api}/auth/user/f/registrar", json=json_register,
                                         headers={'Content-Type': 'application/json'})
                if response.status_code == 201: #conta criada e precisa verificar no email
                   print("cadastro feito")
                elif response.status_code == 401:
                    print("conta já existe")
                else:
                    print("Erro:", response.status_code)


        def show_login_filho(e):
            page.controls.clear()
            page.add(AppLogin.login_filho(page))
            page.update()

        registrar_filho = ft.Container(
            width=600,
            height=350,
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=600 * 0.40,
                        height=350,
                        bgcolor="#58AF9B",
                        border_radius=ft.border_radius.only(
                            top_left=12,
                            top_right=0,
                            bottom_left=12,
                            bottom_right=0
                        ),
                        padding=ft.padding.only(
                            top=50,
                            left=15,
                            right=5,
                        ),
                        content=ft.Column(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Container(
                                            width=80,
                                            height=80,
                                            border=ft.border.all(1, ft.colors.WHITE),
                                            border_radius=5
                                        )
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    width=600 * 0.40
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            value="ENTRAR NA CONTA",
                                            size=18,
                                            weight="bold",
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.JUSTIFY
                                        ),
                                        ft.Text(
                                            value="Caso já tenha uma conta, faça login clicando no botão abaixo",
                                            size=12,
                                            weight="bold",
                                            color=ft.colors.WHITE,
                                            text_align=ft.TextAlign.JUSTIFY
                                        ),
                                    ],
                                    spacing=0
                                ),
                                ft.Row(
                                    controls=[
                                        ft.ElevatedButton(
                                            text="ENTRAR",
                                            color=ft.colors.WHITE,
                                            bgcolor="#58AF9B",
                                            elevation=0,
                                            on_click=show_login_filho,
                                            style=ft.ButtonStyle(
                                                side=ft.BorderSide(
                                                    width=1,
                                                    color=ft.colors.WHITE
                                                )
                                            )
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER
                                )
                            ],
                            spacing=25
                        )
                    ),

                    ft.Container(
                        width=600 * 0.6,
                        height=350,
                        padding=ft.padding.only(
                            top=50,
                            left=12,
                            right=20,
                        ),
                        content=ft.Column(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            value="CRIE A CONTA PARA SEU FILHO",
                                            color="#58AF9B",
                                            size=18,
                                            weight="bold",
                                            font_family="Poppins"
                                        ),
                                        ft.Column(
                                            controls=[
                                                nome_field,
                                                email_field,
                                                senha_field,
                                                confirm_senha_field,
                                                ft.ElevatedButton(
                                                    text='REGISTRAR',
                                                    width=600 * 0.60,
                                                    height=40,
                                                    bgcolor="#58AF9B",
                                                    style=ft.ButtonStyle(
                                                        side=ft.BorderSide(
                                                            width=1,
                                                            color=ft.colors.WHITE
                                                        )
                                                    ),
                                                    color=ft.colors.WHITE,
                                                    on_click=registrar_acao
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )
        return registrar_filho

    @staticmethod
    def tela_pos_login(page, nome_usuario, conectado, nome_responsavel=None):
        """
        Tela que exibe a confirmação de login e indica se o usuário tem um responsável vinculado.
        """
        fundo_retangulo = ft.Container(
            bgcolor=ft.colors.BLUE_50,
            padding=20,
            border_radius=10,
            margin=20,
            width=500,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Text(f"Olá, {nome_usuario}!", size=24, weight="bold", color=ft.colors.BLACK),
                    ft.Row(
                        [
                            ft.Icon(ft.icons.CHECK_CIRCLE, color="green") if conectado else ft.Icon(ft.icons.ERROR,
                                                                                                    color="red"),
                            ft.Text("Conectado" if conectado else "Desconectado", size=18, color=ft.colors.BLACK),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Text(
                        f"Você está conectado a um responsável: {nome_responsavel}" if nome_responsavel
                        else "Nenhum responsável vinculado. Por favor, peça a um responsável para adicionar você à conta deles.",
                        size=18,
                        color="gray" if nome_responsavel is None else ft.colors.BLACK
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            )
        )

        page.controls.clear()
        page.add(fundo_retangulo)
        page.update()

def main(page: ft.Page):
    page.horizontal_alignment = "center"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.maximized = True
    page.bgcolor = "#EEE5E5"

    token = load_token_from_file()

    if token:
        AppLogin.tela_pos_login(page, nome_usuario="Enzo Miguel", conectado=True, nome_responsavel="Felipe")
        iniciar_monitoramento(token)
    else:
        page.add(AppLogin.login_filho(page))

    # Função para capturar eventos de fechamento da janela
    def handle_window_event(e):
        if e.data == "close":
            print("Interrompendo o monitorador...")
            on_exit(token)
            page.window_destroy()

    page.window.on_event = handle_window_event

    def run_scheduler():
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            print(f"Erro no agendador: {e}")

    threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main)
