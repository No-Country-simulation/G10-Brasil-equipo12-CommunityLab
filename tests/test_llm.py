import io
import json
import urllib.error

import pytest

from src import llm


@pytest.fixture
def requisicoes(monkeypatch):
    """Troca a chamada HTTP por uma falsa e guarda as requisições feitas."""
    feitas = []

    def urlopen_falso(requisicao, timeout):
        feitas.append(requisicao)
        if "/api/chat" in requisicao.full_url:
            corpo = {"message": {"content": '{"ok": true}'}}
        else:
            corpo = {"choices": [{"message": {"content": '{"ok": true}'}}]}
        return io.BytesIO(json.dumps(corpo).encode("utf-8"))

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen_falso)
    for variavel in ("LLM_PROVIDER", "NVIDIA_API_KEY", "NVIDIA_MODEL", "NVIDIA_URL", "OLLAMA_MODEL", "OLLAMA_URL"):
        monkeypatch.delenv(variavel, raising=False)
    return feitas


def test_nvidia_envia_requisicao_no_formato_openai(requisicoes, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-teste")

    resposta = llm.chamar_llm("sistema", "usuario")

    assert resposta == '{"ok": true}'
    requisicao = requisicoes[0]
    assert requisicao.full_url == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert requisicao.get_header("Authorization") == "Bearer nvapi-teste"
    corpo = json.loads(requisicao.data)
    assert corpo["model"] == llm.MODELO_NVIDIA_PADRAO
    assert corpo["response_format"] == {"type": "json_object"}
    assert corpo["messages"][0] == {"role": "system", "content": "sistema"}


def test_nvidia_usa_modelo_e_url_do_env(requisicoes, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-teste")
    monkeypatch.setenv("NVIDIA_MODEL", "nvidia/outro-modelo")
    monkeypatch.setenv("NVIDIA_URL", "http://localhost:8000/v1/")

    llm.chamar_llm("sistema", "usuario")

    assert requisicoes[0].full_url == "http://localhost:8000/v1/chat/completions"
    assert json.loads(requisicoes[0].data)["model"] == "nvidia/outro-modelo"


def test_nvidia_sem_chave_levanta_erro(requisicoes, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")

    with pytest.raises(RuntimeError, match="NVIDIA_API_KEY"):
        llm.chamar_llm("sistema", "usuario")
    assert requisicoes == []


def test_erro_http_inclui_o_motivo(monkeypatch):
    def urlopen_com_erro(requisicao, timeout):
        raise urllib.error.HTTPError(
            requisicao.full_url, 404, "Not Found", None, io.BytesIO(b'{"detail": "modelo inexistente"}')
        )

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen_com_erro)
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-teste")

    with pytest.raises(RuntimeError, match="404.*modelo inexistente"):
        llm.chamar_llm("sistema", "usuario")


def test_ollama_usa_modelo_local(requisicoes, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "modelo-local")

    assert llm.chamar_llm("sistema", "usuario") == '{"ok": true}'
    corpo = json.loads(requisicoes[0].data)
    assert requisicoes[0].full_url == "http://127.0.0.1:11434/api/chat"
    assert corpo["model"] == "modelo-local"
    assert corpo["format"] == "json"


def test_provedor_desconhecido_levanta_erro(requisicoes, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "outro")

    with pytest.raises(ValueError, match="LLM_PROVIDER desconhecido"):
        llm.chamar_llm("sistema", "usuario")


def test_erro_http_mascara_a_chave_e_le_so_o_comeco(monkeypatch):
    lidos = []

    class CorpoGrande(io.BytesIO):
        def read(self, tamanho=-1):
            lidos.append(tamanho)
            return super().read(tamanho)

    def urlopen_com_erro(requisicao, timeout):
        corpo = CorpoGrande(b'{"detail": "Invalid API key: nvapi-secreta"}' + b" " * 1_000_000)
        raise urllib.error.HTTPError(requisicao.full_url, 401, "Unauthorized", None, corpo)

    monkeypatch.setattr(llm.urllib.request, "urlopen", urlopen_com_erro)
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-secreta")

    with pytest.raises(RuntimeError) as erro:
        llm.chamar_llm("sistema", "usuario")

    assert "nvapi-secreta" not in str(erro.value)
    assert "Invalid API key: ***" in str(erro.value)
    assert lidos and all(0 < tamanho <= 2000 for tamanho in lidos)
