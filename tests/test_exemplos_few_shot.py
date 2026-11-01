# tests/test_exemplos_few_shot.py
"""Confere os exemplos few-shot dos guias de /prompts. Rodam offline, sem chave de API."""
import json
import re
import unittest
from pathlib import Path

from src.schemas import AtivosDistribuicao
from src.utils.prompt_loader import carregar_guia_prompt

CAMPO_POR_CANAL = {
    "linkedin": "post_linkedin",
    "newsletter": "destaque_newsletter_semanal",
    "faq": "sugestao_conteudo_faq",
}
# Palavras que inflam conquistas: não podem aparecer em nenhum exemplo
# "diferença", "decisiv" e "diferencial": os exemplos não podem plantar frases de causa que o modelo
# copiaria para outros lotes (a mensagem real só diz, por exemplo, "foi o assunto principal")
PALAVRAS_PROIBIDAS = ("garant", "contratad", "conquistou o est", "diferença", "decisiv", "diferencial")


def _blocos_json(texto):
    secao = texto.split("## Exemplos (few-shot)", 1)[1].split("## Exemplo de System Prompt", 1)[0]
    return [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", secao, flags=re.S)]


class TestExemplosFewShot(unittest.TestCase):
    def test_cada_guia_tem_exemplos_validos_no_contrato(self):
        for canal, campo in CAMPO_POR_CANAL.items():
            with self.subTest(canal=canal):
                blocos = _blocos_json(carregar_guia_prompt(canal))
                self.assertGreaterEqual(len(blocos), 2)
                for bloco in blocos:
                    self.assertEqual(list(bloco), [campo])  # cada exemplo traz só o ativo do canal
                    AtivosDistribuicao(**bloco)  # levanta erro se fugir do contrato
                self.assertTrue(any(b[campo] is not None for b in blocos))

    def test_guias_mostram_exemplo_sem_material(self):
        for canal in ("linkedin", "faq"):
            with self.subTest(canal=canal):
                blocos = _blocos_json(carregar_guia_prompt(canal))
                self.assertTrue(any(list(b.values())[0] is None for b in blocos))

    def test_exemplos_nao_inflam_conquistas(self):
        for canal in CAMPO_POR_CANAL:
            texto = json.dumps(_blocos_json(carregar_guia_prompt(canal)), ensure_ascii=False).lower()
            for palavra in PALAVRAS_PROIBIDAS:
                with self.subTest(canal=canal, palavra=palavra):
                    self.assertNotIn(palavra, texto)

    def test_posts_de_linkedin_tem_de_2_a_5_hashtags_so_no_final(self):
        for bloco in _blocos_json(carregar_guia_prompt("linkedin")):
            post = bloco["post_linkedin"]
            if post is None:
                continue
            copia = post["copy"]
            tags = re.findall(r"#\w+", copia)
            self.assertTrue(2 <= len(tags) <= 5, copia)
            ultimo_paragrafo = copia.strip().split("\n\n")[-1]
            self.assertEqual(len(re.findall(r"#\w+", ultimo_paragrafo)), len(tags))

    def test_faq_nao_traz_solucao_e_mantem_status(self):
        for bloco in _blocos_json(carregar_guia_prompt("faq")):
            faq = bloco["sugestao_conteudo_faq"]
            if faq is not None:
                self.assertEqual(faq["status"], "encaminhado_para_mentoria")
                self.assertEqual(set(faq), {"tema", "origem", "status"})

    def test_caso_de_regressao_da_camila_esta_no_caso_de_teste(self):
        caminho = Path(__file__).resolve().parents[1] / "dados" / "caso_teste_few_shot.json"
        lote = json.loads(caminho.read_text(encoding="utf-8"))
        camila = [i for i in lote["interacoes"] if i["id"] == "MSG_T04"]
        self.assertEqual(len(camila), 1)
        self.assertIn("assunto principal da entrevista", camila[0]["texto"])
        self.assertNotIn("diferença", camila[0]["texto"].lower())

    def test_regra_da_newsletter_pede_para_repetir_as_palavras_da_pessoa(self):
        guia = carregar_guia_prompt("newsletter")
        self.assertIn("repita as palavras dela", guia)
        self.assertIn("foi o assunto principal da entrevista", guia)


if __name__ == "__main__":
    unittest.main()
