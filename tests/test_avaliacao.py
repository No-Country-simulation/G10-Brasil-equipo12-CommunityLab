import copy
import json

import pytest

from src.avaliacao import avaliar, comparar_topicos, main, mapear_ativo, verificar_conteudo


@pytest.fixture
def exemplo():
    casos = {
        "interacoes": [
            {
                "id": "DEMO_01",
                "texto": "Consegui uma vaga!",
                "tipo_esperado": "depoimento",
                "sentimento_esperado": "Muito positivo",
                "topicos_esperados": ["Carreira", "IA"],
                "ativo_esperado": "post de LinkedIn",
                "relevancia_esperada": "Alta",
            }
        ]
    }
    resultado = {
        "status": "sucesso",
        "avisos": [],
        "analise_interacoes": [
            {
                "id": "DEMO_01",
                "tipo": "depoimento",
                "sentimento": "Muito positivo",
                "topicos": ["Carreira em IA"],
                "ativos_recomendados": ["post_linkedin"],
                "relevancia": "Alta",
            }
        ],
        "ativos_distribuicao_gerados": {},
    }
    return casos, resultado


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("post de LinkedIn", "post_linkedin"),
        (" FAQ ", "faq"),
        ("newsletter", "newsletter"),
        ("case de sucesso", "case_sucesso"),
        ("sugestao_conteudo_faq", "faq"),
        ("case_sucesso", "case_sucesso"),
        ("desconhecido", None),
        (None, None),
    ],
)
def test_mapeia_nomes_humanos_e_chaves(texto, esperado):
    assert mapear_ativo(texto) == esperado


@pytest.mark.parametrize(
    "esperados, previstos, recall",
    [
        (["Autenticação", "OCI"], ["Erro de autenticacao"], 0.5),
        (["API Groq"], ["Groq indisponível"], 1),
        (["Material de estudo"], ["Material de apoio"], 1),
        (["Carreira em IA"], ["IA"], 1),
        (["Conquista para alunos"], ["Ajuda para mentores"], 0),
        (["IA"], ["OCI"], 0),
        (["FAQ"], [], 0),
        ([], ["FAQ"], 0),
    ],
)
def test_recall_de_topicos(esperados, previstos, recall):
    assert comparar_topicos(esperados, previstos) == recall


def test_acertos_sem_mutar_entradas(exemplo):
    casos, resultado = exemplo
    antes = copy.deepcopy(exemplo)
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["acuracia_media"] == 1
    assert avaliacao["metricas"]["tipo"]["total"] == 1
    assert avaliacao["metricas"]["sentimento_tolerante"]["acuracia"] == 1
    assert exemplo == antes


def test_erros_e_tolerancia_nao_inflam_media(exemplo):
    casos, resultado = exemplo
    resultado["analise_interacoes"][0].update(
        {
            "tipo": "feedback",
            "sentimento": "Positivo",
            "topicos": ["Carreira"],
            "ativos_recomendados": ["faq"],
            "relevancia": "Baixa",
        }
    )
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["metricas"]["sentimento"]["acuracia"] == 0
    assert avaliacao["metricas"]["sentimento_tolerante"]["acuracia"] == 1
    assert avaliacao["metricas"]["topicos"]["acuracia"] == 0.5
    assert avaliacao["acuracia_media"] == pytest.approx(0.1)


@pytest.mark.parametrize("sentimento", ["Neutro", None, "Ativo"])
def test_sentimento_distante_ou_invalido_nao_acerta(exemplo, sentimento):
    casos, resultado = exemplo
    resultado["analise_interacoes"][0]["sentimento"] = sentimento
    assert avaliar(casos, resultado)["metricas"]["sentimento_tolerante"]["acuracia"] == 0


def test_campos_ausentes_nao_entram_no_denominador():
    casos = {
        "interacoes": [
            {"id": "A", "texto": "Olá", "relevancia_esperada": "Média"},
            {"id": "B", "texto": "Oi", "topicos_esperados": []},
        ]
    }
    resultado = {
        "status": "parcial",
        "analise_interacoes": [
            {"id": "A", "relevancia": "media"},
            {"id": "B"},
        ],
    }
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["acuracia_media"] == 1
    assert avaliacao["metricas"]["tipo"]["total"] == 0
    assert avaliacao["metricas"]["tipo"]["acuracia"] is None
    assert avaliacao["metricas"]["topicos"]["total"] == 0


def test_analise_ausente_e_campos_previstos_ausentes_contam_como_erro(exemplo):
    casos, resultado = exemplo
    for analises in ([], [{"id": "DEMO_01"}]):
        resultado["analise_interacoes"] = analises
        avaliacao = avaliar(casos, resultado)
        assert avaliacao["acuracia_media"] == 0
        assert avaliacao["metricas"]["tipo"]["total"] == 1


@pytest.mark.parametrize("presente, acerto", [(False, 1), (True, 0)])
def test_caso_vazio_deve_ser_descartado(presente, acerto):
    casos = {"interacoes": [{"id": "VAZIO", "texto": " \n ", "tipo_esperado": "outro"}]}
    resultado = {"status": "parcial", "analise_interacoes": [{"id": "VAZIO"}] if presente else []}
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["metricas"]["descarte"]["acuracia"] == acerto
    assert avaliacao["metricas"]["tipo"]["total"] == 0


def test_ids_gerados_e_duplicados_seguem_limpeza():
    casos = {
        "interacoes": [
            {"texto": "A", "tipo_esperado": "feedback"},
            {"id": "X", "texto": "B", "tipo_esperado": "outro"},
            {"id": "X", "texto": "C", "tipo_esperado": "depoimento"},
        ]
    }
    resultado = {
        "status": "sucesso",
        "analise_interacoes": [
            {"id": "X_3", "tipo": "depoimento"},
            {"id": "MSG_001", "tipo": "feedback"},
            {"id": "X", "tipo": "outro"},
        ],
    }
    assert avaliar(casos, resultado)["acuracia_media"] == 1


def test_sem_expectativas_nao_inventa_acuracia():
    assert avaliar({"interacoes": []}, {"status": "erro"})["acuracia_media"] == 0


@pytest.mark.parametrize(
    "status, minimo, codigo",
    [
        ("sucesso", "1", 0),
        ("parcial", "1", 0),
        ("erro", "0", 1),
    ],
)
def test_cli_resultado_salvo_sem_llm(exemplo, tmp_path, monkeypatch, capsys, status, minimo, codigo):
    from src import pipeline

    def proibido(*args, **kwargs):
        pytest.fail("O modo de resultado salvo não pode chamar o pipeline")

    monkeypatch.setattr(pipeline, "executar_pipeline", proibido)
    casos, resultado = exemplo
    resultado["status"] = status
    resultado["avisos"] = ["aviso sintético"]
    entrada = tmp_path / "casos.json"
    salvo = tmp_path / "resultado.json"
    copia = tmp_path / "copia.json"
    entrada.write_text(json.dumps(casos), encoding="utf-8")
    salvo.write_text(json.dumps(resultado), encoding="utf-8")
    assert (
        main(["--casos", str(entrada), "--resultado", str(salvo), "--salvar", str(copia), "--min-acuracia", minimo])
        == codigo
    )
    assert json.loads(copia.read_text(encoding="utf-8")) == resultado
    saida = capsys.readouterr().out
    assert "DEMO_01" in saida and "100.0%" in saida
    assert "aviso sintético" in saida


def test_cli_limite_e_pipeline_com_resposta_sintetica(exemplo, tmp_path, monkeypatch):
    from src import pipeline

    casos, resultado = exemplo
    # Substitui apenas a fronteira externa; limpeza e validação reais continuam rodando.
    monkeypatch.setattr(pipeline, "chamar_llm_configurada", lambda *args: json.dumps(resultado))
    entrada = tmp_path / "casos.json"
    salvo = tmp_path / "resultado.json"
    entrada.write_text(json.dumps(casos), encoding="utf-8")
    assert main(["--casos", str(entrada), "--salvar", str(salvo), "--min-acuracia", "1"]) == 0
    assert json.loads(salvo.read_text())["analise_interacoes"][0]["id"] == "DEMO_01"
    resultado["analise_interacoes"][0]["tipo"] = "feedback"
    assert main(["--casos", str(entrada), "--min-acuracia", "0.9"]) == 1


def test_cli_arquivo_invalido_retorna_erro(tmp_path):
    arquivo = tmp_path / "invalido.json"
    arquivo.write_text("{", encoding="utf-8")
    assert main(["--casos", str(arquivo), "--resultado", str(arquivo)]) == 1


@pytest.mark.parametrize("minimo", ["nan", "inf", "-0.1", "1.1"])
def test_cli_rejeita_limite_invalido(minimo):
    with pytest.raises(SystemExit) as erro:
        main(["--min-acuracia", minimo])
    assert erro.value.code == 2


@pytest.mark.parametrize(
    "esperados, previstos, recall",
    [
        (["IA"], ["Mentoria"], 0),
        (["IA"], ["a"], 0),
        (["Conquistas"], ["Conquista de vaga"], 1),
    ],
)
def test_topicos_casam_por_palavra_inteira(esperados, previstos, recall):
    assert comparar_topicos(esperados, previstos) == recall


def test_caso_vazio_com_id_de_caso_valido_nao_conta_como_falha():
    casos = {
        "interacoes": [
            {"id": "DEMO_01", "texto": "Passei!", "tipo_esperado": "depoimento"},
            {"id": "DEMO_01", "texto": "   "},
        ]
    }
    resultado = {"status": "sucesso", "analise_interacoes": [{"id": "DEMO_01", "tipo": "depoimento"}]}
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["metricas"]["descarte"]["acuracia"] == 1
    assert avaliacao["acuracia_media"] == 1


def test_ativos_recomendados_com_nome_do_json_sao_aceitos(exemplo):
    casos, resultado = exemplo
    casos["interacoes"][0]["ativo_esperado"] = "FAQ"
    resultado["analise_interacoes"][0]["ativos_recomendados"] = ["sugestao_conteudo_faq"]
    assert avaliar(casos, resultado)["metricas"]["ativo"]["acuracia"] == 1


def test_interacoes_none_ou_itens_invalidos_nao_quebram(exemplo):
    _, resultado = exemplo
    assert avaliar({"interacoes": None}, resultado)["acuracia_media"] == 0
    casos = {"interacoes": ["texto solto", {"id": "DEMO_01", "texto": "Oi", "tipo_esperado": "depoimento"}]}
    assert avaliar(casos, resultado)["metricas"]["tipo"]["acuracia"] == 1


def test_expectativa_invalida_gera_aviso_e_nao_pontua(exemplo):
    casos, resultado = exemplo
    casos["interacoes"][0]["relevancia_esperada"] = "Urgente"
    casos["interacoes"][0]["ativo_esperado"] = "blog"
    avaliacao = avaliar(casos, resultado)
    assert avaliacao["metricas"]["relevancia"]["total"] == 0
    assert avaliacao["metricas"]["ativo"]["total"] == 0
    assert any("relevancia_esperada inválido" in aviso for aviso in avaliacao["avisos"])
    assert any("ativo_esperado inválido" in aviso for aviso in avaliacao["avisos"])


def test_ativo_esperado_nenhum_exige_lista_vazia():
    casos = {"interacoes": [{"id": "OI", "texto": "Bom dia!", "ativo_esperado": "nenhum"}]}

    def nota(analises):
        return avaliar(casos, {"status": "sucesso", "analise_interacoes": analises})["metricas"]["ativo"]["acuracia"]

    assert nota([{"id": "OI", "ativos_recomendados": []}]) == 1
    assert nota([{"id": "OI", "ativos_recomendados": ["faq"]}]) == 0
    assert nota([]) == 0
    assert nota([{"id": "OI"}]) == 0
    assert nota([{"id": "OI", "ativos_recomendados": None}]) == 0
    assert nota([{"id": "OI", "ativos_recomendados": "faq"}]) == 0


def _resultado_com_post(copy):
    return {
        "status": "sucesso",
        "analise_interacoes": [],
        "ativos_distribuicao_gerados": {
            "post_linkedin": {"titulo": "Conquista", "copy": copy},
            "sugestao_conteudo_faq": {"tema": "Eu tenho uma dúvida", "pergunta": "Como eu faço?"},
        },
    }


def test_verifica_primeira_pessoa_fora_de_aspas():
    casos = {"interacoes": []}

    em_primeira_pessoa = verificar_conteudo(casos, _resultado_com_post("Estou muito feliz, passei na vaga!"))
    com_citacao = verificar_conteudo(casos, _resultado_com_post('A Ana contou: "passei na vaga!"'))

    assert em_primeira_pessoa == ["post_linkedin com marcas de primeira pessoa (estou, passei)"]
    assert com_citacao == []


def test_verifica_termos_proibidos_so_nos_ativos_publicos():
    casos = {"interacoes": [{"id": "AV_15", "texto": "x", "nao_deve_conter": ["TechNova"]}]}
    resultado = _resultado_com_post("A TechNova vai contratar a turma")
    resultado["ativos_distribuicao_gerados"]["sugestao_conteudo_faq"]["tema"] = "TechNova"

    problemas = verificar_conteudo(casos, resultado)

    assert problemas == ["post_linkedin contém 'TechNova', proibido pelo caso AV_15"]
    assert avaliar(casos, resultado)["conteudo"] == problemas


def test_primeira_pessoa_com_outros_verbos_e_voz_da_comunidade():
    casos = {"interacoes": []}

    assert verificar_conteudo(casos, _resultado_com_post("Fui contratada e recebi uma proposta.")) == [
        "post_linkedin com marcas de primeira pessoa (fui, recebi)"
    ]
    assert verificar_conteudo(casos, _resultado_com_post("Nossa comunidade celebra a vaga da Ana.")) == []


def test_citacao_com_aspas_simples_e_aspa_aberta_em_outro_campo():
    casos = {"interacoes": []}
    citacao_simples = _resultado_com_post("Ana contou: ‘Eu consegui minha vaga!’ e 'passei de novo'")
    aspa_aberta = _resultado_com_post('Estou feliz e consegui a vaga!"')
    aspa_aberta["ativos_distribuicao_gerados"]["post_linkedin"]["titulo"] = 'Ana diz "olá'

    assert verificar_conteudo(casos, citacao_simples) == []
    assert verificar_conteudo(casos, aspa_aberta) == ["post_linkedin com marcas de primeira pessoa (consegui, estou)"]
