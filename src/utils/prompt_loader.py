# src/utils/prompt_loader.py
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def carregar_guia_prompt(nome_canal: str) -> str:
    """
    Lê o arquivo de guia de tom de voz correspondente ao canal na pasta /prompts.
    """
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