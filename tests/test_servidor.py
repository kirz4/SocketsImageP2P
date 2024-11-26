import servidor
import json

def test_registrar_cliente():
    """Testa o registro de um cliente."""
    mensagem = {
        "command": "REG",
        "senha": "123",
        "porta": "13377",
        "imagens": ["md5,img1.jpg", "md5,img2.jpg"]
    }
    addr = ("127.0.0.1", 50000)

    resposta = servidor.registrar_cliente(mensagem, addr)
    assert resposta == "OK 2_REGISTERED_IMAGES"
    assert len(servidor.clientes) == 1
    assert len(servidor.imagens_compartilhadas) == 2

def test_listar_imagens():
    """Testa a listagem de imagens."""
    servidor.imagens_compartilhadas = {
        "md5": {"nome": "img1.jpg", "clientes": ["127.0.0.1:13377"]}
    }
    resposta = servidor.listar_imagens()
    assert "img1.jpg" in resposta

def test_desconectar_cliente():
    """Testa a desconexão de um cliente."""
    servidor.clientes = [{"ip": "127.0.0.1", "porta": "13377", "senha": "123"}]
    mensagem = {
        "command": "END",
        "senha": "123",
        "porta": "13377"
    }
    addr = ("127.0.0.1", 50000)

    resposta = servidor.desconectar_cliente(mensagem, addr)
    assert resposta == "OK CLIENT_DISCONNECTED"
    assert len(servidor.clientes) == 0
