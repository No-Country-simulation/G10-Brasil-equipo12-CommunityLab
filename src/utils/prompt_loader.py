# src/utils/prompt_loader.py
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Só letras minúsculas, números, hífen e sublinhado: impede nomes como "../README"
_NOME_VALIDO = re.compile(r"^[a-z0-9_-]+$")


def carregar_guia_prompt(nome_canal: str) -> str:
    """
    Lê o arquivo de guia de tom de voz correspondente ao canal na pasta /prompts.
    """
    if not isinstance(nome_canal, str) or not _NOME_VALIDO.match(nome_canal):
        raise ValueError(
            f"Nome de canal inválido: {nome_canal!r}. Use só letras minúsculas, números, '-' e '_' (ex.: 'linkedin')."
        )

    # Sobe a partir de src/utils/ até a raiz do repositório
    raiz_projeto = Path(__file__).resolve().parents[2]
    caminho_arquivo = raiz_projeto / "prompts" / f"{nome_canal}.md"

    try:
        if caminho_arquivo.exists():
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logger.warning(f"Arquivo de prompt não encontrado em {caminho_arquivo}. Usando padrão.")
            return f"Atue como um redator especializado para o canal {nome_canal}."
    except Exception as e:
        logger.error(f"Erro ao carregar o prompt para {nome_canal}: {e}")
        raise
