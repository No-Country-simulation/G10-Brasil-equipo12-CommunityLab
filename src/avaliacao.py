"""Avalia casos de demonstração com a LLM configurada ou com um resultado salvo."""

import argparse
import json
import math
import re
from pathlib import Path

from src.esquema import ATIVOS, ESCALA_SENTIMENTO, RELEVANCIAS, TIPOS_INTERACAO
from src.ingestao import ler_mensagens_comunidade
from src.limpeza import limpar_dados_comunidade, limpar_texto
from src.validacao import casar_opcao, normalizar_texto

DIMENSOES = ("tipo", "sentimento", "sentimento_tolerante", "relevancia", "ativo", "topicos", "descarte")
PALAVRAS_COMUNS = {
    "com",
    "sem",
    "para",
    "por",
    "uma",
    "uns",
    "umas",
    "dos",
    "das",
    "que",
    "como",
    "sobre",
    "nos",
    "nas",
    "pelo",
    "pela",
    "pelos",
    "pelas",
}


def mapear_ativo(texto) -> str | None:
    """Converte o nome humano ou o nome do objeto JSON para uma chave de ATIVOS."""
    nomes = {
        **{chave: chave for chave in ATIVOS},
        **{valor: chave for chave, valor in ATIVOS.items()},
        "post de LinkedIn": "post_linkedin",
        "case de sucesso": "case_sucesso",
    }
    nome = casar_opcao(texto, list(nomes))
    return nomes[nome] if nome is not None else None


def _textos(valor) -> list:
    """Normaliza uma lista de textos, ignorando itens vazios ou inválidos."""
    if not isinstance(valor, list):
        return []
    return [normalizar_texto(item) for item in valor if normalizar_texto(item)]


def _palavras(texto: str) -> set:
    return {palavra for palavra in re.findall(r"[a-z]+", texto) if len(palavra) >= 3 and palavra not in PALAVRAS_COMUNS}


def _topicos_casam(esperado: str, previsto: str) -> bool:
    """Compara por palavras inteiras, para "IA" não casar com "Mentoria".

    Casa se todas as palavras de um tópico estão no outro ("IA" e "Carreira em IA"),
    ou se há uma palavra significativa em comum, aceitando plural ("conquista" e "conquistas").
    """
    tokens_esperado = set(re.findall(r"[a-z0-9]+", esperado))
    tokens_previsto = set(re.findall(r"[a-z0-9]+", previsto))
    if (
        tokens_esperado
        and tokens_previsto
        and (tokens_esperado <= tokens_previsto or tokens_previsto <= tokens_esperado)
    ):
        return True
    return any(
        a == b or (min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)))
        for a in _palavras(esperado)
        for b in _palavras(previsto)
    )


def comparar_topicos(esperados, previstos) -> float:
    """Recall dos tópicos esperados: fração que casa com algum tópico previsto.

    Sem tópicos esperados, devolve 0; avaliar exclui esse caso da métrica.
    Um tópico previsto pode cobrir mais de um esperado.
    """
    esperados = _textos(esperados)
    previstos = _textos(previstos)
    if not esperados:
        return 0.0
    acertos = sum(any(_topicos_casam(esperado, previsto) for previsto in previstos) for esperado in esperados)
    return acertos / len(esperados)


def avaliar(casos: dict, resultado: dict) -> dict:
    """Compara por ID sem alterar as entradas; expectativas ausentes não pontuam.

    Cada dimensão é a média dos seus casos avaliados (tópicos usa recall por caso).
    A acurácia média dá peso igual às dimensões com expectativas, incluindo descarte.
    Sentimento tolerante é informativo e não entra nessa média para evitar peso duplo.
    Sem expectativas avaliáveis, a média é 0 e as acurácias por dimensão são None.
    Expectativa fora das listas oficiais (ex.: relevancia_esperada "Urgente") não pontua e gera aviso.
    """
    analises = {
        str(item.get("id", "")).strip(): item
        for item in resultado.get("analise_interacoes", [])
        if isinstance(item, dict)
    }
    # Reutiliza a limpeza para acompanhar IDs gerados e renomeados por duplicidade.
    interacoes_limpas = limpar_dados_comunidade(casos)["interacoes"]
    ids_validos = {interacao["id"] for interacao in interacoes_limpas}
    limpas = iter(interacoes_limpas)
    linhas = []
    avisos = list(resultado.get("avisos", []))
    valores = {dimensao: [] for dimensao in DIMENSOES}

    for posicao, caso in enumerate(casos.get("interacoes") or [], start=1):
        if not isinstance(caso, dict):
            continue
        descartado = not limpar_texto(caso.get("texto"))
        if descartado:
            id_caso = limpar_texto(str(caso.get("id") or "")) or f"MSG_{posicao:03d}"
        else:
            id_caso = next(limpas)["id"]
        previsto = analises.get(id_caso, {})
        notas = {}

        if descartado:
            # Se o id também pertence a um caso válido, a análise presente é a desse caso
            notas["descarte"] = float(id_caso not in analises or id_caso in ids_validos)
        else:
            for dimensao, campo, opcoes in (
                ("tipo", "tipo_esperado", TIPOS_INTERACAO),
                ("sentimento", "sentimento_esperado", ESCALA_SENTIMENTO),
                ("relevancia", "relevancia_esperada", RELEVANCIAS),
            ):
                if caso.get(campo) is None:
                    continue
                esperado = casar_opcao(caso[campo], opcoes)
                if esperado is None:
                    avisos.append(f"{id_caso}: {campo} inválido no arquivo de casos ({caso[campo]!r})")
                    continue
                previsto_valor = casar_opcao(previsto.get(dimensao), opcoes)
                notas[dimensao] = float(esperado == previsto_valor)
                if dimensao == "sentimento":
                    notas["sentimento_tolerante"] = float(
                        previsto_valor is not None and abs(opcoes.index(esperado) - opcoes.index(previsto_valor)) <= 1
                    )

            if caso.get("ativo_esperado") is not None:
                ativo = mapear_ativo(caso["ativo_esperado"])
                if ativo is None:
                    avisos.append(
                        f"{id_caso}: ativo_esperado inválido no arquivo de casos ({caso['ativo_esperado']!r})"
                    )
                else:
                    recomendados = previsto.get("ativos_recomendados")
                    recomendados = (
                        [mapear_ativo(nome) for nome in recomendados] if isinstance(recomendados, list) else []
                    )
                    notas["ativo"] = float(ativo in recomendados)
            if _textos(caso.get("topicos_esperados")):
                notas["topicos"] = comparar_topicos(caso["topicos_esperados"], previsto.get("topicos", []))

        for dimensao, nota in notas.items():
            valores[dimensao].append(nota)
        presente = id_caso in analises and not (descartado and id_caso in ids_validos)
        linhas.append({"id": id_caso, "descartado": descartado, "presente": presente, "notas": notas})

    metricas = {}
    for dimensao, notas in valores.items():
        metricas[dimensao] = {
            "acertos": sum(notas),
            "total": len(notas),
            "acuracia": sum(notas) / len(notas) if notas else None,
        }
    medias = [
        metrica["acuracia"]
        for dimensao, metrica in metricas.items()
        if dimensao != "sentimento_tolerante" and metrica["total"]
    ]
    return {
        "status": resultado.get("status", "erro"),
        "avisos": avisos,
        "casos": linhas,
        "metricas": metricas,
        "acuracia_media": sum(medias) / len(medias) if medias else 0.0,
    }


def _imprimir(avaliacao: dict):
    """Mostra notas por caso e médias; travessão indica dimensão não avaliada."""
    cabecalho = ["Caso", "Situação", "Tipo", "Sentimento", "Sent. ±1", "Relevância", "Ativo", "Tópicos", "Descarte"]
    linhas = [cabecalho]
    for caso in avaliacao["casos"]:
        if caso["descartado"]:
            situacao = "descarte falhou" if caso["presente"] else "descarte correto"
        else:
            situacao = "analisado" if caso["presente"] else "sem análise"
        celulas = [caso["id"], situacao]
        for dimensao in DIMENSOES:
            nota = caso["notas"].get(dimensao)
            if nota is None:
                celulas.append("—")
            elif dimensao == "topicos":
                celulas.append(f"{nota:.0%}")
            else:
                celulas.append("✓" if nota == 1 else "✗")
        linhas.append(celulas)
    larguras = [max(len(linha[i]) for linha in linhas) for i in range(len(cabecalho))]
    print(f"Status do pipeline: {avaliacao['status']}")
    for linha in linhas:
        print(" | ".join(celula.ljust(largura) for celula, largura in zip(linha, larguras)))
    print("\nResumo por dimensão (média dos casos):")
    for dimensao, metrica in avaliacao["metricas"].items():
        percentual = f"{metrica['acuracia']:.1%}" if metrica["total"] else "não avaliada"
        print(f"  {dimensao}: {percentual} ({metrica['total']} casos)")
    print(f"Acurácia média: {avaliacao['acuracia_media']:.1%} (sentimento exato; tolerância fora da média)")
    for aviso in avaliacao["avisos"]:
        print(f"Aviso: {aviso}")


def _acuracia_minima(texto: str) -> float:
    try:
        valor = float(texto)
    except ValueError as erro:
        raise argparse.ArgumentTypeError("Informe um número entre 0 e 1") from erro
    if not math.isfinite(valor) or not 0 <= valor <= 1:
        raise argparse.ArgumentTypeError("Informe um número entre 0 e 1")
    return valor


def main(argumentos=None) -> int:
    """Executa a CLI; resultado salvo evita inteiramente a chamada ao pipeline/LLM."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", default=str(Path(__file__).resolve().parents[1] / "dados/casos_demo.json"))
    parser.add_argument("--resultado", help="JSON do pipeline já salvo; não chama a LLM")
    parser.add_argument("--salvar", help="Grava o JSON do pipeline, não o relatório de métricas")
    parser.add_argument("--min-acuracia", type=_acuracia_minima, default=0.0, help="Mínimo entre 0 e 1 (padrão: 0)")
    args = parser.parse_args(argumentos)

    from dotenv import load_dotenv

    load_dotenv()
    try:
        casos = ler_mensagens_comunidade(args.casos)
        if not isinstance(casos, dict) or not isinstance(casos.get("interacoes"), list):
            raise ValueError("Os casos devem conter uma lista de interacoes")
        if not all(isinstance(caso, dict) for caso in casos["interacoes"]):
            raise ValueError("Cada caso deve ser um objeto JSON")
        if args.resultado:
            resultado = json.loads(Path(args.resultado).read_text(encoding="utf-8"))
        else:
            from src.pipeline import executar_pipeline

            resultado = executar_pipeline(casos)
        if not isinstance(resultado, dict) or resultado.get("status") not in {"sucesso", "parcial", "erro"}:
            raise ValueError("Resultado deve ser um objeto com status sucesso, parcial ou erro")
        if not isinstance(resultado.get("analise_interacoes", []), list):
            raise ValueError("analise_interacoes deve ser uma lista")
        if not isinstance(resultado.get("avisos", []), list):
            raise ValueError("avisos deve ser uma lista")
        if args.salvar:
            Path(args.salvar).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        avaliacao = avaliar(casos, resultado)
        _imprimir(avaliacao)
        return int(resultado["status"] == "erro" or avaliacao["acuracia_media"] < args.min_acuracia)
    except (OSError, ValueError) as erro:
        print(f"Erro na avaliação: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
