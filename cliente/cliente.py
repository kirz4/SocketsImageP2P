import os
import hashlib
import socket
import threading
import uuid
import sys
import imghdr

if len(sys.argv) != 3:
    print("Uso: python3 cliente.py <IP_SERVIDOR> <DIRETORIO>")
    sys.exit(1)

SERVER_IP = sys.argv[1]
diretorio = sys.argv[2]

if not os.path.isdir(diretorio):
    print(f"[ERRO] O diretório '{diretorio}' não foi encontrado.")
    sys.exit(1)

SERVER_PORT = 13377

senha_cliente = None
PORTA_TCP = None

def calcular_md5(arquivo):
    with open(arquivo, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def iniciar_servidor_tcp(diretorio):
    # Cria socket TCP, porta = 0 para aleatória
    tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server.bind(("0.0.0.0", 0))
    tcp_server.listen(5)
    porta = tcp_server.getsockname()[1]
    print(f"[LOG] Servidor TCP interno iniciado na porta {porta}...")
    global PORTA_TCP
    PORTA_TCP = porta

    while True:
        conn, addr = tcp_server.accept()
        thread = threading.Thread(target=handle_cliente_tcp, args=(conn, diretorio))
        thread.start()

def handle_cliente_tcp(conn, diretorio):
    try:
        dados = conn.recv(1024).decode()
        if dados.startswith("GET"):
            _, md5 = dados.split()
            # Envia a imagem com esse MD5, se encontrada
            encontrada = False
            for arquivo in os.listdir(diretorio):
                caminho = os.path.join(diretorio, arquivo)
                # Verifica se é imagem
                if os.path.isfile(caminho) and imghdr.what(caminho) is not None:
                    if calcular_md5(caminho) == md5:
                        encontrada = True
                        with open(caminho, "rb") as f:
                            while True:
                                chunk = f.read(4096)
                                if not chunk:
                                    break
                                conn.sendall(chunk)
                        break
            # se não encontrada, não faz nada
        # se não for GET, ignora
    except Exception as e:
        print(f"[ERRO] Erro no servidor TCP interno: {e}")
    finally:
        conn.close()

def registrar_cliente():
    global senha_cliente

    senha = uuid.uuid4().hex[:16]
    senha_cliente = senha

    # Inicia thread do servidor TCP interno (porta aleatória)
    thread = threading.Thread(target=iniciar_servidor_tcp, args=(diretorio,))
    thread.daemon = True
    thread.start()

    # Espera um pouco para garantir que a thread já obteve a PORTA_TCP
    import time
    time.sleep(0.5) 

    if not PORTA_TCP:
        print("[ERRO] Não foi possível obter porta TCP.")
        return

    # Lista apenas arquivos de imagem
    imagens = []
    for arquivo in os.listdir(diretorio):
        caminho = os.path.join(diretorio, arquivo)
        if os.path.isfile(caminho) and imghdr.what(caminho) is not None:
            md5 = calcular_md5(caminho)
            imagens.append(f"{md5},{arquivo}")

    if not imagens:
        print("[ERRO] Nenhuma imagem válida encontrada no diretório.")
        return

    lista_imagens = ";".join(imagens)
    mensagem = f"REG {senha} {PORTA_TCP} {lista_imagens}"

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
        resp, _ = client.recvfrom(1024)
        resposta = resp.decode().strip()
        if resposta.startswith("OK"):
            print("[LOG]", resposta)
        else:
            print("[ERRO]", resposta)

def listar_imagens():
    mensagem = "LST"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
        resp, _ = client.recvfrom(4096)
        resposta = resp.decode().strip()

        if resposta.startswith("ERR"):
            print("[ERRO]", resposta)
        else:
            imagens = resposta.split(";")
            for i, img in enumerate(imagens, 1):
                partes = img.split(",")
                md5 = partes[0]
                nome = partes[1]
                clientes_img = partes[2:]
                print(f"{i} - {nome} (MD5: {md5}) - {len(clientes_img)} peers - {clientes_img}")

def atualizar_registro():
    if not PORTA_TCP or not senha_cliente:
        print("[ERRO] É necessário se registrar primeiro.")
        return

    imagens = []
    for arquivo in os.listdir(diretorio):
        caminho = os.path.join(diretorio, arquivo)
        if os.path.isfile(caminho) and imghdr.what(caminho) is not None:
            md5 = calcular_md5(caminho)
            imagens.append(f"{md5},{arquivo}")

    if not imagens:
        print("[ERRO] Nenhuma imagem válida encontrada.")
        return

    lista_imagens = ";".join(imagens)
    mensagem = f"UPD {senha_cliente} {PORTA_TCP} {lista_imagens}"

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
        resp, _ = client.recvfrom(1024)
        resposta = resp.decode().strip()
        if resposta.startswith("OK"):
            print("[LOG]", resposta)
        else:
            print("[ERRO]", resposta)

def fazer_download():
    # Primeiro obter lista de imagens
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto("LST".encode(), (SERVER_IP, SERVER_PORT))
        resp, _ = client.recvfrom(4096)
        resposta = resp.decode().strip()

        if resposta.startswith("ERR"):
            print("[ERRO]", resposta)
            return

        imagens = resposta.split(";")
        if not imagens:
            print("[ERRO] Nenhuma imagem disponível.")
            return

        for i, img in enumerate(imagens, 1):
            partes = img.split(",")
            md5 = partes[0]
            nome = partes[1]
            clientes_img = partes[2:]
            print(f"{i}. {nome} (MD5: {md5}) - Clientes: {clientes_img}")

        escolha = input("Escolha o número da imagem para download: ")
        if not escolha.isdigit():
            print("[ERRO] Escolha inválida.")
            return
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(imagens):
            print("[ERRO] Índice fora do intervalo.")
            return

        partes = imagens[idx].split(",")
        md5 = partes[0]
        nome = partes[1]
        clientes_img = partes[2:]
        if not clientes_img:
            print("[ERRO] Nenhum cliente possui esta imagem.")
            return

        # Baixa do primeiro cliente da lista
        ip_porta = clientes_img[0].split(":")
        ip_down = ip_porta[0]
        porta_down = int(ip_porta[1])
        print(f"[LOG] Iniciando download de {nome} do cliente {ip_down}:{porta_down}...")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client:
            tcp_client.connect((ip_down, porta_down))
            tcp_client.sendall(f"GET {md5}".encode())

            # Verifica se arquivo já existe no diretório
            caminho_download = os.path.join(diretorio, nome)
            if os.path.exists(caminho_download):
                # Se já existe, adiciona um sufixo para evitar sobrescrever
                base, ext = os.path.splitext(nome)
                novo_nome = f"{base}_downloaded{ext}"
                caminho_download = os.path.join(diretorio, novo_nome)
                print(f"[LOG] Arquivo existente encontrado. Salvando como {novo_nome}")

            with open(caminho_download, "wb") as f:
                while True:
                    dados = tcp_client.recv(4096)
                    if not dados:
                        break
                    f.write(dados)

        print("[LOG] Download concluído da porta", porta_down)
def desconectar_cliente():
    if not PORTA_TCP or not senha_cliente:
        print("[ERRO] É necessário se registrar antes de desconectar.")
        return

    mensagem = f"END {senha_cliente} {PORTA_TCP}"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(mensagem.encode(), (SERVER_IP, SERVER_PORT))
        resp, _ = client.recvfrom(1024)
        resposta = resp.decode().strip()
        if resposta.startswith("OK"):
            print("[LOG]", resposta)
        else:
            print("[ERRO]", resposta)

def main():
    while True:
        print("\nMENU:")
        print("1 - Registrar no servidor")
        print("2 - Listar imagens")
        print("3 - Baixar imagens")
        print("4 - Atualizar registro")
        print("5 - Desconectar do servidor (END)")
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
            desconectar_cliente()
        elif opcao == "6":
            print("[LOG] Encerrando cliente.")
            break
        else:
            print("[ERRO] Opção inválida!")

if __name__ == "__main__":
    main()
