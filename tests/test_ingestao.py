import json
import pytest
from src.ingestao import ler_mensagens_comunidade


def test_ler_json_com_dicionario(tmp_path):
    arquivo = tmp_path / "mensagens.json"
    conteudo = {
        "origem_comunidade": "Discord",
        "periodo_referencia": "Semana_01",
        "interacoes": [
            {"id": "1", "autor": "Ana", "canal": "#geral", "tipo": "feedback", "texto": "Muito bom!"}
        ],
    }
    arquivo.write_text(json.dumps(conteudo), encoding="utf-8")

    resultado = ler_mensagens_comunidade(str(arquivo))

    assert resultado["origem_comunidade"] == "Discord"
    assert len(resultado["interacoes"]) == 1
    assert resultado["interacoes"][0]["texto"] == "Muito bom!"


def test_ler_json_que_eh_so_uma_lista(tmp_path):
    arquivo = tmp_path / "lista.json"
    lista = [
        {"autor": "Carlos", "texto": "Dúvida sobre Python"},
        {"autor": "Bia", "texto": "Consegui rodar o projeto!"},
    ]
    arquivo.write_text(json.dumps(lista), encoding="utf-8")

    resultado = ler_mensagens_comunidade(str(arquivo))

    assert isinstance(resultado, dict)
    assert "interacoes" in resultado
    assert len(resultado["interacoes"]) == 2
    assert resultado["interacoes"][0]["autor"] == "Carlos"


def test_ler_json_sem_lista_em_interacoes_levanta_erro(tmp_path):
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text(json.dumps({"interacoes": "nao_eh_lista"}), encoding="utf-8")

    with pytest.raises(ValueError, match="interacoes"):
        ler_mensagens_comunidade(str(arquivo))


def test_ler_csv_valido(tmp_path):
    arquivo = tmp_path / "mensagens.csv"
    arquivo.write_text(
        "id,autor,canal,tipo,texto\n"
        "CSV_1,João,#duvidas,pergunta_tecnica,Como configurar a chave?\n",
        encoding="utf-8",
    )

    resultado = ler_mensagens_comunidade(str(arquivo))

    assert resultado["origem_comunidade"] == "Discord_CSV_Import"
    assert len(resultado["interacoes"]) == 1
    assert resultado["interacoes"][0]["id"] == "CSV_1"
    assert resultado["interacoes"][0]["autor"] == "João"
    assert resultado["interacoes"][0]["texto"] == "Como configurar a chave?"


def test_ler_csv_sem_coluna_texto_levanta_erro(tmp_path):
    arquivo = tmp_path / "sem_texto.csv"
    arquivo.write_text(
        "id,autor,canal\n"
        "1,Maria,#geral\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="texto"):
        ler_mensagens_comunidade(str(arquivo))


def test_ler_arquivo_inexistente_levanta_erro(tmp_path):
    caminho = tmp_path / "nao_existe.json"

    with pytest.raises(FileNotFoundError):
        ler_mensagens_comunidade(str(caminho))
