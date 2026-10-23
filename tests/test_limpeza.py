from src.limpeza import limpar_dados_comunidade, limpar_texto


def test_limpar_texto_remove_espacos_e_quebras():
    texto_sujo = "   Olá,   pessoal!\n\nComo   vocês estão?   "
    assert limpar_texto(texto_sujo) == "Olá, pessoal! Como vocês estão?"


def test_limpeza_mantem_id_existente_e_gera_msg_quando_falta():
    dados_brutos = {
        "interacoes": [
            {"id": "DEMO_01", "autor": "Ana", "texto": "Passei na entrevista!"},
            {"autor": "Bruno", "texto": "Mensagem sem id definido."},
        ]
    }

    resultado = limpar_dados_comunidade(dados_brutos)

    assert len(resultado["interacoes"]) == 2
    assert resultado["interacoes"][0]["id"] == "DEMO_01"
    assert resultado["interacoes"][1]["id"] == "MSG_002"


def test_limpeza_torna_ids_duplicados_unicos():
    dados_brutos = {
        "interacoes": [
            {"id": "REP_1", "texto": "Primeira mensagem"},
            {"id": "REP_1", "texto": "Segunda mensagem com mesmo id"},
        ]
    }

    resultado = limpar_dados_comunidade(dados_brutos)

    ids = [item["id"] for item in resultado["interacoes"]]
    assert ids == ["REP_1", "REP_1_2"]


def test_limpeza_descarta_texto_vazio_e_itens_que_nao_sao_dict():
    dados_brutos = {
        "interacoes": [
            "item_invalido_string",
            123,
            None,
            {"id": "1", "texto": "   \n  "},
            {"id": "2", "texto": ""},
            {"id": "3", "texto": "Texto válido!"},
        ]
    }

    resultado = limpar_dados_comunidade(dados_brutos)

    assert resultado["total_interacoes_validas"] == 1
    assert len(resultado["interacoes"]) == 1
    assert resultado["interacoes"][0]["id"] == "3"


def test_limpeza_com_interacoes_none():
    dados_brutos = {"origem_comunidade": "Discord", "interacoes": None}

    resultado = limpar_dados_comunidade(dados_brutos)

    assert resultado["interacoes"] == []
    assert resultado["total_interacoes_validas"] == 0


def test_limpeza_id_gerado_nao_colide_com_id_existente():
    dados_brutos = {
        "interacoes": [
            {"id": "A", "texto": "Primeira"},
            {"id": "A_3", "texto": "Segunda"},
            {"id": "A", "texto": "Terceira, repete o id A na posição 3"},
        ]
    }

    resultado = limpar_dados_comunidade(dados_brutos)

    ids = [item["id"] for item in resultado["interacoes"]]
    assert len(set(ids)) == 3
