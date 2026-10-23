import csv
import json
from pathlib import Path

def ler_mensagens_comunidade(caminho_arquivo: str) -> dict:
    """
    Lê um arquivo JSON ou CSV contendo as interações da comunidade
    e retorna um dicionário estruturado compatível com o padrão do pipeline.
    """
    caminho = Path(caminho_arquivo)
    
    if not caminho.exists():
        raise FileNotFoundError(f"O arquivo {caminho_arquivo} não foi encontrado.")
    
    extensao = caminho.suffix.lower()
    
    if extensao == ".json":
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        # Aceita também um arquivo que seja só a lista de interações
        if isinstance(dados, list):
            dados = {"interacoes": dados}
        if not isinstance(dados, dict) or not isinstance(dados.get("interacoes"), list):
            raise ValueError(f"{caminho_arquivo} precisa ter uma lista em \"interacoes\".")
        return dados
            
    elif extensao == ".csv":
        interacoes = []
        with open(caminho, "r", encoding="utf-8") as f:
            leitor = csv.DictReader(f)
            # Sem a coluna "texto" todas as linhas seriam descartadas em silêncio na limpeza
            if "texto" not in (leitor.fieldnames or []):
                raise ValueError(f"{caminho_arquivo} precisa ter a coluna \"texto\". Colunas encontradas: {leitor.fieldnames}")
            for linha in leitor:
                interacoes.append({
                    "id": linha.get("id", ""),
                    "autor": linha.get("autor", "Desconhecido"),
                    "canal": linha.get("canal", "#geral"),
                    "tipo": linha.get("tipo", "geral"),
                    "texto": linha.get("texto", "")
                })
        
        # Retorna estruturado no padrão exigido pelo projeto
        return {
            "origem_comunidade": "Discord_CSV_Import",
            "periodo_referencia": "Semana_Atual",
            "interacoes": interacoes
        }
    else:
        raise ValueError(f"Formato de arquivo não suportado: {extensao}. Utilize .json ou .csv")