import json
import sys

from dotenv import load_dotenv

from src.ingestao import ler_mensagens_comunidade
from src.pipeline import executar_pipeline

load_dotenv()

ARQUIVO_PADRAO = "dados/mensagens_exemplo.json"


def testar_pipeline_com_validacao(caminho_arquivo: str = ARQUIVO_PADRAO) -> int:
    print(f"1. Lendo o arquivo {caminho_arquivo}...")
    dados_brutos = ler_mensagens_comunidade(caminho_arquivo)

    print("2. Limpando os dados, chamando a LLM e validando a resposta...")
    resultado = executar_pipeline(dados_brutos)

    if resultado["status"] == "erro":
        print("❌ O pipeline falhou:")
    elif resultado["status"] == "parcial":
        print(f"⚠️ Resultado parcial ({len(resultado['avisos'])} aviso(s)):")
    else:
        print("✅ Sucesso! JSON validado:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    return 1 if resultado["status"] == "erro" else 0


if __name__ == "__main__":
    sys.exit(testar_pipeline_com_validacao(*sys.argv[1:2]))
