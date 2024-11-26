import os
import hashlib
import socket
import json

# Configuração do servidor
SERVER_IP = "127.0.0.1"
SERVER_PORT = 13377

def calcular_md5(arquivo):
    """Calcula o hash MD5 de um arquivo."""
    print(f"[LOG] Calculando o hash MD5 do arquivo: {arquivo}")
    with open(arquivo, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
        print(f"[LOG] Hash MD5 calculado para {arquivo}: {md5}")
        return md5

def registrar_cliente():
    """Registra o cliente no servidor."""
    try:
        print("[LOG] Iniciando registro do cliente...")
        senha = input("Digite uma senha para registro: ")
        porta_tcp = input("Digite a porta TCP para compartilhar arquivos: ")
        diretorio = input("Digite o diretório com imagens: ")

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

def desconectar_cliente():
    """Desconecta o cliente do servidor."""
    try:
        print("[LOG] Solicitando desconexão do servidor...")
        senha = input("Digite sua senha para desconexão: ")
        mensagem = {
            "command": "END",
            "senha": senha
        }

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
            response, _ = client.recvfrom(1024)
            print(f"[LOG] Resposta do servidor: {response.decode()}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante a desconexão: {e}")

def main():
    """Menu principal do cliente."""
    while True:
        print("\n1. Registrar cliente")
        print("2. Listar imagens disponíveis")
        print("3. Desconectar cliente")
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            registrar_cliente()
        elif opcao == "2":
            listar_imagens()
        elif opcao == "3":
            desconectar_cliente()
            break
        else:
            print("[ERRO] Opção inválida!")

if __name__ == "__main__":
    main()
