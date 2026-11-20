# Teste da interface: exemplos prontos e casos sujos

Este documento registra o teste manual da tela da Pauta IA (`interface_streamlit.py`) com os exemplos de demonstração e com os casos sujos do `dados/casos_demo.json`. Cada resultado tem um print como evidência, em [`docs/evidencias/interface/`](evidencias/interface/).

## Resumo

| Parte | O que foi testado | Resultado |
|---|---|---|
| A | Os três exemplos prontos da tela (Conquistas da comunidade, Proposta de estágio e freela, Dúvida técnica) | Os três geraram só os conteúdos que têm material. Os demais mostraram o motivo. |
| B | Três casos sujos, enviados um por vez (DEMO_04 vazia, DEMO_05 repetida, DEMO_06 com erros de digitação) | Os três tiveram o resultado esperado. |
| C | O lote completo (`dados/casos_demo.json`, 10 mensagens) | Entraram 10 mensagens e foram analisadas 8. O resultado foi o esperado. |

Duas limitações aparecem na seção "Limitações e observações": a tela não mostra quais mensagens foram descartadas na limpeza, e o aviso de FAQ vazia usa sempre a mesma frase.

## Como o teste foi feito

* **Quem e quando:** Bruna Medeiros Brandão, em 20/11/2026 (os prints têm data e hora entre 09:01 e 13:53).
* **Versão:** `main` no commit `edb55c5` (merge da PR #74), com a tela atual (cartões empilhados, botão **Confirmar** ao lado do nome, resumo antes da revisão).
* **Como:** `streamlit run interface_streamlit.py`, tudo pela tela, com a Groq real. Os exemplos foram escolhidos em "Exemplo do projeto". O lote completo e os casos sujos entraram por "Enviar arquivo".
* **Dados:** simulados. Os nomes de revisor nos prints ("Marta", "marta", "maria") são fictícios.
* **O que não foi usado:** nenhum teste enviou algo à OCI (a tela nunca envia) e nenhuma captura mostra chave ou `.env`.
* **Arquivos dos casos sujos:** cada um tem **uma** mensagem, copiada do `dados/casos_demo.json`, com período `Semana_Teste` e comunidade `Teste_Interface`. Ficam em [`evidencias/interface/arquivos_de_teste/`](evidencias/interface/arquivos_de_teste/) para quem quiser repetir.

Como a LLM varia entre execuções, os textos gerados podem ser um pouco diferentes se o teste for repetido. O resultado esperado, porém, é sobre **quais conteúdos saem**, e isso não deve mudar (veja [`resultados_esperados.md`](resultados_esperados.md) e [`regras_roteamento.md`](regras_roteamento.md)).

## Parte A: exemplos prontos da tela

| Exemplo | Mensagens | Esperado | O que apareceu | Bateu? |
|---|---|---|---|---|
| Conquistas da comunidade | EX1_01 (depoimento), EX1_02 (entrega de projeto) | Post e newsletter. Sem FAQ. | Post para o LinkedIn e destaque para a newsletter. FAQ: *"Nenhuma dúvida técnica neste período, então não há sugestão de FAQ."* | Sim |
| Proposta de estágio e freela | MSG_010 e MSG_016 (dois depoimentos) | Post e newsletter. Sem FAQ. | Post para o LinkedIn e destaque para a newsletter. FAQ: *"Nenhuma dúvida técnica neste período, então não há sugestão de FAQ."* | Sim |
| Dúvida técnica | MSG_002 (pergunta técnica) | Só FAQ. Sem post e sem newsletter. | FAQ gerada. Post: *"Nenhum depoimento ou entrega de projeto neste período, então não há post."* Newsletter: *"Nenhum depoimento, feedback ou entrega de projeto neste período, então não há destaque."* | Sim |

No exemplo de estágio, o texto diz que Gustavo Prado **recebeu uma proposta** de estágio, e não que foi contratado. É a regra de fidelidade dos guias de prompt.

<details>
<summary>Prints: Conquistas da comunidade (7)</summary>

![Escolha do exemplo Conquistas da comunidade, com 2 mensagens](evidencias/interface/parteA_conquistas01.png)

![Mensagens de origem: EX1_01 (depoimento) e EX1_02 (entrega_projeto)](evidencias/interface/parteA_conquistas02.png)

![Topo da revisão e post gerado](evidencias/interface/parteA_conquistas03.png)

![Post aprovado](evidencias/interface/parteA_conquistas04.png)

![Newsletter aprovada e FAQ sem sugestão](evidencias/interface/parteA_conquistas05.png)

![Resumo da comunidade e post em "Prontos para publicar"](evidencias/interface/parteA_conquistas06.png)

![Newsletter em "Prontos para publicar"](evidencias/interface/parteA_conquistas07.png)

</details>

<details>
<summary>Prints: Proposta de estágio e freela (8)</summary>

![Escolha do exemplo Proposta de estágio e freela, com 2 mensagens](evidencias/interface/parteA_estagio01.png)

![Topo da revisão e post gerado, antes de aprovar (nome do revisor ainda vazio)](evidencias/interface/parteA_estagio02.png)

![Post aprovado](evidencias/interface/parteA_estagio03.png)

![Newsletter aprovada](evidencias/interface/parteA_estagio04.png)

![Resumo da comunidade e post em "Prontos para publicar"](evidencias/interface/parteA_estagio05.png)

![Post e newsletter em "Prontos para publicar"](evidencias/interface/parteA_estagio06.png)

![Segunda geração: mensagens de origem (MSG_010 e MSG_016)](evidencias/interface/parteA_estagio07.png)

![Segunda geração: newsletter aprovada e FAQ sem sugestão](evidencias/interface/parteA_estagio08.png)

</details>

<details>
<summary>Prints: Dúvida técnica (5)</summary>

![Escolha do exemplo Dúvida técnica, com 1 mensagem](evidencias/interface/parteA_duvida01.png)

![Mensagem de origem: MSG_002 (pergunta_tecnica)](evidencias/interface/parteA_duvida02.png)

![Revisão: sem post, sem destaque e com a FAQ gerada](evidencias/interface/parteA_duvida03.png)

![FAQ aprovada e resumo da comunidade](evidencias/interface/parteA_duvida04.png)

![Revisão e "Prontos para publicar": só o tema da FAQ](evidencias/interface/parteA_duvida05.png)

</details>

## Parte B: casos sujos, um por vez

Cada arquivo tem uma única mensagem e foi enviado em "Enviar arquivo".

| Caso | Esperado | O que apareceu | Bateu? |
|---|---|---|---|
| DEMO_04 (texto vazio) | Erro: *"Não consegui gerar o conteúdo. Nenhuma interação com texto sobrou depois da limpeza."* | Exatamente essa mensagem, em vermelho, sem gerar nada | Sim |
| DEMO_05 (repetida da DEMO_02) | FAQ sobre a API da Groq no OCI. Sem post e sem newsletter. | FAQ *"Dica Rápida: conectar API da Groq no OCI sem erro de autenticação"*. Post e newsletter com o aviso de que não há material. | Sim |
| DEMO_06 (vaga, com erros de digitação) | Sem FAQ (decisão 12 de [`regras_roteamento.md`](regras_roteamento.md)) | Sem post, sem newsletter e sem FAQ. A mensagem contou no resumo (1 analisada). | Sim |

Em "Prontos para publicar", a FAQ da DEMO_05 sai só com o **tema**: o nome de quem perguntou aparece apenas no campo interno "Origem", durante a revisão.

<details>
<summary>Prints: DEMO_04 (2)</summary>

![Arquivo de teste anexado (1 mensagem)](evidencias/interface/parteB_demo04_01.png)

![Mensagem DEMO_04 sem texto e aviso de erro](evidencias/interface/parteB_demo04_02.png)

</details>

<details>
<summary>Prints: DEMO_05 (5)</summary>

![Arquivo de teste anexado (1 mensagem)](evidencias/interface/parteB_demo05_01.png)

![Mensagem DEMO_05](evidencias/interface/parteB_demo05_02.png)

![Revisão: sem post, sem destaque e com FAQ](evidencias/interface/parteB_demo05_03.png)

![FAQ aprovada, com tema, origem e status](evidencias/interface/parteB_demo05_04.png)

![Resumo, revisão e "Prontos para publicar" (só o tema)](evidencias/interface/parteB_demo05_05.png)

</details>

<details>
<summary>Prints: DEMO_06 (4)</summary>

![Arquivo de teste anexado (1 mensagem)](evidencias/interface/parteB_demo06_01.png)

![Mensagem DEMO_06](evidencias/interface/parteB_demo06_02.png)

![Revisão: sem post, sem destaque e sem FAQ](evidencias/interface/parteB_demo06_03.png)

![Resumo (1 mensagem analisada) e revisão sem itens](evidencias/interface/parteB_demo06_04.png)

</details>

## Parte C: o lote completo

Arquivo: `dados/casos_demo.json` (10 mensagens), enviado em "Enviar arquivo".

| Mensagens | Esperado | O que apareceu | Bateu? |
|---|---|---|---|
| DEMO_04 (vazia) e DEMO_05 (repetida da DEMO_02) | Saem na limpeza e não contam na análise | Constam na lista "Conferir o que a comunidade escreveu" (10 encontradas), mas o resumo mostra **8** mensagens analisadas e as duas **não aparecem** em "De quais mensagens pode ter vindo" da FAQ | Sim |
| DEMO_01 e DEMO_09 (depoimentos) | Post e newsletter | Post (2 origens) citando Mariana e Rafael. Newsletter com as duas entre as origens. | Sim |
| DEMO_03 e DEMO_08 (feedbacks) | Só newsletter | Aparecem na newsletter (4 origens) e não no post (2 origens) | Sim |
| DEMO_02, DEMO_06, DEMO_07 e DEMO_10 (dúvidas técnicas) | Candidatas à FAQ | Origens da FAQ (4): exatamente essas quatro | Sim |

O sistema devolve **uma** sugestão de FAQ por lote (decisão 4 de [`regras_roteamento.md`](regras_roteamento.md)). Neste lote a IA escolheu a dúvida sobre a API da Groq no OCI. Por isso "candidata à FAQ" quer dizer que a mensagem **pode** alimentar a FAQ, e não que cada uma gera uma FAQ própria. É o mesmo motivo de a DEMO_06, que é candidata no lote, ficar sem FAQ quando testada sozinha.

No resumo do lote apareceram 8 mensagens analisadas, clima "Positivo" e 3 itens aprovados na revisão.

<details>
<summary>Prints: lote completo (10)</summary>

![Arquivo casos_demo.json anexado, com 10 mensagens encontradas](evidencias/interface/parteC_lote_01.png)

![Lista das 10 mensagens (DEMO_04 sem texto; DEMO_05 igual à DEMO_02)](evidencias/interface/parteC_lote_02.png)

![Topo da revisão e post gerado](evidencias/interface/parteC_lote_03.png)

![Post aprovado](evidencias/interface/parteC_lote_04.png)

![Newsletter aprovada, com "De quais mensagens pode ter vindo" ainda fechado (post com 2, newsletter com 4)](evidencias/interface/parteC_lote_05.png)

![FAQ aprovada (4 origens, fechado)](evidencias/interface/parteC_lote_06.png)

![Resumo (8 mensagens analisadas), revisão (3 aprovados) e post em "Prontos para publicar"](evidencias/interface/parteC_lote_07.png)

![Newsletter e FAQ em "Prontos para publicar"](evidencias/interface/parteC_lote_08.png)

![Origens da newsletter abertas: DEMO_09, DEMO_01, DEMO_03 e DEMO_08](evidencias/interface/parteC_lote_09.png)

![Origens da FAQ abertas: DEMO_02, DEMO_06, DEMO_07 e DEMO_10 (sem DEMO_04 e DEMO_05)](evidencias/interface/parteC_lote_10.png)

</details>

## Limitações e observações

1. **A tela não mostra quais mensagens foram descartadas na limpeza.** A lista "Conferir o que a comunidade escreveu" traz as 10 mensagens, e o resumo traz 8. A prova de que DEMO_04 e DEMO_05 ficaram de fora é indireta: a contagem (10 contra 8) e a ausência delas nas listas de origem (print `parteC_lote_10.png`).
2. **O aviso de FAQ vazia é sempre o mesmo.** Quando não há FAQ, a tela diz *"Nenhuma dúvida técnica neste período, então não há sugestão de FAQ."* Isso é verdade quando não há dúvidas técnicas, mas na DEMO_06 há uma dúvida técnica, só vaga demais para virar FAQ. O resultado está correto (sem FAQ); a frase é que é genérica. Fica como melhoria futura.
3. **O texto gerado muda a cada geração.** A própria tela avisa. No exemplo de estágio, os prints 07 e 08 são de uma segunda geração (11:11), e a newsletter ficou com "depois de publicar" em vez de "após publicar".
4. **A revisão humana existe por isso.** No exemplo de Conquistas, a mensagem diz que o projeto "fez toda a diferença na entrevista técnica", e o texto gerado diz que ele "foi o assunto da entrevista técnica". No de estágio, o post saiu com "Qual projeto seu pode abrir portas?". Em ambos, a pessoa que revisa corrige antes de aprovar. Os prints mostram o que a ferramenta gerou, sem retoque.
5. **Teste manual.** Não há automação para a tela com a Groq real. Os testes automáticos (`python -m unittest discover -s tests -t .`) cobrem a lógica sem rede, em `tests/`.

## Como repetir

1. Na raiz do projeto, com o `.env` configurado: `streamlit run interface_streamlit.py`.
2. **Parte A:** em "Exemplo do projeto", escolha o exemplo e clique em **Gerar conteúdo**.
3. **Parte B:** em "Enviar arquivo", anexe um arquivo de `evidencias/interface/arquivos_de_teste/` por vez e clique em **Gerar conteúdo**.
4. **Parte C:** em "Enviar arquivo", anexe `dados/casos_demo.json`.
5. Compare com as colunas "Esperado" das tabelas. Não use o período `Semana_04`.

## Arquivos

* Prints: [`evidencias/interface/`](evidencias/interface/) (`parteA_*`, `parteB_*`, `parteC_*`).
* Arquivos dos casos sujos: [`evidencias/interface/arquivos_de_teste/`](evidencias/interface/arquivos_de_teste/) (`teste_DEMO_04_vazia.json`, `teste_DEMO_05_repetida.json`, `teste_DEMO_06_digitacao.json`).
