# src/validacao.py

def validar_e_tratar_json(dados_json: dict, total_processado: int = 1) -> dict:
    """
    Valida se o JSON retornado pela LLM possui todas as chaves obrigatórias 
    do PDF do hackathon e aplica valores de fallback caso algum campo esteja faltando.
    """
    if not isinstance(dados_json, dict):
        dados_json = {}

    resumo_raw = dados_json.get("resumo_comunidade", {})
    ativos_raw = dados_json.get("ativos_distribuicao_gerados", {})
    post_raw = ativos_raw.get("post_linkedin", {})
    news_raw = ativos_raw.get("destaque_newsletter_semanal", {})
    faq_raw = ativos_raw.get("sugestao_conteudo_faq", {})
    oci_raw = dados_json.get("armazenamento_oci", {})

    json_valido = {
        "status": dados_json.get("status", "sucesso"),
        "resumo_comunidade": {
            "sentimento_predominante": resumo_raw.get("sentimento_predominante", "Altamente Positivo"),
            "topicos_principais": resumo_raw.get("topicos_principais", ["Geral"]),
            "total_interacoes_processadas": resumo_raw.get("total_interacoes_processadas", total_processado)
        },
        "ativos_distribuicao_gerados": {
            "post_linkedin": {
                "titulo": post_raw.get("titulo", "Atualizações da Comunidade ONE"),
                "copy": post_raw.get("copy", "Confira as novidades da nossa comunidade!"),
                "canal_recomendado": post_raw.get("canal_recomendado", "LinkedIn Oficial"),
                "potencial_engajamento": post_raw.get("potencial_engajamento", "Alto")
            },
            "destaque_newsletter_semanal": {
                "secao": news_raw.get("secao", "Vitória da Semana"),
                "chamada": news_raw.get("chamada", "Resumo da Semana"),
                "resumo": news_raw.get("resumo", "Acompanhe os principais destaques da comunidade.")
            },
            "sugestao_conteudo_faq": {
                "tema": faq_raw.get("tema", "Dúvidas Frequentes"),
                "origem": faq_raw.get("origem", "Interações gerais"),
                "status": faq_raw.get("status", "encaminhado_para_mentoria")
            }
        },
        "armazenamento_oci": {
            "bucket": oci_raw.get("bucket", "communitylab-ativos-marketing"),
            "caminho_objeto": oci_raw.get("caminho_objeto", "ativos/2026-semana-04/pacote-distribuicao.json"),
            "status": oci_raw.get("status", "pendente_upload")
        }
    }

    return json_valido