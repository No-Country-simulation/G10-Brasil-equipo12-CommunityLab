import csv
import json
from pathlib import Path

from pydantic import ValidationError

from src.schemas import LoteEntrada


def _formatar_erros(erro: ValidationError) -> str:
    """Transforma os erros do Pydantic em linhas legíveis: '- campo: motivo'."""
    linhas = []
    for e in erro.errors():
        campo = ".".join(str(parte) for parte in e["loc"]) or "(arquivo inteiro)"
        linhas.append(f"  - {campo}: {e['msg']}")
    return "\n".join(linhas)


def validar_lote(dados) -> dict:
    """
    Confere se o lote segue o formato de entrada do projeto (src/schemas.py).
    Devolve um dicionário já normalizado (valores padrão aplicados e campos
    extras de teste, como 'cenario', descartados) ou levanta ValueError
    informando qual campo está errado.
    """
    try:
        lote = LoteEntrada.model_validate(dados)
    except ValidationError as erro:
        raise ValueError("Lote fora do formato esperado:\n" + _formatar_erros(erro)) from erro
    return lote.model_dump(exclude_none=True)


def ler_mensagens_comunidade(
    caminho_arquivo: str,
    origem_comunidade: str = "Discord_CSV_Import",
    periodo_referencia: str = "Semana_Atual",
) -> dict:
    """
    Lê um arquivo JSON ou CSV contendo as interações da comunidade,
    valida o formato e retorna um dicionário compatível com o padrão do pipeline.

    Os parâmetros origem_comunidade e periodo_referencia só valem para CSV,
    que não carrega esses dados dentro do arquivo.
    """
    caminho = Path(caminho_arquivo)

    if not caminho.exists():
        raise FileNotFoundError(f"O arquivo {caminho_arquivo} não foi encontrado.")

    extensao = caminho.suffix.lower()

    if extensao == ".json":
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return validar_lote(dados)

    elif extensao == ".csv":
        interacoes = []
        # utf-8-sig: aceita CSV salvo pelo Excel (com BOM) e também sem BOM
        with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
            leitor = csv.DictReader(f)
            for linha in leitor:
                interacao = {
                    "autor": linha.get("autor") or "Desconhecido",
                    "canal": linha.get("canal") or "#geral",
                    "tipo": (linha.get("tipo") or "interacao_geral").strip(),
                    "texto": linha.get("texto") or "",
                }
                if linha.get("id"):
                    interacao["id"] = linha["id"]
                interacoes.append(interacao)

        return validar_lote(
            {
                "origem_comunidade": origem_comunidade,
                "periodo_referencia": periodo_referencia,
                "interacoes": interacoes,
            }
        )
    else:
        raise ValueError(f"Formato de arquivo não suportado: {extensao}. Utilize .json ou .csv")