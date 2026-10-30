# Exemplos de Transformação (antes → depois)

Projeto: G10 Brasil · Equipe 12 · CommunityLab

Este documento mostra três transformações reais feitas pelo motor: mensagens da comunidade entram, e ativos de distribuição prontos para curadoria saem.

> **Dados simulados.** Todas as mensagens vêm de [`dados/mensagens_exemplo.json`](../dados/mensagens_exemplo.json), [`dados/dataset_simulado.json`](../dados/dataset_simulado.json) ou [`dados/caso_proposta_estagio.json`](../dados/caso_proposta_estagio.json). Nomes e relatos são fictícios (veja [`dataset_simulado.md`](dataset_simulado.md)), e os textos gerados não devem ser publicados como se fossem fatos reais.
>
> **Saídas reais, não editadas.** Foram geradas em 25/10/2026 com `openai/gpt-oss-120b` (Groq), pelo comando `python -m src.pipeline`. A LLM varia entre execuções: uma nova execução pode gerar textos diferentes. Por isso existe a etapa de curadoria humana antes de publicar.

## Exemplo 1: depoimento vira post de LinkedIn e destaque de newsletter

**Como reproduzir:** `python -m src.pipeline dados/mensagens_exemplo.json` (lote de 5 interações; abaixo, as que originaram os ativos).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Mariana Souza | `#conquistas-e-vagas` | `depoimento` | Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA! O projeto do curso de LangChain e OCI que construí no portfólio fez toda a diferença na entrevista técnica. |
| Rafael Lima | `#projetos-alunos` | `entrega_projeto` | Concluí o deploy do meu assistente inteligente usando Streamlit Cloud e ChromaDB. Deixei o link no repositório do GitHub para quem quiser testar. |

**Análise do lote:** sentimento predominante `Altamente Positivo`; tópicos: Conquista de vaga, Projetos com LangChain e OCI, Engenharia de prompts e automação, Deploy de assistente inteligente, Dúvidas técnicas sobre LangGraph e OCI.

**Ativo 1: `post_linkedin`**

- **Título:** De estudante a desenvolvedora júnior de IA: sucesso com projetos práticos!
- **Copy:** 🎉 A Mariana acabou de ser aprovada no processo seletivo para Desenvolvedora Júnior de IA! Seu portfólio com LangChain e OCI fez a diferença. 🚀 Parabéns a todos que estão construindo projetos reais e colocando em prática o que aprendemos. #IA #LangChain #OCI #CarreiraTech #CommunityLab
- **Canal recomendado:** LinkedIn Oficial · **Potencial de engajamento:** Alto

**Ativo 2: `destaque_newsletter_semanal`**

- **Seção:** Vitória da Semana
- **Chamada:** Alunos conquistam vagas e lançam projetos inovadores
- **Resumo:** Mariana foi aprovada como desenvolvedora júnior de IA usando seu projeto LangChain/OCI, e Rafael compartilhou o deploy de um assistente inteligente no Streamlit Cloud.

**O que este exemplo mostra:** uma conquista e uma entrega de projeto viram dois formatos diferentes (post inspirador e chamada curta) na mesma execução.

## Exemplo 2: proposta de estágio não vira contratação

**Como reproduzir:** `python -m src.pipeline dados/caso_proposta_estagio.json` (lote de 2 interações, as mensagens MSG_010 e MSG_016 do dataset simulado).

**Mensagens originais**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Gustavo Prado | `#conquistas-e-vagas` | `depoimento` | Recebi uma proposta para estágio em engenharia de dados! Tudo começou quando publiquei no GitHub meu pipeline com bucket na nuvem. Vale muito mostrar o que a gente constrói. |
| Henrique Barros | `#conquistas-e-vagas` | `depoimento` | Fechei meu primeiro freela de automação! Usei n8n com Webhook para ligar um formulário a uma planilha. O cliente adorou. |

**Análise do lote:** sentimento predominante `Positivo`; tópicos: Estágio em Engenharia de Dados, Freelance de Automação.

**Ativo 1: `post_linkedin`**

- **Título:** Conquistas que inspiram: estágio em dados e primeiro freela de automação
- **Copy:** 🚀 O Gustavo compartilhou que recebeu uma proposta de estágio em Engenharia de Dados após publicar seu pipeline no GitHub. O Henrique celebrou o primeiro freela de automação usando n8n e Webhook, encantando o cliente. Histórias como essas mostram o poder de transformar projetos pessoais em oportunidades reais. #EngenhariaDeDados #Automação #Freelance #ComunidadeONE #CarreiraTech

**Ativo 2: `destaque_newsletter_semanal`**

- **Chamada:** Estágio em Dados e Primeiro Freela de Automação
- **Resumo:** Gustavo recebeu proposta de estágio em Engenharia de Dados e Henrique fechou seu primeiro projeto de automação com n8n, provando que compartilhar resultados gera oportunidades.

**Ativo 3: `sugestao_conteudo_faq`:** `null`

**O que este exemplo mostra:**

1. **Fidelidade aos fatos:** quem *recebeu uma proposta* não aparece como contratado, e quem *fechou* um freela continua com a conquista plena. O prompt tem regras contra inflar conquistas (em testes anteriores, sem essa regra, a LLM chegou a escrever que o Gustavo "garantiu" o estágio).
2. **Sem material, sem ativo:** como o lote não tinha nenhuma pergunta técnica, a sugestão de FAQ veio `null`, em vez de um conteúdo inventado.

## Exemplo 3: dúvida técnica vira sugestão de FAQ

**Como reproduzir:** `python -m src.pipeline dados/dataset_simulado.json` (47 interações válidas; abaixo, a que originou o FAQ).

**Mensagem original**

| Autor | Canal | Tipo | Texto |
| :--- | :--- | :--- | :--- |
| Rafael Tavares | `#duvidas-langgraph` | `pergunta_tecnica` | Alguém sabe como configurar um retry no nó condicional do LangGraph quando a LLM devolve um JSON quebrado? Estou tentando com um router, mas ele só tenta uma vez. |

**Ativo gerado: `sugestao_conteudo_faq`**

- **Tema:** Dica Rápida: Configurando retry no LangGraph para JSON quebrado
- **Origem:** Pergunta de Rafael Tavares sobre retry no nó condicional do LangGraph
- **Status:** `encaminhado_para_mentoria`

**O que este exemplo mostra:** uma dúvida recorrente vira um tópico de FAQ rastreável até a mensagem de origem e já encaminhado para a mentoria.

## Limites conhecidos

- A análise (sentimento e tópicos) é do **lote inteiro**, não de cada mensagem.
- O modelo pode exagerar ou generalizar mesmo com as regras do prompt. Exemplos observados nos testes: dizer que um projeto "foi decisivo" na entrevista quando a mensagem dizia que foi "o assunto principal", ou usar "vários" sem base. Revise antes de publicar.
- Mensagens de dificuldade pessoal servem só para o sentimento: o prompt manda não citar o nome do autor em conteúdo público.
