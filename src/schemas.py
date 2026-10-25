"""Contrato único de dados do CommunityLab (entrada e saída).

Fonte da verdade do formato do PDF do hackathon. Todos os módulos
(ingestão, limpeza, prompts, validação, OCI, Streamlit) devem usar estes modelos.
"""
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


class ResumoComunidade(BaseModel):
    total_interacoes_processadas: int  # preenchido pelo CÓDIGO, não pela LLM
    sentimento_predominante: Literal[SENTIMENTOS]
    topicos_principais: list[str]


class PostLinkedin(BaseModel):
    titulo: str
    copy_: str = Field(alias="copy")  # 'copy' sombreia um método do BaseModel
    canal_recomendado: str = "LinkedIn Oficial"
    potencial_engajamento: Literal["Alto", "Médio", "Baixo"]

    model_config = ConfigDict(populate_by_name=True)


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


# --------------------------------------------------------------- ANÁLISE LLM
class AnaliseLLM(BaseModel):
    """O que a LLM realmente devolve. Contagem e bloco OCI NÃO vêm dela."""

    sentimento_predominante: Literal[SENTIMENTOS]
    topicos_principais: list[str]
    ativos_distribuicao_gerados: AtivosDistribuicao

    @field_validator("topicos_principais")
    @classmethod
    def _sem_vazios(cls, v):
        return [t.strip() for t in v if t and t.strip()]


def montar_resposta(
    lote: LoteEntrada, analise: AnaliseLLM, oci: Optional[ArmazenamentoOci] = None
) -> RespostaCommunityLab:
    """Junta o que é da LLM com o que é determinístico (contagem e OCI)."""
    return RespostaCommunityLab(
        status="sucesso",
        resumo_comunidade=ResumoComunidade(
            total_interacoes_processadas=len(lote.interacoes),
            sentimento_predominante=analise.sentimento_predominante,
            topicos_principais=analise.topicos_principais,
        ),
        ativos_distribuicao_gerados=analise.ativos_distribuicao_gerados,
        armazenamento_oci=oci,
    )