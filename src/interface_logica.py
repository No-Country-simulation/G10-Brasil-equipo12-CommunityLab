# src/interface_logica.py
"""Lógica da interface de curadoria (Streamlit), separada da tela.

Nada aqui importa o Streamlit: assim dá para testar sem abrir a tela e sem chave de API.
A tela (interface_streamlit.py) só chama estas funções e desenha o resultado.

A interface NUNCA envia nada ao OCI: `executar` chama o pipeline com salvar_oci=False.
"""
import json
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.ingestao import ler_mensagens_comunidade, validar_lote
from src.limpeza import AUTOR_ANONIMO, limpar_dados_comunidade
from src.pipeline import caminho_local, processar_lote
from src.relevancia import LIMITE_AMOSTRA_PADRAO, selecionar_amostra
from src.roteamento import _cita, _normalizar, _primeiro_nome, rotear_interacoes

PASTA_DADOS = Path("dados")
EXTENSOES_ACEITAS = (".json", ".csv")

# Nome amigável, na ordem em que aparecem na tela, e o rótulo de cada campo do ativo
ATIVOS = {
    "post_linkedin": (
        "Post para o LinkedIn",
        {"titulo": "Título", "copy": "Texto do post", "canal_recomendado": "Canal recomendado", "potencial_engajamento": "Potencial de engajamento"},
    ),
    "destaque_newsletter_semanal": (
        "Destaque para a newsletter",
        {"secao": "Seção", "chamada": "Chamada", "resumo": "Resumo"},
    ),
    "sugestao_conteudo_faq": (
        "Pergunta frequente sugerida",
        {"tema": "Tema", "origem": "Origem", "status": "Status"},
    ),
}

# Exemplos mostrados na tela, com nome simples: arquivo em dados/ -> nome que o usuário vê
EXEMPLOS_DE_DEMONSTRACAO = {
    "caso_conquista.json": "Conquistas da comunidade",
    "caso_proposta_estagio.json": "Proposta de estágio e freela",
    "caso_duvida_tecnica.json": "Dúvida técnica",
}

# O que dizer quando um ativo não existe (cada um tem a sua rota: ver docs/regras_roteamento.md)
TEXTO_SEM_MATERIAL = {
    "post_linkedin": "Nenhum depoimento ou entrega de projeto neste período, então não há post.",
    "destaque_newsletter_semanal": "Nenhum depoimento, feedback ou entrega de projeto neste período, então não há destaque.",
    "sugestao_conteudo_faq": "Nenhuma dúvida técnica neste período, então não há sugestão de FAQ.",
}

# Os cinco valores que o motor aceita em `sentimento_predominante` (src/schemas.py), em frase simples
CLIMA_DA_COMUNIDADE = {
    "Altamente Positivo": "🎉 Muito animado",
    "Positivo": "🙂 Positivo",
    "Neutro": "😐 Tranquilo, sem grandes emoções",
    "Negativo": "😕 Atenção: a comunidade está insatisfeita",
    "Altamente Negativo": "⚠️ Alerta: a comunidade está muito insatisfeita",
}

TEXTO_STATUS_OCI = {
    "pendente_upload": "Não enviado ao OCI (esta tela não envia nada ao bucket).",
    "salvo_com_sucesso": "Enviado ao OCI.",
    "falha_ao_salvar": "Falha ao enviar ao OCI.",
}


@dataclass
class ResultadoExecucao:
    resposta: dict
    avisos: list = field(default_factory=list)
    caminho_local: str = ""
    origens: dict = field(default_factory=dict)  # ativo -> mensagens que podem tê-lo originado


def listar_exemplos(pasta: Path = PASTA_DADOS) -> list:
    """Arquivos .json e .csv da pasta de dados, em ordem alfabética."""
    pasta = Path(pasta)
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSOES_ACEITAS)


def exemplos_de_demonstracao(pasta: Path = PASTA_DADOS) -> list:
    """Os exemplos de demonstração que existem na pasta, como (caminho, nome simples), na ordem da tela.

    Arquivo que não existe (ainda) simplesmente não aparece.
    """
    pasta = Path(pasta)
    return [(pasta / arquivo, nome) for arquivo, nome in EXEMPLOS_DE_DEMONSTRACAO.items() if (pasta / arquivo).is_file()]


def carregar_lote_de_exemplo(caminho) -> dict:
    """Lê e valida um arquivo da pasta de dados (mesma função da linha de comando)."""
    return ler_mensagens_comunidade(str(caminho))


def carregar_lote_enviado(nome_arquivo: str, conteudo: bytes, periodo_csv: Optional[str] = None) -> dict:
    """Lê e valida um arquivo enviado pela tela.

    Reaproveita `ler_mensagens_comunidade` (a mesma validação da linha de comando) por meio de um
    arquivo temporário, que é apagado em seguida. O período só vale para CSV, que não o carrega.
    Levanta ValueError com mensagem legível se o formato ou o conteúdo estiver errado.
    """
    sufixo = Path(nome_arquivo).suffix.lower()
    if sufixo not in EXTENSOES_ACEITAS:
        raise ValueError(f"Formato de arquivo não suportado: {sufixo or '(sem extensão)'}. Utilize .json ou .csv")
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / f"lote{sufixo}"
        caminho.write_bytes(conteudo)
        try:
            if sufixo == ".csv" and periodo_csv:
                return ler_mensagens_comunidade(str(caminho), periodo_referencia=periodo_csv)
            return ler_mensagens_comunidade(str(caminho))
        except UnicodeDecodeError as erro:
            raise ValueError("Não consegui ler o arquivo: salve-o em UTF-8.") from erro
        except ValueError as erro:
            # JSON quebrado também cai aqui (JSONDecodeError é um ValueError)
            raise ValueError(f"Arquivo inválido: {erro}") from erro


def tabela_de_mensagens(lote: dict) -> list:
    """Linhas simples (id, autor, canal, tipo, texto) para mostrar o lote antes de processar."""
    return [
        {
            "id": i.get("id") or "",
            "autor": i.get("autor", ""),
            "canal": i.get("canal", ""),
            "tipo": i.get("tipo", ""),
            "texto": i.get("texto", ""),
        }
        for i in lote.get("interacoes", [])
    ]


class _ColetorDeAvisos(logging.Handler):
    """Guarda as mensagens de aviso do pipeline (amostra reduzida, ativo descartado) para a tela."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.mensagens = []

    def emit(self, record):
        self.mensagens.append(record.getMessage())


def executar(
    lote: dict,
    periodo: Optional[str] = None,
    limite_amostra: Optional[int] = LIMITE_AMOSTRA_PADRAO,
    cliente_llm=None,
) -> ResultadoExecucao:
    """Roda o pipeline completo SEM enviar ao OCI e devolve a resposta e os avisos do caminho.

    A cópia local continua sendo gravada em saida/ (ignorada pelo Git), como na linha de comando.
    Erros do pipeline (lote inválido, LLM, chave ausente) sobem como estão; a tela os mostra.
    """
    lote = dict(lote)
    if periodo:
        lote["periodo_referencia"] = periodo

    coletor = _ColetorDeAvisos()
    logger = logging.getLogger("src")
    logger.addHandler(coletor)
    try:
        resposta = processar_lote(lote, salvar_oci=False, limite_amostra=limite_amostra, cliente_llm=cliente_llm)
    finally:
        logger.removeHandler(coletor)

    return ResultadoExecucao(
        resposta=resposta.para_dict(),
        avisos=coletor.mensagens,
        caminho_local=str(caminho_local(lote["periodo_referencia"])),
        origens=origens_possiveis(lote, limite_amostra),
    )


def origens_possiveis(lote: dict, limite_amostra: Optional[int] = LIMITE_AMOSTRA_PADRAO) -> dict:
    """Para cada ativo, as mensagens que PODEM ter originado o texto: as que foram enviadas à LLM
    (depois da limpeza e da amostra) e cujo tipo alimenta aquele ativo (regras de roteamento).

    É a mesma limpeza, a mesma amostra e a mesma rota do pipeline, sem chamar a LLM. O motor não
    registra qual mensagem gerou qual trecho, então isto é uma lista de candidatas, não uma prova.
    Conversa geral não aparece em nenhum ativo (não tem rota).
    """
    dados_limpos = limpar_dados_comunidade(validar_lote(lote))
    amostra = selecionar_amostra(dados_limpos["interacoes"], limite_amostra)
    return {
        ativo: [{"id": m.get("id") or "", "autor": m.get("autor", ""), "canal": m.get("canal", ""), "tipo": m.get("tipo", "")} for m in mensagens]
        for ativo, mensagens in rotear_interacoes(amostra).items()
    }


def ativos_para_exibir(resposta: dict) -> list:
    """Os três ativos na ordem da tela: nome, se existe e os campos com rótulo.

    Ativo `null` (sem material) vem com `existe=False`, `campos=[]` e a frase `sem_material` para a tela.
    """
    ativos = resposta.get("ativos_distribuicao_gerados") or {}
    saida = []
    for chave, (nome, rotulos) in ATIVOS.items():
        valor = ativos.get(chave)
        campos = [(rotulo, valor[campo]) for campo, rotulo in rotulos.items() if valor and campo in valor]
        saida.append({
            "chave": chave,
            "nome": nome,
            "existe": bool(valor),
            "campos": campos,
            "sem_material": TEXTO_SEM_MATERIAL[chave],
        })
    return saida


def clima_da_comunidade(sentimento: str) -> str:
    """Frase simples para o sentimento predominante. Valor desconhecido aparece como veio, sem quebrar."""
    return CLIMA_DA_COMUNIDADE.get(sentimento, sentimento or "Não informado")


def frase_do_lote(lote: dict) -> str:
    """Uma linha para dizer o que foi carregado: quantas mensagens e de qual comunidade."""
    n = len(lote.get("interacoes", []))
    mensagens = "1 mensagem" if n == 1 else f"{n} mensagens"
    return f"Encontramos {mensagens} da comunidade {lote.get('origem_comunidade', '')}."


def texto_status_oci(resposta: dict) -> str:
    """Frase para a tela sobre o envio ao OCI (inclui o motivo, se houve falha)."""
    oci = resposta.get("armazenamento_oci") or {}
    status = oci.get("status", "")
    texto = TEXTO_STATUS_OCI.get(status, f"Status do OCI: {status or 'desconhecido'}.")
    if oci.get("detalhe_erro"):
        texto += f" Motivo: {oci['detalhe_erro']}"
    return texto


# ------------------------------------------------------------------ PASSO 2: revisão humana
# O contrato (src/schemas.py) não tem campo de aprovação. Por isso a decisão da pessoa fica num
# arquivo À PARTE, em saida/ (ignorada pelo Git), e o pacote gerado pelo motor não é alterado.

# Campos de texto que a pessoa pode corrigir. Os demais (seção, canal, engajamento, status) ficam fixos.
CAMPOS_EDITAVEIS = {
    "post_linkedin": ("titulo", "copy"),
    "destaque_newsletter_semanal": ("chamada", "resumo"),
    "sugestao_conteudo_faq": ("tema", "origem"),
}

DECISOES = ("aprovado", "reprovado")

# Motivos prontos para reprovar (a pessoa também pode acrescentar um detalhe, e tudo é opcional)
MOTIVOS_REPROVACAO = (
    "Sem autorização das pessoas citadas",
    "Fato incorreto ou exagerado",
    "Texto fora do tom da comunidade",
    "Outro motivo",
)

# O LinkedIn não aceita, de forma confiável, texto preenchido pelo endereço: o botão abre o feed e a pessoa cola o texto copiado.
URL_LINKEDIN = "https://www.linkedin.com/feed/"

# Orientação mostrada quando o texto cita alguém: como seguir sem a autorização da pessoa
EXEMPLO_SEM_NOME = "uma aluna da nossa comunidade"


def campos_editaveis(chave: str) -> list:
    """[(campo, rótulo)] dos campos que a pessoa pode editar neste ativo, na ordem da tela."""
    rotulos = ATIVOS[chave][1]
    return [(campo, rotulos[campo]) for campo in CAMPOS_EDITAVEIS[chave]]


def texto_do_ativo(resposta: dict, chave: str) -> dict:
    """Os campos editáveis do ativo, como o motor gerou ({campo: texto}). Vazio se o ativo não existe."""
    valor = (resposta.get("ativos_distribuicao_gerados") or {}).get(chave) or {}
    return {campo: valor.get(campo, "") for campo in CAMPOS_EDITAVEIS[chave]} if valor else {}


def pessoas_citadas(texto: str, lote: dict) -> list:
    """Autores do lote cujo nome completo ou primeiro nome aparece no texto (palavra inteira, sem acento nem maiúscula).

    É um AUXÍLIO para quem revisa conferir a autorização, não uma garantia: um nome escrito de outro
    jeito (apelido, erro de digitação) pode não ser achado. O código não verifica autorização.
    """
    texto_normalizado = _normalizar(texto)
    citadas = []
    for interacao in lote.get("interacoes", []):
        autor = (interacao.get("autor") or "").strip()
        if not autor or autor == AUTOR_ANONIMO or autor in citadas:
            continue
        primeiro = _primeiro_nome(autor)
        if _cita(texto_normalizado, _normalizar(autor)) or (primeiro and _cita(texto_normalizado, primeiro)):
            citadas.append(autor)
    return citadas


def pessoas_citadas_no_ativo(textos: dict, lote: dict) -> list:
    """O mesmo de `pessoas_citadas`, olhando todos os campos editáveis do ativo juntos."""
    return pessoas_citadas("\n".join(str(v) for v in textos.values()), lote)


def nome_do_revisor_valido(nome: str) -> bool:
    """A pessoa precisa se identificar para aprovar ou reprovar (pelo menos 2 letras, sem contar espaços)."""
    return len((nome or "").strip()) >= 2


def decisao_vale(decisao: Optional[dict], textos_atuais: dict) -> bool:
    """Uma decisão só vale se o texto não mudou depois dela: editar depois de aprovar exige aprovar de novo."""
    return bool(decisao) and decisao.get("texto_final") == textos_atuais


def registrar_decisao(
    chave: str,
    decisao: str,
    revisor: str,
    texto_original: dict,
    texto_final: dict,
    pessoas: list,
    motivo: str = "",
    conferiu_fatos: bool = False,
    conferiu_autorizacao: bool = False,
    agora: Optional[datetime] = None,
) -> dict:
    """Monta o registro de uma decisão. Aprovar exige nome, as duas conferências e texto não vazio."""
    if decisao not in DECISOES:
        raise ValueError(f"Decisão inválida: {decisao!r}.")
    if not nome_do_revisor_valido(revisor):
        raise ValueError("Informe o seu nome antes de aprovar ou reprovar.")
    if decisao == "aprovado":
        if not (conferiu_fatos and conferiu_autorizacao):
            raise ValueError("Para aprovar, confirme as duas conferências (fatos e autorização).")
        if any(not str(v).strip() for v in texto_final.values()):
            raise ValueError("Não dá para aprovar um texto com campo vazio.")
    return {
        "ativo": chave,
        "decisao": decisao,
        "revisor": revisor.strip(),
        "data_hora": (agora or datetime.now()).isoformat(timespec="seconds"),
        "texto_final": dict(texto_final),
        "texto_original": dict(texto_original),
        "editado_pela_pessoa": dict(texto_final) != dict(texto_original),
        "pessoas_citadas": list(pessoas),
        "conferiu_fatos": bool(conferiu_fatos),
        "conferiu_autorizacao": bool(conferiu_autorizacao),
        "motivo": (motivo or "").strip(),
    }


def caminho_curadoria(periodo_referencia: str, pasta_saida: str = "saida") -> Path:
    """'Semana_04' -> saida/2026-semana-04_curadoria.json (ao lado da cópia local do pacote)."""
    pacote = caminho_local(periodo_referencia, pasta_saida)
    return pacote.with_name(pacote.name.replace("_pacote-distribuicao.json", "_curadoria.json"))


def salvar_decisoes(decisoes: dict, periodo_referencia: str, pasta_saida: str = "saida") -> Path:
    """Grava o estado atual das decisões ({ativo: registro}) em saida/. Nunca envia nada ao OCI."""
    caminho = caminho_curadoria(periodo_referencia, pasta_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = {"periodo_referencia": periodo_referencia, "decisoes": list(decisoes.values())}
    caminho.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def pacote_aprovado(decisoes: dict, periodo_referencia: str) -> dict:
    """Só o que foi aprovado, com o texto final, para a pessoa baixar. Vazio se nada foi aprovado."""
    aprovados = [d for d in decisoes.values() if d["decisao"] == "aprovado"]
    return {"periodo_referencia": periodo_referencia, "aprovados": aprovados}


def montar_motivo(opcao: Optional[str], detalhe: str = "") -> str:
    """Junta o motivo escolhido e o detalhe digitado ('Sem autorização das pessoas citadas. Pediram para não aparecer'). Tudo é opcional."""
    partes = [(opcao or "").strip(), (detalhe or "").strip()]
    return ". ".join(p for p in partes if p)


def texto_para_publicar(chave: str, texto_final: dict) -> str:
    """O texto pronto para copiar e colar onde a pessoa vai publicar.

    Post: só o texto do post (o LinkedIn não tem título). Newsletter: chamada e resumo, separados por linha em branco.
    FAQ: só o tema (a origem é interna, cita quem fez a pergunta, e não é para publicar).
    """
    if chave == "post_linkedin":
        return texto_final.get("copy", "").strip()
    if chave == "destaque_newsletter_semanal":
        return "\n\n".join(p.strip() for p in (texto_final.get("chamada", ""), texto_final.get("resumo", "")) if p.strip())
    if chave == "sugestao_conteudo_faq":
        return texto_final.get("tema", "").strip()
    raise ValueError(f"Ativo desconhecido: {chave!r}.")
