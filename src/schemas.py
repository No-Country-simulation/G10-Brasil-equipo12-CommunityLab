"""Contrato único de dados do CommunityLab (entrada e saída).

Fonte da verdade do formato do PDF do hackathon. Todos os módulos
(ingestão, limpeza, prompts, validação, OCI, Streamlit) devem usar estes modelos.
"""
import unicodedata
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------- ENTRADA
TIPOS_INTERACAO = (
    "depoimento",
    "pergunta_tecnica",
    "feedback",
    "interacao_geral",
    "entrega_projeto",  # aparece em dados/mensagens_exemplo.json e no texto do PDF
)


class Interacao(BaseModel):
    # extra="ignore": campos só de teste (cenario, tipo_esperado, ...) não quebram a entrada
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None  # opcional: o PDF não tem, o dataset_simulado tem
    autor: str = "Desconhecido"
    canal: str = "#geral"
    tipo: Literal[TIPOS_INTERACAO] = "interacao_geral"
    texto: str


class LoteEntrada(BaseModel):
    model_config = ConfigDict(extra="ignore")

    origem_comunidade: str
    periodo_referencia: str
    interacoes: list[Interacao] = Field(min_length=1)


# ------------------------------------------------------------------ SAÍDA
SENTIMENTOS = ("Altamente Positivo", "Positivo", "Neutro", "Negativo", "Altamente Negativo")
ENGAJAMENTOS = ("Alto", "Médio", "Baixo")


def _sem_acento_minusculo(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).strip().casefold()


def _normalizar(valor, validos: tuple):
    """'altamente positivo ' -> 'Altamente Positivo'. Valor desconhecido passa direto
    (e a validação do Literal recusa com mensagem clara)."""
    if isinstance(valor, str):
        for canonico in validos:
            if _sem_acento_minusculo(valor) == _sem_acento_minusculo(canonico):
                return canonico
    return valor


class ResumoComunidade(BaseModel):
    total_interacoes_processadas: int  # preenchido pelo CÓDIGO, não pela LLM
    sentimento_predominante: Literal[SENTIMENTOS]
    topicos_principais: list[str]


class PostLinkedin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    titulo: str
    copy_: str = Field(alias="copy")  # 'copy' sombreia um método do BaseModel
    canal_recomendado: str = "LinkedIn Oficial"
    potencial_engajamento: Literal[ENGAJAMENTOS]

    @field_validator("potencial_engajamento", mode="before")
    @classmethod
    def _normaliza_engajamento(cls, v):
        return _normalizar(v, ENGAJAMENTOS)


class DestaqueNewsletter(BaseModel):
    secao: str
    chamada: str
    resumo: str


class SugestaoFaq(BaseModel):
    tema: str
    origem: str
    status: str = "encaminhado_para_mentoria"


class AtivosDistribuicao(BaseModel):
    # None = "não havia material para este ativo" (ex.: lote sem depoimentos).
    post_linkedin: Optional[PostLinkedin] = None
    destaque_newsletter_semanal: Optional[DestaqueNewsletter] = None
    sugestao_conteudo_faq: Optional[SugestaoFaq] = None


class ArmazenamentoOci(BaseModel):
    bucket: str
    caminho_objeto: str
    status: str  # pendente_upload | salvo_com_sucesso | falha_ao_salvar
    detalhe_erro: Optional[str] = None


class RespostaCommunityLab(BaseModel):
    status: Literal["sucesso", "erro"]
    resumo_comunidade: ResumoComunidade
    ativos_distribuicao_gerados: AtivosDistribuicao
    armazenamento_oci: Optional[ArmazenamentoOci] = None

    def para_dict(self) -> dict:
        """Dicionário no formato do PDF (usa 'copy' em vez de 'copy_').
        Use SEMPRE este método para imprimir, salvar no OCI ou mostrar no Streamlit."""
        dados = self.model_dump(by_alias=True)
        oci = dados.get("armazenamento_oci")
        if oci is not None and oci.get("detalhe_erro") is None:
            oci.pop("detalhe_erro", None)
        return dados


# --------------------------------------------------------------- ANÁLISE LLM
class AnaliseLLM(BaseModel):
    """O que a LLM realmente devolve. Contagem e bloco OCI NÃO vêm dela."""

    sentimento_predominante: Literal[SENTIMENTOS]
    topicos_principais: list[str]
    ativos_distribuicao_gerados: AtivosDistribuicao

    @field_validator("sentimento_predominante", mode="before")
    @classmethod
    def _normaliza_sentimento(cls, v):
        return _normalizar(v, SENTIMENTOS)

    @field_validator("topicos_principais")
    @classmethod
    def _sem_vazios(cls, v):
        limpos = [t.strip() for t in v if isinstance(t, str) and t.strip()]
        if not limpos:
            raise ValueError("a lista de tópicos não pode ficar vazia")
        return limpos


def montar_resposta(
    lote: LoteEntrada,
    analise: AnaliseLLM,
    oci: Optional[ArmazenamentoOci] = None,
    total_interacoes: Optional[int] = None,
) -> RespostaCommunityLab:
    """Junta o que é da LLM com o que é determinístico (contagem e OCI).

    total_interacoes: quando a LLM analisa só uma amostra do lote, informe aqui o total
    do lote inteiro. Se omitido, vale a quantidade de interações de `lote`."""
    return RespostaCommunityLab(
        status="sucesso",
        resumo_comunidade=ResumoComunidade(
            total_interacoes_processadas=(
                total_interacoes if total_interacoes is not None else len(lote.interacoes)
            ),
            sentimento_predominante=analise.sentimento_predominante,
            topicos_principais=analise.topicos_principais,
        ),
        ativos_distribuicao_gerados=analise.ativos_distribuicao_gerados,
        armazenamento_oci=oci,
    )