# src/validacao.py

def validar_e_tratar_json(dados_json: dict) -> dict:
    """
    Valida se o JSON retornado pela LLM possui todas as chaves obrigatórias 
    do projeto e aplica valores de fallback caso algum campo esteja faltando.
    """
    # Garante que o retorno é um dicionário
    if not isinstance(dados_json, dict):
        dados_json = {}

    # Define o esqueleto padrão (fallback) para evitar erros na aplicação
    json_valido = {
        "status": dados_json.get("status", "sucesso_com_fallback"),
        "resumo_comunidade": {
            "sentimento_predominante": dados_json.get("resumo_comunidade", {}).get("sentimento_predominante", "Neutro"),
            "topicos_principais": dados_json.get("resumo_comunidade", {}).get("topicos_principais", ["Geral"])
        },
        "total_interacoes_processadas": dados_json.get("total_interacoes_processadas", 1),
        "ativos_distribuicao_gerados": {
            "post_linkedin": {
                "titulo": dados_json.get("ativos_distribuicao_gerados", {}).get("post_linkedin", {}).get("titulo", "Atualizações da Comunidade ONE"),
                "copy": dados_json.get("ativos_distribuicao_gerados", {}).get("post_linkedin", {}).get("copy", "Confira as novidades e interações da nossa comunidade esta semana! #Tech #ONE")
            },
            "destaque_newsletter_semanal": {
                "secao": dados_json.get("ativos_distribuicao_gerados", {}).get("destaque_newsletter_semanal", {}).get("secao", "Destaque"),
                "chamada": dados_json.get("ativos_distribuicao_gerados", {}).get("destaque_newsletter_semanal", {}).get("chamada", "Resumo da Semana"),
                "resumo": dados_json.get("ativos_distribuicao_gerados", {}).get("destaque_newsletter_semanal", {}).get("resumo", "Acompanhe os principais debates e conquistas da nossa comunidade.")
            }
        },
        "sugestao_conteudo_faq": {
            "tema": dados_json.get("sugestao_conteudo_faq", {}).get("tema", "Dúvidas Frequentes da Comunidade"),
            "origem": dados_json.get("sugestao_conteudo_faq", {}).get("origem", "Interações gerais"),
            "status": dados_json.get("sugestao_conteudo_faq", {}).get("status", "analisado")
        }
    }

    return json_valido