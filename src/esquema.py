# src/esquema.py
# Valores aceitos pelo pipeline. Prompt, validação e avaliação usam estas mesmas listas.

ESCALA_SENTIMENTO = ["Muito positivo", "Positivo", "Neutro", "Negativo", "Muito negativo"]

TIPOS_INTERACAO = ["depoimento", "pergunta_tecnica", "feedback", "entrega_projeto", "outro"]

# Chaves dos ativos dentro de "ativos_distribuicao_gerados"
ATIVOS = {
    "post_linkedin": "post_linkedin",
    "newsletter": "destaque_newsletter_semanal",
    "faq": "sugestao_conteudo_faq",
    "case_sucesso": "case_sucesso",
}

RELEVANCIAS = ["Alta", "Média", "Baixa"]

BUCKET_OCI = "communitylab-ativos-marketing"
