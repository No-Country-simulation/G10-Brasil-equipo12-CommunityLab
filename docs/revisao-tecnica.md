# Revisão técnica — CommunityLab (G10 · Equipe 12)

Revisão de 23/10/2026, feita por Gabriel Maia com Claude, Codex e OpenCode.

## Resumo

O CommunityLab tem a estrutura certa (ingestão, limpeza, LLM, validação), mas no main as falhas da IA apareciam como sucesso, com texto inventado. Além disso, a saída não trazia cases de sucesso nem análise por mensagem. A branch `feat/revisao-pipeline-avaliacao` corrige os 14 problemas encontrados e completa os quatro ativos da proposta. Ela também traz um script de avaliação com 18 casos rotulados: depois das regras de conteúdo, a acurácia média ficou entre 88% e 90% pela API da NVIDIA, e os 84 testes passam.

- **Revisores:** Claude (Claude Code), Codex (GPT-6-Astra) e OpenCode (Gemini 4 Argon), primeiro de forma independente no main, depois revisando o trabalho uns dos outros.
- **Ainda falta:** validar com a Groq, o modelo do projeto. As rodadas usaram a API da NVIDIA e um modelo local, porque não havia chave da Groq disponível.
- **Próximo passo:** enviar a branch ao GitHub e abrir um Pull Request.

## Como o pipeline funciona hoje (main, commit b755eda)

O main tem um pipeline de 4 etapas em Python, rodado com `python -m src.teste_execucao`. Ele gera 1 post de LinkedIn, 1 destaque de newsletter e 1 sugestão de FAQ para o lote inteiro de mensagens.

1. `src/ingestao.py` lê as mensagens de um JSON ou CSV.
2. `src/limpeza.py` normaliza espaços e descarta mensagens vazias.
3. `src/prompts.py` monta o prompt e `src/teste_execucao.py` chama a Groq (`openai/gpt-oss-120b`) pedindo um JSON fixo.
4. `src/validacao.py` preenche com valores padrão qualquer campo que o modelo não devolver.

| Item | README promete | Código no main faz |
| --- | --- | --- |
| Entrada | Discord e PDFs | Arquivo JSON ou CSV local |
| Modelo | Gemini + LangGraph | Groq (`openai/gpt-oss-120b`), sem LangGraph |
| Classificação | Depoimento, dúvida técnica, feedback, por mensagem | O `tipo` já chega pronto na entrada; a saída não tem nada por mensagem |
| Armazenamento | Gravação na Oracle Cloud (OCI) | Nenhum upload; o bloco `armazenamento_oci` é um texto fixo que o modelo devolve |
| Ativos | Posts, newsletters, cases de sucesso, FAQs | Post, newsletter e FAQ; cases de sucesso não existem |

## Problemas encontrados e correções

Três revisões independentes do main (Claude, Codex e OpenCode) acharam 14 problemas, e todos foram corrigidos na branch `feat/revisao-pipeline-avaliacao`. Os dois mais graves: uma falha da IA aparecia como sucesso com texto inventado, e o validador quebrava quando o modelo devolvia um campo `null`.

| # | Problema | Onde | Achado por | Correção |
| --- | --- | --- | --- | --- |
| 1 | Falha da IA vira `status: sucesso` com sentimento "Altamente Positivo" e textos genéricos | `validacao.py`, `teste_execucao.py` | Claude, Codex, OpenCode | `status` passa a ser `sucesso`, `parcial` ou `erro`, com a lista de `avisos`; nada é inventado |
| 2 | Validador quebra (`AttributeError`) se o modelo devolve `"resumo_comunidade": null` ou um ativo `null` | `validacao.py` | Codex, OpenCode | Cada nível do JSON tem o tipo conferido |
| 3 | Escala de sentimento diferente no prompt, na validação e nos docs | `prompts.py`, `validacao.py`, `docs/` | Claude, Codex, OpenCode | Lista única em `src/esquema.py`, usada no prompt e validada na saída |
| 4 | Saída só agregada, mas os casos de teste são por mensagem; a limpeza descartava o `id` | `limpeza.py`, `prompts.py` | Claude, Codex, OpenCode | Nova lista `analise_interacoes`, uma entrada por `id`; o `id` é mantido ou gerado (`MSG_001`) |
| 5 | O `tipo` ia pronto para o modelo, então não havia classificação de verdade | `prompts.py` | Claude, Codex | O `tipo` não é mais enviado; o modelo classifica |
| 6 | Total de mensagens processadas podia virar 1 ou o número que o modelo inventasse | `teste_execucao.py`, `validacao.py` | Claude, Codex, OpenCode | Calculado pelo código a partir das mensagens enviadas |
| 7 | Ingestão quebrava com JSON em lista ou `interacoes: null`; CSV sem coluna `texto` era descartado em silêncio | `ingestao.py`, `limpeza.py` | Codex | Estrutura conferida, com erro claro; o modelo não é chamado sem mensagens |
| 8 | Mensagens podiam dar ordens ao modelo (prompt injection) | `prompts.py` | Codex | Regra explícita no prompt; o case cita os ids de origem. Reduz o risco, não elimina |
| 9 | O bloco `armazenamento_oci` era escrito pelo modelo | `prompts.py` | Claude, Codex | Preenchido pelo código, com `status: pendente_upload` |
| 10 | Erros terminavam com código de saída 0 | `teste_execucao.py`, `teste_groq.py` | Codex | Saída 1 quando falha |
| 11 | `teste_groq.py` chamava a API só de ser importado | `teste_groq.py` | Codex | Execução protegida por `if __name__ == "__main__"` |
| 12 | Dependências não declaradas | raiz | Claude | `requirements.txt` e `requirements-dev.txt` |
| 13 | Bloco do diagrama no README fechado com `'''` em vez de crases | `README.md` | Claude | Corrigido |
| 14 | DEMO_03 tinha o tópico "Sprint 1" no JSON, mas não na tabela | `dados/`, `docs/` | Codex | Tabela alinhada |

Depois das correções, houve uma revisão cruzada: o Codex revisou o diff e o OpenCode revisou o script de avaliação. Eles acharam mais 8 pontos, todos corrigidos e cobertos por testes. Entre eles: listas malformadas aceitas sem aviso, resposta sem conteúdo útil classificada como `parcial` em vez de `erro`, case de sucesso sem as mensagens de origem e a comparação de tópicos contando "IA" dentro de "Mentoria".

## O que foi adicionado para completar a proposta

A saída agora cobre os quatro ativos da proposta e traz uma análise para cada mensagem. A estrutura do PDF oficial foi mantida: só entraram campos novos, nenhum foi renomeado.

- **Análise por mensagem** (`analise_interacoes`): para cada `id`, o modelo devolve tipo, sentimento, de 1 a 4 tópicos, relevância e para quais ativos a mensagem serve de matéria-prima.
- **Case de sucesso** (`case_sucesso`): título, desafio, solução, resultado e os ids das mensagens usadas. Se não houver história de sucesso nas mensagens, o modelo devolve `null` em vez de inventar.
- **FAQ com pergunta**: o campo `pergunta` traz a dúvida reescrita como pergunta de FAQ. A resposta continua com a mentoria, porque o modelo poderia inventar uma solução técnica.
- **Valores aceitos num lugar só** (`src/esquema.py`): tipos, escala de sentimento, ativos e relevâncias. O prompt, a validação e a avaliação usam a mesma lista.
- **Pipeline reutilizável** (`src/pipeline.py`): `executar_pipeline()` faz limpeza, chamada à LLM e validação, e aceita uma LLM falsa nos testes.
- **Provedor de LLM configurável** (`src/llm.py`): Groq continua o padrão. Com `LLM_PROVIDER=nvidia`, usa a API da NVIDIA ([build.nvidia.com](https://build.nvidia.com), modelo padrão `openai/gpt-oss-20b`). Com `LLM_PROVIDER=ollama`, roda com um modelo local, sem chave de API.
- **Testes automatizados** (`tests/`): rodam sem chamar a LLM.
- **README**: correção do diagrama, tabela do que já está implementado, escolha da LLM e passo a passo para rodar.
- **Padronização**: código formatado com ruff, configuração do pytest em `pyproject.toml` e GitHub Actions rodando lint e testes em cada Pull Request.

## Avaliação automática: primeira rodada

Em 6 rodadas sobre `dados/casos_demo.json`, com dois modelos, a acurácia média ficou entre 76% e 87%. O tipo de mensagem acertou em todas. O sentimento da DEMO_02 errou nas 6, sempre com a mesma resposta, o que aponta para o rótulo esperado e não para o modelo (próxima seção).

O script `src/avaliacao.py` roda o pipeline nos casos de demonstração e compara cada resposta com os campos `*_esperado` do JSON. Os 84 testes automatizados passam e não chamam a LLM.

```bash
python -m src.avaliacao                               # chama a LLM configurada no .env
python -m src.avaliacao --salvar saidas/r1.json       # guarda o resultado do pipeline
python -m src.avaliacao --resultado saidas/r1.json    # reavalia sem chamar a LLM
python -m src.avaliacao --min-acuracia 0.8            # sai com código 1 abaixo de 80%
python -m pytest                                      # testes, sem LLM
```

Acertos por caso nas 4 rodadas com um modelo local via Ollama (Ornith 1.5 35B):

| Caso | Tipo | Sentimento | Relevância | Ativo | Tópicos encontrados |
| --- | --- | --- | --- | --- | --- |
| DEMO_01 depoimento | 4 de 4 | 4 de 4 | 4 de 4 | 4 de 4 | 100%, 67%, 100%, 67% |
| DEMO_02 dúvida técnica | 4 de 4 | 0 de 4: sempre "Neutro", esperado "Negativo" | 4 de 4 | 4 de 4 | 67%, 100%, 100%, 67% |
| DEMO_03 feedback | 4 de 4 | 4 de 4 | 3 de 4 | 0 de 4: recomendou FAQ ou nada, esperado newsletter | 67% nas 4 |

Acertos por caso nas 2 rodadas com `openai/gpt-oss-20b` pela API da NVIDIA (acurácia média de 78% e 87%):

| Caso | Tipo | Sentimento | Relevância | Ativo | Tópicos encontrados |
| --- | --- | --- | --- | --- | --- |
| DEMO_01 depoimento | 2 de 2 | 1 de 2: uma vez "Positivo" | 2 de 2 | 2 de 2 | 33%, 33% |
| DEMO_02 dúvida técnica | 2 de 2 | 0 de 2: sempre "Neutro", esperado "Negativo" | 2 de 2 | 2 de 2 | 100%, 100% |
| DEMO_03 feedback | 2 de 2 | 2 de 2 | 2 de 2 | 2 de 2: recomendou newsletter | 33%, 67% |

- Uma rodada extra incluiu os casos "sujos" do PR #12 aberto. A mensagem vazia foi descartada antes da LLM. A mensagem com gíria e a com erros de digitação foram classificadas como dúvida técnica, como esperado.
- Em 2 das 4 rodadas o status saiu `parcial`: o case de sucesso veio sem desafio e sem solução. A mensagem da DEMO_01 não traz essas informações, então o modelo deixou em branco em vez de inventar, e a validação avisou. Com a mensagem mais completa de `mensagens_exemplo.json`, o case saiu inteiro, com desafio, solução e resultado tirados da mensagem.
- O texto gerado precisa de revisão humana. Pela API da NVIDIA, um post de LinkedIn saiu em primeira pessoa, como se a própria Mariana escrevesse, e outro afirmou que "mentoria e networking ajudaram", o que a mensagem não diz.
- Na conta usada, o Nemotron Super não estava liberado e o Nemotron Ultra devolveu JSON inválido. Por isso o padrão ficou `openai/gpt-oss-20b`.
- Falta validar com a Groq (`openai/gpt-oss-120b`), que é o modelo do projeto. Com a `GROQ_API_KEY` no `.env`, basta rodar `python -m src.avaliacao`.

## Segunda rodada: mais casos e regras de conteúdo

O prompt ganhou duas regras: escrever post, newsletter e case em terceira pessoa e não atribuir causas que a mensagem não diz. Com elas, os problemas de conteúdo caíram e a acurácia subiu, medidos pela API da NVIDIA (`openai/gpt-oss-20b`).

- **Casos de avaliação** (`dados/casos_avaliacao.json`): 18 mensagens cobrindo depoimentos, dúvidas com e sem frustração, feedbacks, entregas, saudação, venda, uma tentativa de dar ordens ao sistema e uma mensagem vazia. Os critérios estão em `docs/criterios_rotulagem.md`. O Codex rotulou as mensagens às cegas e concordou em 67 de 68 rótulos; os 2 casos discutíveis foram ajustados.
- **Verificação de conteúdo:** a avaliação aponta marcas comuns de primeira pessoa do singular fora de aspas e termos proibidos (`nao_deve_conter`) no post, na newsletter e no case. É uma heurística revisada pelo Codex: pega os casos observados, mas verbos fora da lista e sinônimos dos termos proibidos passam despercebidos.
- **Respostas cortadas:** com o limite de 4.096 tokens, o `gpt-oss-20b` gastava quase tudo raciocinando e o JSON vinha cortado em lotes de 17 mensagens. O limite subiu para 16.384, e as três integrações agora avisam "resposta cortada pelo limite de tokens" em vez de "JSON inválido".
- **Tempo de espera:** uma rodada passou de 180 segundos no endpoint gratuito da NVIDIA. O limite subiu para 300 segundos.

| Medida (NVIDIA, `gpt-oss-20b`) | Antes das regras | Depois das regras |
| --- | --- | --- |
| Rodadas com problema de conteúdo, casos de demonstração | 3 de 6 | 1 de 6 |
| Rodadas com post em primeira pessoa | 2 de 6 | 0 de 6 |
| Acurácia média, 18 casos (3 rodadas) | 83%, 85%, 86% | 88%, 89%, 90% |
| Sentimento, 18 casos | 59% a 65% | 76% a 82% |
| Relevância, 18 casos | 71% a 88% | 88% a 100% |

- O problema que restou foi o post dizer que a vaga veio "graças ao aprendizado e networking na comunidade", o que a mensagem não diz. O exemplo de JSON do prompt contém `encaminhado_para_mentoria`, o que pode puxar o modelo para esse assunto.
- A melhora de sentimento e relevância se repetiu nas 3 rodadas, mas as regras novas não falam desses campos. A explicação mais provável é o modelo ficar mais literal; com 3 rodadas, não dá para ter certeza.
- Os erros de sentimento que restam são de intensidade (Muito positivo contra Positivo). Colocar no prompt as definições de `docs/criterios_rotulagem.md` deve ajudar, mas isso depende de o time aprovar os critérios.

## Decisões do time e próximos passos

Seis pontos dependem do time e não foram decididos no código:

1. **Rótulos esperados.** Uma dúvida sobre erro de autenticação é "Negativo" ou "Neutro"? E feedback vai para a newsletter (como em `docs/resultados_esperados.md`) ou para "Métricas Gerais" (como no diagrama do README)? O modelo da NVIDIA indicou newsletter e o local não, então vale descrever no prompt para que serve cada ativo.
2. **Nomes e voz em conteúdo público.** O post de LinkedIn gerado citou o nome completo de quem escreveu a mensagem e, numa rodada, falou em nome da pessoa. Antes de publicar de verdade, o sistema precisa de consentimento (LGPD) ou de uma regra como "só o primeiro nome".
3. **Campos novos no JSON.** `analise_interacoes`, `case_sucesso`, `pergunta` e `avisos` são adições ao formato do PDF oficial. Confirmar se o PDF permite.
4. **`tipo` fora do prompt.** A classificação agora é feita pelo modelo. Se o time quiser usar o canal ou o tipo informado como dica, dá para voltar a enviar.
5. **PR #12 (dados sujos).** Ele foi criado sobre uma versão antiga de `casos_demo.json` e vai conflitar. O id `"DEMO 04"` tem espaço, e a limpeza ainda não remove mensagens duplicadas.
6. **Status da FAQ.** O valor `encaminhado_para_mentoria` vem do PDF, mas o sistema não encaminha nada para mentores. Vale trocar por algo como `pendente_mentoria` até existir esse fluxo, como já é feito com `pendente_upload` no OCI.

Próximos passos sugeridos:

- [ ] Rodar `python -m src.avaliacao` com a chave da Groq
- [ ] Combinar no guia de commits os tipos `test:`, `style:` e `ci:`, que hoje não existem
- [ ] Revisar e aprovar `docs/criterios_rotulagem.md`; se aprovado, colocar as definições de sentimento e relevância no prompt e medir de novo
- [ ] Aumentar ainda mais os casos: com 17 mensagens, cada erro ainda muda a acurácia de um campo em 6 pontos
- [ ] Prever revisão humana dos ativos antes de qualquer publicação
- [ ] Implementar Discord, PDF, LangGraph e upload no OCI, ou tirar do README o que não vai entrar no hackathon
