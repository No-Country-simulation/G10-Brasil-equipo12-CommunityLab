# src/interface_logica.py
"""Lógica da interface de curadoria (Streamlit), separada da tela.

Nada aqui importa o Streamlit: assim dá para testar sem abrir a tela e sem chave de API.
A tela (interface_streamlit.py) só chama estas funções e desenha o resultado.

A interface NUNCA envia nada ao OCI: `executar` chama o pipeline com salvar_oci=False.
"""
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.ingestao import ler_mensagens_comunidade, validar_lote
from src.limpeza import limpar_dados_comunidade
from src.pipeline import caminho_local, processar_lote
from src.relevancia import LIMITE_AMOSTRA_PADRAO, selecionar_amostra
from src.roteamento import rotear_interacoes

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
