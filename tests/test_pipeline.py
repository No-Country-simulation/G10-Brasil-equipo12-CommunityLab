import json
from src.pipeline import executar_pipeline


def _dados_entrada_validos():
    return {
        "origem_comunidade": "Discord",
        "periodo_referencia": "Semana_04",
        "interacoes": [
            {
                "id": "MSG_001",
                "autor": "Mariana",
                "canal": "#conquistas",
                "tipo": "depoimento",
                "texto": "Consegui minha primeira vaga em IA!",
            }
        ],
    }


def _json_llm_bom():
    return json.dumps({
        "resumo_comunidade": {
            "sentimento_predominante": "Muito positivo",
            "topicos_principais": ["Carreira", "IA"],
        },
        "analise_interacoes": [
            {
                "id": "MSG_001",
                "tipo": "depoimento",
                "sentimento": "Muito positivo",
                "topicos": ["Carreira", "IA"],
                "ativos_recomendados": ["post_linkedin"],
                "relevancia": "Alta",
            }
        ],
        "ativos_distribuicao_gerados": {
            "post_linkedin": {
                "titulo": "Nova conquista na comunidade",
                "copy": "Mariana conquistou sua vaga em IA!",
            },
            "destaque_newsletter_semanal": None,
            "sugestao_conteudo_faq": None,
            "case_sucesso": None,
        },
    })


def test_pipeline_com_llm_falsa_devolvendo_json_bom():
    def llm_falsa(system_prompt, user_prompt):
        return _json_llm_bom()

    resultado = executar_pipeline(_dados_entrada_validos(), chamar_llm=llm_falsa)

    assert resultado["status"] == "sucesso"
    assert resultado["avisos"] == []
    assert len(resultado["analise_interacoes"]) == 1
    assert resultado["analise_interacoes"][0]["id"] == "MSG_001"


def test_pipeline_com_llm_devolvendo_texto_que_nao_eh_json():
    def llm_invalida(system_prompt, user_prompt):
        return "Desculpe, não consegui gerar o JSON solicitado."

    resultado = executar_pipeline(_dados_entrada_validos(), chamar_llm=llm_invalida)

    assert resultado["status"] == "erro"
    assert resultado["avisos"] == ["a LLM não retornou um JSON válido"]


def test_pipeline_com_llm_que_levanta_excecao():
    def llm_com_erro(system_prompt, user_prompt):
        raise RuntimeError(" Falha de conexão com o servidor")

    resultado = executar_pipeline(_dados_entrada_validos(), chamar_llm=llm_com_erro)

    assert resultado["status"] == "erro"
    assert len(resultado["avisos"]) == 1
    assert "falha ao chamar a LLM:" in resultado["avisos"][0]
    assert "Falha de conexão" in resultado["avisos"][0]


def test_pipeline_sem_interacoes_validas_nao_chama_llm():
    foi_chamada = False

    def llm_espia(system_prompt, user_prompt):
        nonlocal foi_chamada
        foi_chamada = True
        return "{}"

    dados_vazios = {
        "interacoes": [
            {"id": "1", "texto": "   "},
            {"id": "2", "texto": ""},
        ]
    }

    resultado = executar_pipeline(dados_vazios, chamar_llm=llm_espia)

    assert foi_chamada is False
    assert resultado["status"] == "erro"
    assert resultado["avisos"] == ["nenhuma interação com texto após a limpeza"]
    assert resultado["resumo_comunidade"]["total_interacoes_processadas"] == 0
