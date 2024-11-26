import socket
import json

# Configuração do servidor
SERVER_IP = "127.0.0.1"
SERVER_PORT = 13377

# Lista de clientes registrados
clientes = []

# Lista de imagens compartilhadas
imagens_compartilhadas = {}

def registrar_cliente(data, addr):
    """Registra um cliente no servidor."""
    try:
        print(f"[LOG] Dados recebidos para registro: {data}")
        senha = data.get("senha")
        porta = data.get("porta")
        imagens = data.get("imagens", [])

        if not senha or not porta or not imagens:
            print("[ERRO] Dados incompletos no registro.")
            return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

        # Adiciona o cliente à lista
        clientes.append({"ip": addr[0], "porta": porta, "senha": senha})
        print(f"[LOG] Cliente registrado: {clientes[-1]}")

        # Adiciona as imagens à lista compartilhada
        for imagem in imagens:
            md5, nome = imagem.split(",")
            if md5 not in imagens_compartilhadas:
                imagens_compartilhadas[md5] = {"nome": nome, "clientes": []}
            imagens_compartilhadas[md5]["clientes"].append(f"{addr[0]}:{porta}")

        print(f"[LOG] Imagens compartilhadas atualizadas: {imagens_compartilhadas}")
        return {"status": "OK", "message": f"{len(imagens)}_REGISTERED_IMAGES"}
    except Exception as e:
        print(f"[ERRO] Erro ao registrar cliente: {e}")
        return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

def listar_imagens():
    """Retorna a lista de imagens compartilhadas."""
    print("[LOG] Listando imagens disponíveis...")
    return {"status": "OK", "imagens": [
        f"{md5},{info['nome']},{','.join(info['clientes'])}" for md5, info in imagens_compartilhadas.items()
    ]}

def desconectar_cliente(data, addr):
    """Desconecta um cliente do servidor."""
    try:
        print(f"[LOG] Dados recebidos para desconexão: {data}")
        senha = data.get("senha")
        porta = data.get("porta")

        if not senha or not porta:
            print("[ERRO] Dados incompletos na solicitação de desconexão.")
            return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

        # Localiza o cliente na lista
        cliente = next((c for c in clientes if c["ip"] == addr[0] and c["porta"] == porta), None)
        if not cliente:
            print("[ERRO] Cliente não encontrado.")
            return {"status": "ERR", "message": "CLIENT_NOT_FOUND"}

        # Verifica a senha
        if cliente["senha"] != senha:
            print("[ERRO] Senha inválida fornecida para desconexão.")
            return {"status": "ERR", "message": "INVALID_PASSWORD"}

        # Remove o cliente da lista
        clientes.remove(cliente)

        # Remove as imagens associadas ao cliente
        for md5, info in list(imagens_compartilhadas.items()):
            info["clientes"] = [c for c in info["clientes"] if c != f"{addr[0]}:{porta}"]
            if not info["clientes"]:
                del imagens_compartilhadas[md5]

        print(f"[LOG] Cliente desconectado: {cliente}")
        return {"status": "OK", "message": "CLIENT_DISCONNECTED"}
    except Exception as e:
        print(f"[ERRO] Erro ao desconectar cliente: {e}")
        return {"status": "ERR", "message": "INTERNAL_SERVER_ERROR"}

def main():
    """Inicia o servidor."""
    try:
        print("[LOG] Iniciando servidor...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind((SERVER_IP, SERVER_PORT))
            print(f"[LOG] Servidor rodando na porta {SERVER_PORT}...")

            while True:
                print("[LOG] Aguardando mensagens...")
                data, addr = server.recvfrom(4096)  # Aumentar buffer para 4096 bytes
                print(f"[LOG] Mensagem recebida de {addr}: {data.decode()}")

                try:
                    mensagem = json.loads(data.decode())
                    command = mensagem.get("command")

                    if command == "REG":
                        resposta = registrar_cliente(mensagem, addr)
                    elif command == "LST":
                        resposta = listar_imagens()
                    elif command == "END":
                        resposta = desconectar_cliente(mensagem, addr)
                    else:
                        resposta = {"status": "ERR", "message": "INVALID_COMMAND"}
                except Exception as e:
                    print(f"[ERRO] Erro ao processar mensagem: {e}")
                    resposta = {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

                print(f"[LOG] Enviando resposta para {addr}: {resposta}")
                server.sendto(json.dumps(resposta).encode(), addr)
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro no servidor: {e}")

if __name__ == "__main__":
    main()
