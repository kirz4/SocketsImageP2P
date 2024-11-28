import os
import hashlib
import socket
import json

# Configuração do servidor
SERVER_IP = "127.0.0.1"
SERVER_PORT = 13377

# Porta TCP do cliente
PORTA_TCP = None

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
    try:
        print("[LOG] Iniciando registro do cliente...")
        senha = input("Digite uma senha para registro: ")
        porta_tcp = input("Digite a porta TCP para compartilhar arquivos: ")
        diretorio = input("Digite o diretório com imagens: ")

        # Salva a porta TCP globalmente
        PORTA_TCP = porta_tcp

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
        mensagem = {
            "command": "REG",
            "senha": senha,
            "porta": porta_tcp,
            "imagens": imagens
        }

        print(f"[LOG] Enviando mensagem de registro para o servidor: {mensagem}")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            print(f"[LOG] Resposta do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante o registro do cliente: {e}")

def listar_imagens():
    """Lista imagens disponíveis na rede."""
    try:
        print("[LOG] Solicitando lista de imagens ao servidor...")
        mensagem = {"command": "LST"}

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            print(f"[LOG] Resposta do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao listar imagens: {e}")

def fazer_download():
    """Realiza o download de uma imagem."""
    try:
        print("[LOG] Solicitando lista de imagens para download...")
        mensagem = {"command": "LST"}  # Envia o comando LST para o servidor

        # Solicita a lista de imagens do servidor
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(4096)
            resposta_servidor = json.loads(response.decode())

            if resposta_servidor.get("status") != "OK":
                print("[ERRO] Não foi possível obter a lista de imagens.")
                return

            lista_imagens = resposta_servidor.get("imagens", [])
            if not lista_imagens:
                print("[ERRO] Nenhuma imagem disponível na rede.")
                return

            print("[LOG] Imagens disponíveis para download:")
            for idx, imagem in enumerate(lista_imagens):
                md5, nome, *clientes = imagem.split(",")
                print(f"{idx + 1}. {nome} - MD5: {md5} - Clientes: {', '.join(clientes)}")

            # Solicita ao usuário o índice da imagem para download
            escolha = int(input("Escolha o número da imagem para download: ")) - 1
            if escolha < 0 or escolha >= len(lista_imagens):
                print("[ERRO] Escolha inválida.")
                return

            imagem_escolhida = lista_imagens[escolha]
            md5, nome, *clientes = imagem_escolhida.split(",")

            # Seleciona o primeiro cliente da lista para realizar o download
            ip_porta = clientes[0].split(":")
            ip = ip_porta[0]
            porta = int(ip_porta[1])

            print(f"[LOG] Iniciando download de {nome} do cliente {ip}:{porta}...")

            # Realiza a conexão TCP para baixar a imagem
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
            "senha": senha,
            "porta": PORTA_TCP  # Envia a porta TCP registrada
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
        print("\n1. Registrar cliente")
        print("2. Listar imagens disponíveis")
        print("3. Fazer download de imagem")
        print("4. Desconectar cliente")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            registrar_cliente()
        elif opcao == "2":
            listar_imagens()
        elif opcao == "3":
            fazer_download()
        elif opcao == "4":
            desconectar_cliente()
            break
        else:
            print("[ERRO] Opção inválida!")

if __name__ == "__main__":
    main()
