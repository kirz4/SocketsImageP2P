import socket
import json
from threading import Lock

# Porta padrão para o servidor
SERVER_PORT = 13377
# Estrutura de dados para armazenar clientes e imagens
clientes = {}
imagens = {}
lock = Lock()

def handle_message(data, addr):
    """Processa a mensagem recebida pelo servidor."""
    global clientes, imagens

    try:
        message = json.loads(data.decode())
        command = message.get("command")
        
        if command == "REG":
            senha = message["senha"]
            porta = message["porta"]
            imagens_cliente = message["imagens"]

            with lock:
                clientes[addr] = {"senha": senha, "porta": porta, "imagens": imagens_cliente}
                for imagem in imagens_cliente:
                    md5, nome = imagem.split(",")
                    if md5 not in imagens:
                        imagens[md5] = {"nome": nome, "clientes": []}
                    imagens[md5]["clientes"].append(addr)

            return json.dumps({"status": "OK", "message": f"{len(imagens_cliente)}_REGISTERED_IMAGES"}).encode()

        elif command == "LST":
            lista_imagens = []
            with lock:
                for md5, dados in imagens.items():
                    clientes_list = [f"{c[0]}:{clientes[c]['porta']}" for c in dados["clientes"]]
                    lista_imagens.append(f"{md5},{dados['nome']},{','.join(clientes_list)}")
            return json.dumps({"status": "OK", "imagens": lista_imagens}).encode()

        elif command == "END":
            senha = message["senha"]
            with lock:
                if addr in clientes and clientes[addr]["senha"] == senha:
                    del clientes[addr]
                    for imagem in list(imagens.keys()):
                        imagens[imagem]["clientes"] = [
                            c for c in imagens[imagem]["clientes"] if c != addr
                        ]
                        if not imagens[imagem]["clientes"]:
                            del imagens[imagem]
                    return json.dumps({"status": "OK", "message": "CLIENT_FINISHED"}).encode()
                else:
                    return json.dumps({"status": "ERR", "message": "INVALID_PASSWORD"}).encode()

        else:
            return json.dumps({"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}).encode()

    except Exception as e:
        return json.dumps({"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}).encode()

def main():
    """Inicializa o servidor."""
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("0.0.0.0", SERVER_PORT))
    print(f"Servidor rodando na porta {SERVER_PORT}...")

    while True:
        data, addr = server.recvfrom(1024)
        response = handle_message(data, addr)
        server.sendto(response, addr)

if __name__ == "__main__":
    main()
