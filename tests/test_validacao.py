from src.esquema import BUCKET_OCI
from src.validacao import validar_e_tratar_json


def _dados_limpos_exemplo():
    return {
        "origem_comunidade": "Discord_ONE",
        "periodo_referencia": "Semana 04",
        "interacoes": [
            {"id": "MSG_001", "autor": "Ana", "canal": "#conquistas", "tipo": "depoimento", "texto": "Consegui vaga!"},
            {"id": "MSG_002", "autor": "Beto", "canal": "#duvidas", "tipo": "pergunta_tecnica", "texto": "Erro no OCI"},
        ],
    }


def _resposta_llm_valida():
    return {
        "resumo_comunidade": {
            "sentimento_predominante": "Positivo",
            "topicos_principais": ["Carreira", "OCI"],
        },
        "analise_interacoes": [
            {
                "id": "MSG_001",
                "tipo": "depoimento",
                "sentimento": "Muito positivo",
                "topicos": ["Carreira"],
                "ativos_recomendados": ["post_linkedin", "case_sucesso"],
                "relevancia": "Alta",
            },
            {
                "id": "MSG_002",
                "tipo": "pergunta_tecnica",
                "sentimento": "Negativo",
                "topicos": ["OCI"],
                "ativos_recomendados": ["faq"],
                "relevancia": "Média",
            },
        ],
        "ativos_distribuicao_gerados": {
            "post_linkedin": {
                "titulo": "Conquista na comunidade",
                "copy": "Parabéns pela nova vaga!",
                "canal_recomendado": "LinkedIn Oficial",
                "potencial_engajamento": "Alto",
            },
            "destaque_newsletter_semanal": {
                "secao": "Destaques",
                "chamada": "Novidades da semana",
                "resumo": "Muitas conquistas e dúvidas técnicas resolvidas.",
            },
            "sugestao_conteudo_faq": {
                "tema": "Configuração OCI",
                "pergunta": "Como resolver erro no OCI?",
                "origem": "Dúvida do Beto",
                "status": "encaminhado_para_mentoria",
            },
            "case_sucesso": {
                "titulo": "De aluna a dev",
                "desafio": "Conseguir primeira oportunidade",
                "solucao": "Projetos práticos na comunidade",
                "resultado": "Aprovação em vaga",
                "interacoes_origem": ["MSG_001"],
            },
        },
    }


def test_validacao_com_resposta_boa_retorna_sucesso():
    dados_limpos = _dados_limpos_exemplo()
    resposta_llm = _resposta_llm_valida()

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    assert resultado["status"] == "sucesso"
    assert resultado["avisos"] == []
    assert resultado["resumo_comunidade"]["total_interacoes_processadas"] == 2
    assert resultado["armazenamento_oci"] == {
        "bucket": BUCKET_OCI,
        "caminho_objeto": "ativos/semana-04/pacote-distribuicao.json",
        "status": "pendente_upload",
    }


def test_validacao_valores_fora_da_escala_gera_aviso_e_none():
    dados_limpos = {"interacoes": [{"id": "MSG_001", "texto": "Oi"}]}
    resposta_llm = _resposta_llm_valida()
    resposta_llm["resumo_comunidade"]["sentimento_predominante"] = "Empolgado"
    resposta_llm["analise_interacoes"] = [
        {
            "id": "MSG_001",
            "tipo": "fofoca",
            "sentimento": "Super Feliz",
            "topicos": ["Geral"],
            "ativos_recomendados": ["post_linkedin"],
            "relevancia": "Urgente",
        }
    ]

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    analise = resultado["analise_interacoes"][0]
    assert resultado["status"] == "parcial"
    assert resultado["resumo_comunidade"]["sentimento_predominante"] is None
    assert analise["tipo"] is None
    assert analise["sentimento"] is None
    assert analise["relevancia"] is None
    assert any("sentimento_predominante fora da escala" in a for a in resultado["avisos"])
    assert any("tipo fora da lista" in a for a in resultado["avisos"])
    assert any("sentimento fora da escala" in a for a in resultado["avisos"])
    assert any("relevancia fora da lista" in a for a in resultado["avisos"])


def test_validacao_aceita_sem_acento_e_maiusculas():
    dados_limpos = {"interacoes": [{"id": "MSG_001", "texto": "Oi"}]}
    resposta_llm = _resposta_llm_valida()
    resposta_llm["resumo_comunidade"]["sentimento_predominante"] = "MUITO POSITIVO"
    resposta_llm["analise_interacoes"] = [
        {
            "id": "MSG_001",
            "tipo": "PERGUNTA TECNICA",
            "sentimento": "muito positivo",
            "topicos": ["IA"],
            "ativos_recomendados": ["sugestao_conteudo_faq"],
            "relevancia": "media",
        }
    ]

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    analise = resultado["analise_interacoes"][0]
    assert resultado["resumo_comunidade"]["sentimento_predominante"] == "Muito positivo"
    assert analise["tipo"] == "pergunta_tecnica"
    assert analise["sentimento"] == "Muito positivo"
    assert analise["relevancia"] == "Média"
    assert analise["ativos_recomendados"] == ["faq"]


def test_validacao_id_desconhecido_descartado_e_interacao_sem_analise():
    dados_limpos = _dados_limpos_exemplo()
    resposta_llm = _resposta_llm_valida()
    resposta_llm["analise_interacoes"] = [
        {
            "id": "ID_INVENTADO",
            "tipo": "depoimento",
            "sentimento": "Positivo",
            "topicos": [],
            "ativos_recomendados": [],
            "relevancia": "Alta",
        },
        resposta_llm["analise_interacoes"][0],  # Apenas MSG_001 presente; MSG_002 faltando
    ]

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    ids_analisados = [a["id"] for a in resultado["analise_interacoes"]]
    assert ids_analisados == ["MSG_001"]
    assert any("id desconhecido descartada: ID_INVENTADO" in a for a in resultado["avisos"])
    assert any("MSG_002: interação sem análise" in a for a in resultado["avisos"])


def test_validacao_ativo_null_sem_aviso_e_ativo_ausente_com_aviso():
    dados_limpos = _dados_limpos_exemplo()
    resposta_llm = _resposta_llm_valida()
    resposta_llm["ativos_distribuicao_gerados"]["case_sucesso"] = None
    del resposta_llm["ativos_distribuicao_gerados"]["sugestao_conteudo_faq"]

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    assert resultado["ativos_distribuicao_gerados"]["case_sucesso"] is None
    assert resultado["ativos_distribuicao_gerados"]["sugestao_conteudo_faq"] is None
    assert not any("case_sucesso" in a for a in resultado["avisos"])
    assert "ativo ausente: sugestao_conteudo_faq" in resultado["avisos"]


def test_validacao_case_sucesso_com_id_desconhecido():
    dados_limpos = _dados_limpos_exemplo()
    resposta_llm = _resposta_llm_valida()
    resposta_llm["ativos_distribuicao_gerados"]["case_sucesso"]["interacoes_origem"] = [
        "MSG_001",
        "MSG_999",
    ]

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    case = resultado["ativos_distribuicao_gerados"]["case_sucesso"]
    assert case["interacoes_origem"] == ["MSG_001"]
    assert any("case_sucesso cita ids desconhecidos: MSG_999" in a for a in resultado["avisos"])


def test_validacao_subobjetos_null_nao_quebram():
    dados_limpos = _dados_limpos_exemplo()
    resposta_llm = {
        "resumo_comunidade": None,
        "analise_interacoes": None,
        "ativos_distribuicao_gerados": None,
    }

    resultado = validar_e_tratar_json(resposta_llm, dados_limpos)

    assert resultado["status"] == "erro"
    assert resultado["resumo_comunidade"]["sentimento_predominante"] is None
    assert resultado["analise_interacoes"] == []
    assert all(v is None for v in resultado["ativos_distribuicao_gerados"].values())


def test_validacao_resposta_vazia_retorna_status_erro():
    dados_limpos = _dados_limpos_exemplo()

    resultado = validar_e_tratar_json({}, dados_limpos)

    assert resultado["status"] == "erro"
    assert "resposta da LLM vazia ou não é um objeto JSON" in resultado["avisos"]
    assert resultado["resumo_comunidade"]["total_interacoes_processadas"] == 2


def test_validacao_listas_malformadas_geram_aviso():
    resposta_llm = _resposta_llm_valida()
    resposta_llm["resumo_comunidade"]["topicos_principais"] = None
    resposta_llm["analise_interacoes"][0]["topicos"] = 42
    resposta_llm["analise_interacoes"][1]["ativos_recomendados"] = "faq"

    resultado = validar_e_tratar_json(resposta_llm, _dados_limpos_exemplo())

    assert resultado["status"] == "parcial"
    assert any("topicos_principais" in aviso for aviso in resultado["avisos"])
    assert any("MSG_001: topicos" in aviso for aviso in resultado["avisos"])
    assert any("MSG_002: ativos_recomendados" in aviso for aviso in resultado["avisos"])


def test_validacao_ativos_recomendados_vazio_e_valido():
    resposta_llm = _resposta_llm_valida()
    resposta_llm["analise_interacoes"][1]["ativos_recomendados"] = []

    resultado = validar_e_tratar_json(resposta_llm, _dados_limpos_exemplo())

    assert resultado["status"] == "sucesso"


def test_validacao_estruturas_vazias_sao_erro():
    dados_limpos = _dados_limpos_exemplo()

    so_post_vazio = validar_e_tratar_json({"ativos_distribuicao_gerados": {"post_linkedin": {}}}, dados_limpos)
    so_ids = validar_e_tratar_json({"analise_interacoes": [{"id": "MSG_001"}]}, dados_limpos)

    assert so_post_vazio["status"] == "erro"
    assert so_ids["status"] == "erro"


def test_validacao_case_sem_origem_gera_aviso():
    resposta_llm = _resposta_llm_valida()
    del resposta_llm["ativos_distribuicao_gerados"]["case_sucesso"]["interacoes_origem"]

    resultado = validar_e_tratar_json(resposta_llm, _dados_limpos_exemplo())

    assert resultado["status"] == "parcial"
    assert any("interacoes_origem" in aviso for aviso in resultado["avisos"])
