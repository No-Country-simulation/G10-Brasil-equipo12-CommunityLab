# Exemplos de Transformação (antes → depois)

Projeto: G10 Brasil · Equipe 12 · CommunityLab

Este documento mostra três transformações reais feitas pelo motor: mensagens da comunidade entram, e ativos de distribuição prontos para curadoria saem.

> **Dados simulados.** Cada exemplo tem um arquivo de entrada próprio e congelado em `dados/` ([`caso_conquista.json`](../dados/caso_conquista.json), [`caso_proposta_estagio.json`](../dados/caso_proposta_estagio.json) e [`caso_duvida_tecnica.json`](../dados/caso_duvida_tecnica.json)). Nomes e relatos são fictícios (veja [`dataset_simulado.md`](dataset_simulado.md)), e os textos gerados não devem ser publicados como se fossem fatos reais.
>
> **Saídas reais, não editadas.** Foram geradas em 16 e 17/11/2026, com o modelo `openai/gpt-oss-120b` (Groq), pelo comando `python -m src.pipeline`, **sem** `--oci` (por isso `armazenamento_oci.status` ficou `pendente_upload` nos três). Os exemplos 1 e 2 vieram da branch `fix/exemplo-linkedin-linguagem-neutra` (commit `f76d020`, PR #71), que corrige o guia do LinkedIn; o exemplo 3 veio da `main` no commit `63e3fcd` (nesse lote só o FAQ é pedido, então o guia do LinkedIn nem é usado). A LLM varia entre execuções: uma nova execução pode gerar textos diferentes. Por isso existe a etapa de curadoria humana antes de publicar. A seção "Como estas saídas foram obtidas", no fim, conta quantas execuções foram feitas.
>
> **Entradas congeladas.** O teste [`tests/test_exemplos_demo.py`](../tests/test_exemplos_demo.py) garante que cada arquivo de entrada continua com os mesmos textos e o mesmo roteamento esperado. Se alguém alterar uma entrada, o teste falha e este documento precisa ser regenerado.

## Exemplo 1: depoimento e entrega de projeto viram post de LinkedIn e destaque de newsletter

**Como reproduzir:** `python -m src.pipeline dados/caso_conquista.json` (lote de 2 interações).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Mariana Souza | `#conquistas-e-vagas` | `depoimento` | Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA! O projeto do curso de LangChain e OCI que construí no portfólio fez toda a diferença na entrevista técnica. |
| Rafael Lima | `#projetos-alunos` | `entrega_projeto` | Concluí o deploy do meu assistente inteligente usando Streamlit Cloud e ChromaDB. Deixei o link no repositório do GitHub para quem quiser testar. |

**Análise do lote:** sentimento predominante `Altamente Positivo`; tópicos: processo seletivo, deploy de assistente inteligente, LangChain e OCI.

**Ativo 1: `post_linkedin`**

- **Título:** Mariana passa em processo seletivo para Desenvolvedora Júnior de IA e Rafael conclui deploy de assistente inteligente
- **Copy:**

  > A Mariana Souza passou no processo seletivo para Desenvolvedora Júnior de IA. 🎉
  >
  > Ela contou que o projeto do curso de LangChain e OCI que construiu no portfólio fez toda a diferença na entrevista técnica.
  >
  > Rafael Lima concluiu o deploy do seu assistente inteligente usando Streamlit Cloud e ChromaDB, deixando o link no repositório do GitHub para quem quiser testar.
  >
  > Parabéns!
  >
  > Qual projeto seu está pronto para ser mostrado? Compartilhe nos comentários.
  >
  > #CarreiraTech #LangChain #OCI #Streamlit #ChromaDB

- **Canal recomendado:** LinkedIn Oficial · **Potencial de engajamento:** Alto

**Ativo 2: `destaque_newsletter_semanal`**

- **Seção:** Vitória da Semana
- **Chamada:** Mariana passa em processo seletivo para Desenvolvedora Júnior de IA
- **Resumo:** Mariana Souza passou no processo seletivo para Desenvolvedora Júnior de IA, destacando que o projeto de LangChain e OCI foi decisivo na entrevista. Rafael Lima concluiu o deploy do assistente inteligente com Streamlit Cloud e ChromaDB, disponibilizando o link no GitHub. Quer mostrar seu projeto? Compartilhe no canal #projetos-alunos.

**Ativo 3: `sugestao_conteudo_faq`:** `null`

**O que este exemplo mostra:** uma conquista e uma entrega de projeto viram dois formatos diferentes (post inspirador e chamada curta) na mesma execução, e, como o lote não tinha pergunta técnica, a sugestão de FAQ veio `null`.

## Exemplo 2: proposta de estágio não vira contratação

**Como reproduzir:** `python -m src.pipeline dados/caso_proposta_estagio.json` (lote de 2 interações, as mensagens MSG_010 e MSG_016 do dataset simulado).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Gustavo Prado | `#conquistas-e-vagas` | `depoimento` | Recebi uma proposta para estágio em engenharia de dados! Tudo começou quando publiquei no GitHub meu pipeline com bucket na nuvem. Vale muito mostrar o que a gente constrói. |
| Henrique Barros | `#conquistas-e-vagas` | `depoimento` | Fechei meu primeiro freela de automação! Usei n8n com Webhook para ligar um formulário a uma planilha. O cliente adorou. |

**Análise do lote:** sentimento predominante `Altamente Positivo`; tópicos: estágio em engenharia de dados, freela de automação.

**Ativo 1: `post_linkedin`**

- **Título:** Uma proposta de estágio em dados e um primeiro freela de automação
- **Copy:**

  > Duas histórias da nossa comunidade. 🚀
  >
  > Gustavo Prado contou que recebeu uma proposta de estágio em engenharia de dados. Tudo começou quando publicou no GitHub um pipeline com bucket na nuvem.
  >
  > Henrique Barros contou que fechou seu primeiro freela de automação, usando n8n com Webhook para ligar um formulário a uma planilha. O cliente adorou.
  >
  > Parabéns!
  >
  > Qual projeto seu merece ser mostrado no GitHub? Conte nos comentários.
  >
  > #EngenhariaDeDados #Automação #CarreiraTech

- **Canal recomendado:** LinkedIn Oficial · **Potencial de engajamento:** Alto

**Ativo 2: `destaque_newsletter_semanal`**

- **Seção:** Vitória da Semana
- **Chamada:** Gustavo recebe proposta de estágio em engenharia de dados
- **Resumo:** Gustavo Prado recebeu uma proposta de estágio em engenharia de dados depois de publicar no GitHub um pipeline com bucket na nuvem. Henrique Barros fechou seu primeiro freela de automação, usando n8n com Webhook para ligar um formulário a uma planilha. Quer mostrar seu projeto? Compartilhe no canal #conquistas-e-vagas.

**Ativo 3: `sugestao_conteudo_faq`:** `null`

**O que este exemplo mostra:**

1. **Fidelidade aos fatos:** quem *recebeu uma proposta* não aparece como contratado, e quem *fechou* um freela continua com a conquista plena. O prompt tem regras contra inflar conquistas (em testes anteriores, sem essa regra, a LLM chegou a escrever que o Gustavo "garantiu" o estágio).
2. **Sem material, sem ativo:** como o lote não tinha nenhuma pergunta técnica, a sugestão de FAQ veio `null`, em vez de um conteúdo inventado.
3. **Linguagem sem marca de gênero:** as mensagens do Gustavo e do Henrique não mostram gênero, e nesta execução o texto não usa "ele", "ela" nem artigo antes dos nomes. Nem sempre foi assim: veja "Como estas saídas foram obtidas".

## Exemplo 3: dúvida técnica vira sugestão de FAQ

**Como reproduzir:** `python -m src.pipeline dados/caso_duvida_tecnica.json` (lote de 1 interação, a mensagem MSG_002 do dataset simulado).

**Mensagem original**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Rafael Tavares | `#duvidas-langgraph` | `pergunta_tecnica` | Alguém sabe como configurar um retry no nó condicional do LangGraph quando a LLM devolve um JSON quebrado? Estou tentando com um router, mas ele só tenta uma vez. |

**Análise do lote:** sentimento predominante `Neutro`; tópicos: LangGraph, retry.

**Ativo gerado: `sugestao_conteudo_faq`**

- **Tema:** Dica Rápida: retry no nó condicional do LangGraph quando a LLM devolve JSON quebrado
- **Origem:** Dúvida de Rafael Tavares no canal #duvidas-langgraph
- **Status:** `encaminhado_para_mentoria`

**Ativos `post_linkedin` e `destaque_newsletter_semanal`:** `null`

**O que este exemplo mostra:**

1. **Rastreabilidade:** uma dúvida recorrente vira um tópico de FAQ ligado à mensagem de origem e já encaminhado para a mentoria.
2. **Roteamento por tipo:** uma `pergunta_tecnica` não gera post nem newsletter. Só o FAQ é preenchido.

## Como estas saídas foram obtidas

Para não parecer que escolhemos só o melhor resultado, aqui está o que aconteceu em cada execução. Todas foram feitas por Denilson Silva de Almeida, sem `--oci`.

| Exemplo | Execuções | O que aconteceu |
| :--- | :-: | :--- |
| 1 | 3 | 16/11 (`63e3fcd`): o post terminou com "Parabéns a todos!", contra a regra do guia. 17/11 (`9be88b1`): dentro da regra. 17/11 (`f76d020`): dentro da regra, e é a que está acima. |
| 2 | 5 | 16/11 (`63e3fcd`) e três execuções em 17/11 (`9be88b1`): em todas o post trouxe "Ele usou..." para o Henrique (e "Segundo ele..." para o Gustavo em três delas), sem que a mensagem mostrasse gênero. Causa: o Exemplo 2 do guia `prompts/linkedin.md` tinha essas mesmas formas, e a LLM copiava o exemplo. Depois de corrigir o guia (PR #71, commit `f76d020`), a execução seguinte, em 17/11, saiu dentro da regra e é a que está acima. |
| 3 | 1 | 16/11 (`63e3fcd`): dentro do esperado. Entre `63e3fcd` e `9be88b1`, só mudaram README e documentos. |

"Dentro da regra" quer dizer: o post usa só "Parabéns!", não usa "ele" nem "ela" para quem não mostrou gênero na própria mensagem, e não muda nenhum fato (proposta continua proposta). Os textos usados acima foram conferidos contra as mensagens originais. Isso mostra que a regra de linguagem neutra no prompt **não é uma garantia**: a revisão humana continua necessária.

## Limites conhecidos

- A análise (sentimento e tópicos) é do **lote inteiro**, não de cada mensagem.
- O modelo pode exagerar ou generalizar mesmo com as regras do prompt. Exemplos observados nos testes: dizer que um projeto "foi decisivo" na entrevista quando a mensagem dizia que foi "o assunto principal", ou usar "vários" sem base. Revise antes de publicar.
- Mensagens de dificuldade pessoal servem só para o sentimento: o prompt manda não citar o nome do autor em conteúdo público.
