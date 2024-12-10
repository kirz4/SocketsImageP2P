import socket
import json
import threading

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
        senha = data["senha"]
        porta = int(data["porta"])
        imagens = data["imagens"]

        # Validações iniciais
        if not senha or not porta or not imagens:
            print("[ERRO] Dados incompletos no registro.")
            return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

        # Valida o formato das imagens
        imagens_validas = []
        for imagem in imagens:
            if "," not in imagem:
                print(f"[ERRO] Formato inválido para a imagem: {imagem}")
                return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}
            md5, nome = imagem.split(",", 1)
            if len(md5) != 32:  # Validação básica para hash MD5
                print(f"[ERRO] Hash MD5 inválido para a imagem: {imagem}")
                return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}
            imagens_validas.append((md5, nome))

        # Adiciona o cliente à lista
        cliente = {"ip": addr[0], "porta": porta, "senha": senha}
        clientes.append(cliente)
        print(f"[LOG] Cliente registrado: {cliente}")

        # Adiciona as imagens à lista compartilhada
        for md5, nome in imagens_validas:
            if md5 not in imagens_compartilhadas:
                imagens_compartilhadas[md5] = {"nome": nome, "clientes": []}
            imagens_compartilhadas[md5]["clientes"].append(f"{addr[0]}:{porta}")

        print(f"[LOG] Imagens compartilhadas atualizadas: {imagens_compartilhadas}")

        # Retorna a resposta no formato esperado
        return {"status": "OK", "message": f"{len(imagens_validas)}_REGISTERED_IMAGES"}
    except Exception as e:
        print(f"[ERRO] Erro ao registrar cliente: {e}")
        return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

    
def listar_imagens():
    """Retorna a lista de imagens compartilhadas."""
    print("[LOG] Listando imagens disponíveis...")
    imagens_lista = [
        f"{md5},{info['nome']},{','.join(info['clientes'])}" 
        for md5, info in imagens_compartilhadas.items()
    ]
    if not imagens_lista:
        return {"status": "ERR", "message": "NO_IMAGES_AVAILABLE"}
    return {"status": "OK", "imagens": imagens_lista}


def handle_client(conn, addr):
    """Lida com a conexão de um cliente para envio de imagens."""
    try:
        print(f"[LOG] Conexão recebida de {addr}")
        dados = conn.recv(1024).decode()

        if dados.startswith("GET"):
            _, md5 = dados.split()
            if md5 in imagens_compartilhadas:
                caminho_imagem = imagens_compartilhadas[md5]["nome"]
                with open(caminho_imagem, "rb") as f:
                    while chunk := f.read(4096):
                        conn.sendall(chunk)
                print(f"[LOG] Imagem {caminho_imagem} enviada para {addr}")
            else:
                print("[ERRO] Imagem não encontrada.")
        else:
            print("[ERRO] Comando inválido recebido.")
    except Exception as e:
        print(f"[ERRO] Erro ao enviar imagem: {e}")
    finally:
        conn.close()


def start_tcp_server(port):
    """Inicia o servidor TCP para envio de imagens."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_server:
        tcp_server.bind((SERVER_IP, port))
        tcp_server.listen(5)
        print(f"[LOG] Servidor TCP rodando na porta {port}...")

        while True:
            conn, addr = tcp_server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

def atualizar_registro(data, addr):
    """Atualiza o registro de um cliente no servidor."""
    try:
        porta = data.get("porta")
        imagens = data.get("imagens", [])

        if not porta or not imagens:
            print("[ERRO] Dados incompletos para atualização de registro.")
            return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

        # Atualiza ou adiciona as imagens na lista compartilhada
        for imagem in imagens:
            if "," not in imagem:
                print(f"[ERRO] Formato inválido para imagem: {imagem}")
                return {"status": "ERR", "message": "INVALID_IMAGE_FORMAT"}

            md5, nome = imagem.split(",", 1)
            if md5 not in imagens_compartilhadas:
                imagens_compartilhadas[md5] = {"nome": nome, "clientes": []}
            if f"{addr[0]}:{porta}" not in imagens_compartilhadas[md5]["clientes"]:
                imagens_compartilhadas[md5]["clientes"].append(f"{addr[0]}:{porta}")

        print(f"[LOG] Registro atualizado para cliente {addr[0]}:{porta}")
        return {"status": "OK", "message": "UPDATED"}
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar registro: {e}")
        return {"status": "ERR", "message": "UPDATE_FAILED"}

def remover_registro(data, addr):
    """Remove o registro de um cliente no servidor."""
    try:
        porta = data.get("porta")

        if not porta:
            print("[ERRO] Dados incompletos para remoção de registro.")
            return {"status": "ERR", "message": "INVALID_MESSAGE_FORMAT"}

        # Remove o cliente da lista de clientes
        cliente = next((c for c in clientes if c["ip"] == addr[0] and c["porta"] == int(porta)), None)
        if not cliente:
            print("[ERRO] Cliente não encontrado.")
            return {"status": "ERR", "message": "CLIENT_NOT_FOUND"}

        clientes.remove(cliente)

        # Remove as imagens associadas ao cliente
        for md5, info in list(imagens_compartilhadas.items()):
            if f"{addr[0]}:{porta}" in info["clientes"]:
                info["clientes"].remove(f"{addr[0]}:{porta}")
                if not info["clientes"]:  # Remove a imagem se nenhum cliente a compartilha mais
                    del imagens_compartilhadas[md5]

        print(f"[LOG] Registro removido para cliente {addr[0]}:{porta}")
        return {"status": "OK", "message": "REMOVED"}
    except Exception as e:
        print(f"[ERRO] Erro ao remover registro: {e}")
        return {"status": "ERR", "message": "REMOVE_FAILED"}


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
                    data_decoded = data.decode().strip()  # Decodifica e remove espaços extras
                    print(f"[LOG] Mensagem recebida: {data_decoded}")

                    if data_decoded.startswith("REG"):
                        # Separar os parâmetros da mensagem REG
                        partes = data_decoded.split(" ", 3)
                        if len(partes) != 4:
                            raise ValueError("Formato inválido para REG")
                        senha, porta, imagens = partes[1], partes[2], partes[3]
                        imagens_lista = imagens.split(";")  # Divide as imagens no formato MD5,NOME
                        # Processa o registro do cliente
                        resposta = registrar_cliente({"senha": senha, "porta": porta, "imagens": imagens_lista}, addr)

                    elif data_decoded == "LST":
                        # Comando para listar imagens
                        resposta = listar_imagens()

                    elif data_decoded.startswith("UPD"):
                        # Separar os parâmetros da mensagem UPD
                        partes = data_decoded.split(" ", 2)
                        if len(partes) != 3:
                            raise ValueError("Formato inválido para UPD")
                        porta, imagens = partes[1], partes[2]
                        imagens_lista = imagens.split(";")
                        resposta = atualizar_registro({"porta": porta, "imagens": imagens_lista}, addr)

                    elif data_decoded.startswith("DEL"):
                        # Separar os parâmetros da mensagem DEL
                        partes = data_decoded.split(" ", 1)
                        if len(partes) != 2:
                            raise ValueError("Formato inválido para DEL")
                        porta = partes[1]
                        resposta = remover_registro({"porta": porta}, addr)

                    elif data_decoded.startswith("END"):
                        # Separar os parâmetros da mensagem END
                        partes = data_decoded.split(" ", 2)
                        if len(partes) != 3:
                            raise ValueError("Formato inválido para END")
                        senha, porta = partes[1], partes[2]
                        resposta = desconectar_cliente({"senha": senha, "porta": porta}, addr)

                    else:
                        # Comando inválido
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
