import os
import hashlib
import socket
import json
import threading
import random
import uuid
import sys

# Capturar argumentos da linha de comando
if len(sys.argv) != 3:
    print("Uso: python3 cliente.py <IP> <DIRETORIO>")
    sys.exit(1)

SERVER_IP = sys.argv[1]
diretorio = sys.argv[2]


# Validar o diretório fornecido
if not os.path.isdir(diretorio):
    print(f"[ERRO] O diretório '{diretorio}' não foi encontrado.")
    sys.exit(1)

SERVER_PORT = 13377
porta = SERVER_PORT

def iniciar_servidor_tcp(porta, diretorio):
    """Inicia o servidor TCP para enviar imagens."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_server:
            tcp_server.bind(("0.0.0.0", int(porta)))  # Ouvindo em todas as interfaces
            tcp_server.listen(5)
            print(f"[LOG] Servidor TCP rodando na porta {porta}...")

            while True:
                conn, addr = tcp_server.accept()
                print(f"[LOG] Conexão recebida de {addr}")
                thread = threading.Thread(target=handle_cliente_tcp, args=(conn, diretorio))
                thread.start()
    except Exception as e:
        print(f"[ERRO] Erro ao iniciar servidor TCP: {e}")

def handle_cliente_tcp(conn, diretorio):
    """Lida com solicitações de download de imagens via TCP."""
    try:
        dados = conn.recv(1024).decode()
        if dados.startswith("GET"):
            _, md5 = dados.split()
            # Procura a imagem no diretório com base no MD5
            for arquivo in os.listdir(diretorio):
                caminho = os.path.join(diretorio, arquivo)
                if calcular_md5(caminho) == md5:
                    with open(caminho, "rb") as f:
                        while chunk := f.read(4096):
                            conn.sendall(chunk)
                    print(f"[LOG] Imagem {arquivo} enviada com sucesso.")
                    break
            else:
                print(f"[ERRO] Imagem com MD5 {md5} não encontrada.")
        else:
            print("[ERRO] Comando inválido recebido.")
    except Exception as e:
        print(f"[ERRO] Erro ao processar solicitação do cliente TCP: {e}")
    finally:
        conn.close()


def calcular_md5(arquivo):
    """Calcula o hash MD5 de um arquivo."""
    print(f"[LOG] Calculando o hash MD5 do arquivo: {arquivo}")
    with open(arquivo, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
        print(f"[LOG] Hash MD5 calculado para {arquivo}: {md5}")
        return md5

def registrar_cliente():
    """Registra o cliente no servidor."""
    global PORTA_TCP
    global diretorio
    global senha_cliente

    try:
        print("[LOG] Iniciando registro do cliente...")
        senha = uuid.uuid4().hex[:16]  # Gera uma senha de 16 caracteres
        senha_cliente = senha  # Atribuir senha gerada à variável global
        print(f"[LOG] Senha do cliente: {senha}")

        porta_tcp = porta
        print(f"[LOG] Utilizando porta {porta_tcp}.")

        # Salva a porta TCP globalmente
        PORTA_TCP = porta_tcp
        thread = threading.Thread(target=iniciar_servidor_tcp, args=(porta_tcp, diretorio))
        thread.daemon = True
        thread.start()


        print(f"[LOG] Diretório fornecido: {diretorio}")
        if not os.path.isdir(diretorio):
            print(f"[ERRO] O diretório '{diretorio}' não foi encontrado.")
            return

        imagens = []
        print("[LOG] Listando arquivos no diretório...")
        for arquivo in os.listdir(diretorio):
            caminho = os.path.join(diretorio, arquivo)
            if os.path.isfile(caminho):
                print(f"[LOG] Arquivo encontrado: {caminho}")
                md5 = calcular_md5(caminho)
                imagens.append(f"{md5},{arquivo}")

        if not imagens:
            print("[ERRO] Nenhum arquivo válido encontrado no diretório.")
            return

        print(f"[LOG] Arquivos para registro: {imagens}")
        # Formata a mensagem como string exigida pelo enunciado
        lista_imagens = ";".join(imagens)  # Junta imagens no formato MD5,NOME
        mensagem = f"REG {senha} {porta_tcp} {lista_imagens}"

        print(f"[LOG] Enviando mensagem de registro para o servidor: {mensagem}")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            try:
                # Decodifica a resposta JSON do servidor
                resposta = json.loads(response.decode())
                if resposta["status"] == "OK":
                    print(f"[LOG] Cliente registrado com sucesso: {resposta['message']}")
                else:
                    print(f"[ERRO] Falha no registro do cliente: {resposta['message']}")
            except json.JSONDecodeError:
                print(f"[ERRO] Resposta inesperada do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante o registro do cliente: {e}")


def listar_imagens():
    """Lista imagens disponíveis na rede."""
    try:
        print("[LOG] Solicitando lista de imagens ao servidor...")
        mensagem = "LST"

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(4096)
            resposta = json.loads(response.decode())

            if resposta["status"] == "OK":
                print("[LOG] Imagens disponíveis:")
                for idx, imagem in enumerate(resposta["imagens"], 1):
                    md5, nome, *clientes = imagem.split(",")
                    num_peers = len(clientes)
                    print(f"{idx} - {num_peers} peers - {nome} - {clientes}")
            else:
                print(f"[ERRO] Não foi possível listar imagens: {resposta['message']}")

    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao listar imagens: {e}")

def atualizar_registro():
    """Atualiza o registro do cliente no servidor."""
    global PORTA_TCP, diretorio
    try:
        print("[LOG] Atualizando registro do cliente no servidor...")

        # Verifica se o diretório é válido
        if not os.path.isdir(diretorio):
            print(f"[ERRO] O diretório '{diretorio}' não foi encontrado.")
            return

        # Lista as imagens no diretório e calcula o MD5
        imagens = []
        for arquivo in os.listdir(diretorio):
            caminho = os.path.join(diretorio, arquivo)
            if os.path.isfile(caminho):
                md5 = calcular_md5(caminho)
                imagens.append(f"{md5},{arquivo}")

        # Prepara a mensagem de atualização
        lista_imagens = ";".join(imagens)
        mensagem = f"UPD {PORTA_TCP} {lista_imagens}"

        # Envia a mensagem ao servidor
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            resposta = json.loads(response.decode())

            if resposta["status"] == "OK":
                print(f"[LOG] Registro atualizado com sucesso: {resposta['message']}")
            else:
                print(f"[ERRO] Falha ao atualizar registro: {resposta['message']}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao atualizar registro: {e}")

def remover_registro():
    """Remove o registro do cliente no servidor."""
    global PORTA_TCP
    try:
        print("[LOG] Solicitando remoção do registro no servidor...")
        mensagem = f"DEL {PORTA_TCP}"

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            print(f"[LOG] Resposta do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao remover registro: {e}")


def fazer_download():
    """Realiza o download de uma imagem."""
    try:
        print("[LOG] Solicitando lista de imagens para download...")
        mensagem = "LST"

        # Solicita a lista de imagens do servidor
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(4096)
            resposta = json.loads(response.decode())

            if resposta["status"] != "OK":
                print("[ERRO] Não foi possível obter a lista de imagens.")
                return

            lista_imagens = resposta["imagens"]
            if not lista_imagens:
                print("[ERRO] Nenhuma imagem disponível para download.")
                return

            print("[LOG] Imagens disponíveis:")
            for idx, imagem in enumerate(lista_imagens, 1):
                md5, nome, *clientes = imagem.split(",")
                print(f"{idx}. {nome} - MD5: {md5} - Clientes: {', '.join(clientes)}")

            escolha = int(input("Escolha o número da imagem para download: ")) - 1
            if escolha < 0 or escolha >= len(lista_imagens):
                print("[ERRO] Escolha inválida.")
                return

            imagem_escolhida = lista_imagens[escolha]
            md5, nome, *clientes = imagem_escolhida.split(",")
            ip_porta = clientes[0].split(":")
            ip, porta = ip_porta[0], int(ip_porta[1])

            print(f"[LOG] Iniciando download de {nome} do cliente {ip}:{porta}...")

            # Conexão TCP com o cliente que possui a imagem
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client:
                tcp_client.connect((ip, porta))
                tcp_client.sendall(f"GET {md5}".encode())

                # Salva a imagem recebida
                with open(nome, "wb") as f:
                    while True:
                        dados = tcp_client.recv(4096)
                        if not dados:
                            break
                        f.write(dados)

            print(f"[LOG] Download de {nome} concluído!")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao realizar o download: {e}")

        
def desconectar_cliente():
    """Desconecta o cliente do servidor."""
    global PORTA_TCP
    try:
        if not PORTA_TCP:
            print("[ERRO] Porta TCP não registrada. Registre-se antes de desconectar.")
            return

        print("[LOG] Solicitando desconexão do servidor...")
        senha = input("Digite sua senha para desconexão: ")
        mensagem = {
            "command": "END",
            "senha": senha_cliente,
            "porta": PORTA_TCP
        }


        print(f"[LOG] Enviando mensagem de desconexão: {mensagem}")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            print(f"[LOG] Resposta do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante a desconexão: {e}")

def main():
    """Menu principal do cliente."""
    global PORTA_TCP
    while True:
        print("\nMENU:")
        print("1 - Registrar no servidor")
        print("2 - Listar imagens")
        print("3 - Baixar imagens")
        print("4 - Atualizar registro")
        print("5 - Remover registro do servidor")
        print("6 - Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            registrar_cliente()
        elif opcao == "2":
            listar_imagens()
        elif opcao == "3":
            fazer_download()
        elif opcao == "4":
            atualizar_registro()
        elif opcao == "5":
            remover_registro()
        elif opcao == "6":
            print("[LOG] Encerrando cliente.")
            break
        else:
            print("[ERRO] Opção inválida!")


if __name__ == "__main__":
    main()
