import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../cliente')))
import cliente
import json
import socket


def test_calcular_md5(tmp_path):
    """Testa o cálculo do hash MD5."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("conteúdo de teste")
    expected_md5 = "823ba3dcaf66ff6a5a6e57e8e5d6069b"
    assert cliente.calcular_md5(test_file) == expected_md5

def test_registrar_cliente(monkeypatch, tmp_path):
    """Testa o registro de um cliente."""
    # Cria um arquivo temporário para simular imagens
    test_dir = tmp_path / "imagens"
    test_dir.mkdir()
    (test_dir / "imagem1.jpg").write_text("imagem de teste 1")
    (test_dir / "imagem2.jpg").write_text("imagem de teste 2")

    # Mock inputs
    inputs = iter(["123", "13377", str(test_dir)])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    # Mock do socket
    def fake_sendto(data, addr):
        assert json.loads(data.decode())["command"] == "REG"
    monkeypatch.setattr(socket.socket, "sendto", fake_sendto)

    def fake_recvfrom(buffer_size):
        return b'{"status": "OK", "message": "2_REGISTERED_IMAGES"}', None
    monkeypatch.setattr(socket.socket, "recvfrom", fake_recvfrom)

    cliente.registrar_cliente()

def test_listar_imagens(monkeypatch):
    """Testa a listagem de imagens."""
    def fake_recvfrom(buffer_size):
        return b'{"status": "OK", "imagens": ["img1,md5,img2"]}', None
    monkeypatch.setattr(socket.socket, "recvfrom", fake_recvfrom)

    cliente.listar_imagens()

def test_desconectar_cliente(monkeypatch):
    """Testa a desconexão de um cliente."""
    inputs = iter(["123"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    def fake_sendto(data, addr):
        assert json.loads(data.decode())["command"] == "END"
    monkeypatch.setattr(socket.socket, "sendto", fake_sendto)

    def fake_recvfrom(buffer_size):
        return b'{"status": "OK", "message": "CLIENT_DISCONNECTED"}', None
    monkeypatch.setattr(socket.socket, "recvfrom", fake_recvfrom)

    cliente.desconectar_cliente()
