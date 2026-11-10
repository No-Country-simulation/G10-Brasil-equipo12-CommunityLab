# Exemplos de Transformação (antes → depois)

Projeto: G10 Brasil · Equipe 12 · CommunityLab

Este documento mostra três transformações reais feitas pelo motor: mensagens da comunidade entram, e ativos de distribuição prontos para curadoria saem.

> **Dados simulados.** Cada exemplo tem um arquivo de entrada próprio e congelado em `dados/` ([`caso_conquista.json`](../dados/caso_conquista.json), [`caso_proposta_estagio.json`](../dados/caso_proposta_estagio.json) e [`caso_duvida_tecnica.json`](../dados/caso_duvida_tecnica.json)). Nomes e relatos são fictícios (veja [`dataset_simulado.md`](dataset_simulado.md)), e os textos gerados não devem ser publicados como se fossem fatos reais.
>
> **Saídas reais, não editadas.** Foram geradas em 09/11/2026, com a versão `53d1396` da branch `main` e o modelo `openai/gpt-oss-120b` (Groq), pelo comando `python -m src.pipeline`, **sem** `--oci` (por isso `armazenamento_oci.status` ficou `pendente_upload` nos três). A LLM varia entre execuções: uma nova execução pode gerar textos diferentes. Por isso existe a etapa de curadoria humana antes de publicar.
>
> **Entradas congeladas.** O teste [`tests/test_exemplos_demo.py`](../tests/test_exemplos_demo.py) garante que cada arquivo de entrada continua com os mesmos textos e o mesmo roteamento esperado. Se alguém alterar uma entrada, o teste falha e este documento precisa ser regenerado.

## Exemplo 1: depoimento e entrega de projeto viram post de LinkedIn e destaque de newsletter

**Como reproduzir:** `python -m src.pipeline dados/caso_conquista.json` (lote de 2 interações).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Mariana Souza | `#conquistas-e-vagas` | `depoimento` | Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA! O projeto do curso de LangChain e OCI que construí no portfólio fez toda a diferença na entrevista técnica. |
| Rafael Lima | `#projetos-alunos` | `entrega_projeto` | Concluí o deploy do meu assistente inteligente usando Streamlit Cloud e ChromaDB. Deixei o link no repositório do GitHub para quem quiser testar. |

**Análise do lote:** sentimento predominante `Altamente Positivo`; tópicos: Processo Seletivo, Deploy de Projeto.

**Ativo 1: `post_linkedin`**

- **Título:** Mariana aprovada em processo seletivo para Desenvolvedora Júnior de IA e Rafael conclui deploy de assistente inteligente
- **Copy:**

  > Duas conquistas da comunidade ONE G10. 🚀
  >
  > Mariana Souza foi aprovada no processo seletivo para Desenvolvedora Júnior de IA. Ela destacou que o projeto de LangChain e OCI do portfólio fez toda a diferença na entrevista técnica.
  >
  > Rafael Lima concluiu o deploy do seu assistente inteligente usando Streamlit Cloud e ChromaDB, disponibilizando o link no GitHub para testes.
  >
  > Parabéns a ambos!
  >
  > Qual foi a sua maior vitória esta semana? Compartilhe nos comentários.
  >
  > #CarreiraTech #LangChain #OCI #Streamlit #ChromaDB

- **Canal recomendado:** LinkedIn Oficial · **Potencial de engajamento:** Alto

**Ativo 2: `destaque_newsletter_semanal`**

- **Seção:** Vitória da Semana
- **Chamada:** Mariana é aprovada em processo seletivo para Desenvolvedora Júnior de IA
- **Resumo:** Mariana Souza contou que passou no processo seletivo para Desenvolvedora Júnior de IA, ressaltando que o projeto de LangChain e OCI foi decisivo na entrevista técnica. Rafael Lima também destacou a entrega do deploy do seu assistente inteligente com Streamlit Cloud e ChromaDB, disponibilizando o link no GitHub. Quer mostrar seu projeto? Compartilhe no canal #projetos-alunos.

**Ativo 3: `sugestao_conteudo_faq`:** `null`

**O que este exemplo mostra:** uma conquista e uma entrega de projeto viram dois formatos diferentes (post inspirador e chamada curta) na mesma execução, e, como o lote não tinha pergunta técnica, a sugestão de FAQ veio `null`.

## Exemplo 2: proposta de estágio não vira contratação

**Como reproduzir:** `python -m src.pipeline dados/caso_proposta_estagio.json` (lote de 2 interações, as mensagens MSG_010 e MSG_016 do dataset simulado).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Gustavo Prado | `#conquistas-e-vagas` | `depoimento` | Recebi uma proposta para estágio em engenharia de dados! Tudo começou quando publiquei no GitHub meu pipeline com bucket na nuvem. Vale muito mostrar o que a gente constrói. |
| Henrique Barros | `#conquistas-e-vagas` | `depoimento` | Fechei meu primeiro freela de automação! Usei n8n com Webhook para ligar um formulário a uma planilha. O cliente adorou. |

**Análise do lote:** sentimento predominante `Altamente Positivo`; tópicos: proposta de estágio, freela de automação.

**Ativo 1: `post_linkedin`**

- **Título:** Uma proposta de estágio em dados e um primeiro freela de automação
- **Copy:**

  > Duas histórias da nossa comunidade. 🚀
  >
  > O Gustavo Prado contou que recebeu uma proposta de estágio em engenharia de dados. Segundo ele, tudo começou quando publicou no GitHub um pipeline com bucket na nuvem.
  >
  > O Henrique Barros contou que fechou seu primeiro freela de automação. Ele usou n8n com Webhook para ligar um formulário a uma planilha, e o cliente adorou.
  >
  > Parabéns aos dois!
  >
  > Qual projeto seu merece ser mostrado no GitHub? Conte nos comentários.
  >
  > #EngenhariaDeDados #Automação #CarreiraTech

- **Canal recomendado:** LinkedIn Oficial · **Potencial de engajamento:** Alto

**Ativo 2: `destaque_newsletter_semanal`**

- **Seção:** Vitória da Semana
- **Chamada:** Gustavo recebe proposta de estágio em engenharia de dados
- **Resumo:** Gustavo Prado recebeu uma proposta de estágio em engenharia de dados depois de publicar no GitHub um pipeline com bucket na nuvem. Henrique Barros fechou seu primeiro freela de automação, usando n8n com Webhook para ligar um formulário a uma planilha. Compartilhe sua conquista em #conquistas-e-vagas.

**Ativo 3: `sugestao_conteudo_faq`:** `null`

**O que este exemplo mostra:**

1. **Fidelidade aos fatos:** quem *recebeu uma proposta* não aparece como contratado, e quem *fechou* um freela continua com a conquista plena. O prompt tem regras contra inflar conquistas (em testes anteriores, sem essa regra, a LLM chegou a escrever que o Gustavo "garantiu" o estágio).
2. **Sem material, sem ativo:** como o lote não tinha nenhuma pergunta técnica, a sugestão de FAQ veio `null`, em vez de um conteúdo inventado.

## Exemplo 3: dúvida técnica vira sugestão de FAQ

**Como reproduzir:** `python -m src.pipeline dados/caso_duvida_tecnica.json` (lote de 1 interação, a mensagem MSG_002 do dataset simulado).

**Mensagem original**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Rafael Tavares | `#duvidas-langgraph` | `pergunta_tecnica` | Alguém sabe como configurar um retry no nó condicional do LangGraph quando a LLM devolve um JSON quebrado? Estou tentando com um router, mas ele só tenta uma vez. |

**Análise do lote:** sentimento predominante `Neutro`; tópicos: LangGraph, retry, JSON quebrado.

**Ativo gerado: `sugestao_conteudo_faq`**

- **Tema:** Dica Rápida: retry no nó condicional do LangGraph quando a LLM devolve JSON quebrado
- **Origem:** Dúvida de Rafael Tavares no canal #duvidas-langgraph
- **Status:** `encaminhado_para_mentoria`

**Ativos `post_linkedin` e `destaque_newsletter_semanal`:** `null`

**O que este exemplo mostra:**

1. **Rastreabilidade:** uma dúvida recorrente vira um tópico de FAQ ligado à mensagem de origem e já encaminhado para a mentoria.
2. **Roteamento por tipo:** uma `pergunta_tecnica` não gera post nem newsletter. Só o FAQ é preenchido.

## Limites conhecidos

- A análise (sentimento e tópicos) é do **lote inteiro**, não de cada mensagem.
- O modelo pode exagerar ou generalizar mesmo com as regras do prompt. Exemplos observados nos testes: dizer que um projeto "foi decisivo" na entrevista quando a mensagem dizia que foi "o assunto principal", ou usar "vários" sem base. Revise antes de publicar.
- Mensagens de dificuldade pessoal servem só para o sentimento: o prompt manda não citar o nome do autor em conteúdo público.
