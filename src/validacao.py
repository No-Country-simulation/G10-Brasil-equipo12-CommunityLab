# src/validacao.py
import re
import unicodedata

from src.esquema import ATIVOS, BUCKET_OCI, ESCALA_SENTIMENTO, RELEVANCIAS, TIPOS_INTERACAO

# Campos de texto obrigatórios de cada ativo. Campos com valor padrão não geram aviso quando faltam.
CAMPOS_ATIVOS = {
    "post_linkedin": ["titulo", "copy"],
    "destaque_newsletter_semanal": ["secao", "chamada", "resumo"],
    "sugestao_conteudo_faq": ["tema", "pergunta", "origem"],
    "case_sucesso": ["titulo", "desafio", "solucao", "resultado"],
}
PADROES_ATIVOS = {
    "post_linkedin": {"canal_recomendado": "LinkedIn Oficial", "potencial_engajamento": None},
    "destaque_newsletter_semanal": {},
    "sugestao_conteudo_faq": {"status": "encaminhado_para_mentoria"},
    "case_sucesso": {},
}


def normalizar_texto(texto) -> str:
    """Minúsculas, sem acentos e sem espaços extras. Usado para comparar valores da LLM."""
    if not isinstance(texto, str):
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


def casar_opcao(valor, opcoes: list):
    """Devolve a opção oficial que corresponde a `valor` (ignorando maiúsculas e acentos), ou None."""
    alvo = normalizar_texto(valor).replace("_", " ")
    for opcao in opcoes:
        if normalizar_texto(opcao).replace("_", " ") == alvo:
            return opcao
    return None


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar_texto(texto)).strip("-") or "sem-periodo"


def _lista_de_textos(valor) -> list:
    if not isinstance(valor, list):
        return []
    return [t.strip() for t in valor if isinstance(t, str) and t.strip()]


def _lista_obrigatoria(dados: dict, campo: str, rotulo: str, avisos: list, aceita_vazia: bool = False) -> list:
    """Lê uma lista de textos e avisa quando ela falta, não é lista ou vem vazia sem poder."""
    valor = dados.get(campo)
    if not isinstance(valor, list):
        avisos.append(f"{rotulo} ausente ou não é uma lista ({valor!r})")
        return []
    lista = _lista_de_textos(valor)
    if not lista and not aceita_vazia:
        avisos.append(f"{rotulo} vazio")
    return lista


def _validar_analises(analises_raw, ids_esperados: list, avisos: list) -> list:
    if not isinstance(analises_raw, list):
        avisos.append("analise_interacoes ausente ou em formato inválido")
        return []

    # Aceita os dois nomes de cada ativo: a chave curta ("faq") e a chave do JSON ("sugestao_conteudo_faq")
    nomes_ativos = {**{k: k for k in ATIVOS}, **{v: k for k, v in ATIVOS.items()}}
    analises = []
    vistos = set()

    for item in analises_raw:
        if not isinstance(item, dict):
            avisos.append("item de analise_interacoes não é um objeto")
            continue
        id_item = str(item.get("id", "")).strip()
        if id_item not in ids_esperados:
            avisos.append(f"analise com id desconhecido descartada: {id_item or '(vazio)'}")
            continue
        if id_item in vistos:
            avisos.append(f"analise duplicada descartada: {id_item}")
            continue
        vistos.add(id_item)

        tipo = casar_opcao(item.get("tipo"), TIPOS_INTERACAO)
        sentimento = casar_opcao(item.get("sentimento"), ESCALA_SENTIMENTO)
        relevancia = casar_opcao(item.get("relevancia"), RELEVANCIAS)
        if tipo is None:
            avisos.append(f"{id_item}: tipo fora da lista ({item.get('tipo')!r})")
        if sentimento is None:
            avisos.append(f"{id_item}: sentimento fora da escala ({item.get('sentimento')!r})")
        if relevancia is None:
            avisos.append(f"{id_item}: relevancia fora da lista ({item.get('relevancia')!r})")

        ativos = []
        # Lista vazia é válida: a mensagem pode não servir para nenhum ativo
        nomes = _lista_obrigatoria(
            item, "ativos_recomendados", f"{id_item}: ativos_recomendados", avisos, aceita_vazia=True
        )
        for nome in nomes:
            chave = nomes_ativos.get(normalizar_texto(nome))
            if chave is None:
                avisos.append(f"{id_item}: ativo desconhecido ignorado ({nome!r})")
            elif chave not in ativos:
                ativos.append(chave)

        analises.append(
            {
                "id": id_item,
                "tipo": tipo,
                "sentimento": sentimento,
                "topicos": _lista_obrigatoria(item, "topicos", f"{id_item}: topicos", avisos),
                "ativos_recomendados": ativos,
                "relevancia": relevancia,
            }
        )

    for id_faltante in [i for i in ids_esperados if i not in vistos]:
        avisos.append(f"{id_faltante}: interação sem análise")

    # Mantém a ordem das interações de entrada
    return sorted(analises, key=lambda a: ids_esperados.index(a["id"]))


def _validar_ativo(nome: str, ativos_raw: dict, ids_esperados: list, avisos: list):
    if nome not in ativos_raw:
        avisos.append(f"ativo ausente: {nome}")
        return None
    bruto = ativos_raw[nome]
    if bruto is None:
        # null = a LLM indicou que não há material para este ativo nas mensagens
        return None
    if not isinstance(bruto, dict):
        avisos.append(f"ativo em formato inválido: {nome}")
        return None

    ativo = {}
    for campo in CAMPOS_ATIVOS[nome]:
        valor = bruto.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            avisos.append(f"{nome}.{campo} ausente")
            valor = ""
        ativo[campo] = valor.strip()
    for campo, padrao in PADROES_ATIVOS[nome].items():
        valor = bruto.get(campo)
        ativo[campo] = valor.strip() if isinstance(valor, str) and valor.strip() else padrao

    if nome == "case_sucesso":
        origem = _lista_obrigatoria(bruto, "interacoes_origem", "case_sucesso.interacoes_origem", avisos)
        desconhecidos = [i for i in origem if i not in ids_esperados]
        if desconhecidos:
            avisos.append(f"case_sucesso cita ids desconhecidos: {', '.join(desconhecidos)}")
        ativo["interacoes_origem"] = [i for i in origem if i in ids_esperados]
    return ativo


def _tem_conteudo(analises: list, ativos: dict) -> bool:
    """True se sobrou algo aproveitável: uma análise com algum campo válido ou um ativo com texto."""
    analise_util = any(a["tipo"] or a["sentimento"] or a["topicos"] for a in analises)
    ativo_util = any(ativo and any(ativo[campo] for campo in CAMPOS_ATIVOS[nome]) for nome, ativo in ativos.items())
    return analise_util or ativo_util


def validar_e_tratar_json(dados_json, dados_limpos: dict) -> dict:
    """
    Valida o JSON retornado pela LLM contra as interações que foram enviadas e monta
    a resposta final do pipeline, sempre com a mesma estrutura.

    Não inventa conteúdo: campo ausente ou fora da escala vira vazio/None e gera um aviso.
    status = "sucesso" (sem avisos), "parcial" (com avisos) ou "erro" (resposta inutilizável).
    """
    interacoes = dados_limpos.get("interacoes", [])
    ids_esperados = [i["id"] for i in interacoes]
    avisos = []

    if not isinstance(dados_json, dict) or not dados_json:
        avisos.append("resposta da LLM vazia ou não é um objeto JSON")
        dados_json = {}

    resumo_raw = dados_json.get("resumo_comunidade")
    resumo_valido = isinstance(resumo_raw, dict)
    if not resumo_valido:
        if dados_json:
            avisos.append("resumo_comunidade ausente")
        resumo_raw = {}
    sentimento_geral = casar_opcao(resumo_raw.get("sentimento_predominante"), ESCALA_SENTIMENTO)
    if resumo_valido and sentimento_geral is None:
        avisos.append(f"sentimento_predominante fora da escala ({resumo_raw.get('sentimento_predominante')!r})")

    topicos_principais = (
        _lista_obrigatoria(resumo_raw, "topicos_principais", "topicos_principais", avisos) if resumo_valido else []
    )

    analises = _validar_analises(dados_json.get("analise_interacoes"), ids_esperados, avisos) if dados_json else []

    ativos_raw = dados_json.get("ativos_distribuicao_gerados")
    if isinstance(ativos_raw, dict):
        ativos = {nome: _validar_ativo(nome, ativos_raw, ids_esperados, avisos) for nome in CAMPOS_ATIVOS}
    else:
        if dados_json:
            avisos.append("ativos_distribuicao_gerados ausente")
        ativos = dict.fromkeys(CAMPOS_ATIVOS)

    if not _tem_conteudo(analises, ativos):
        status = "erro"
    elif avisos:
        status = "parcial"
    else:
        status = "sucesso"

    return {
        "status": status,
        "avisos": avisos,
        "resumo_comunidade": {
            "sentimento_predominante": sentimento_geral,
            "topicos_principais": topicos_principais,
            "total_interacoes_processadas": len(interacoes),
        },
        "analise_interacoes": analises,
        "ativos_distribuicao_gerados": ativos,
        # Preenchido pelo código, não pela LLM: o upload para o OCI ainda não existe
        "armazenamento_oci": {
            "bucket": BUCKET_OCI,
            "caminho_objeto": f"ativos/{_slug(dados_limpos.get('periodo_referencia', ''))}/pacote-distribuicao.json",
            "status": "pendente_upload",
        },
    }
