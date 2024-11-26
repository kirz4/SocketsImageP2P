import socket
import json
import os
import hashlib

# Endereço do servidor
SERVER_IP = "127.0.0.1"
SERVER_PORT = 13377

def calcular_md5(arquivo):
    """Calcula o hash MD5 de um arquivo."""
    with open(arquivo, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def registrar_cliente():
    """Registra o cliente no servidor."""
    senha = input("Digite uma senha para registro: ")
    porta_tcp = input("Digite a porta TCP para compartilhar arquivos: ")
    diretorio = input("Digite o diretório com imagens: ")

    imagens = []
    for arquivo in os.listdir(diretorio):
        caminho = os.path.join(diretorio, arquivo)
        if os.path.isfile(caminho):
            md5 = calcular_md5(caminho)
            imagens.append(f"{md5},{arquivo}")

    mensagem = {
        "command": "REG",
        "senha": senha,
        "porta": porta_tcp,
        "imagens": imagens
    }

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
        response, _ = client.recvfrom(1024)
        print(json.loads(response.decode()))

def listar_imagens():
    """Lista imagens disponíveis na rede."""
    mensagem = {"command": "LST"}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
        response, _ = client.recvfrom(1024)
        print(json.loads(response.decode()))

def desconectar_cliente():
    """Desconecta o cliente do servidor."""
    senha = input("Digite sua senha para desconexão: ")
    mensagem = {
        "command": "END",
        "senha": senha
    }

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(json.dumps(mensagem).encode(), (SERVER_IP, SERVER_PORT))
        response, _ = client.recvfrom(1024)
        print(json.loads(response.decode()))

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
            print("Opção inválida!")

if __name__ == "__main__":
    main()
