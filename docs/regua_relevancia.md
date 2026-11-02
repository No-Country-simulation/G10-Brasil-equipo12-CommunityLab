# Régua de relevância

Referência para classificar cada mensagem da comunidade em **Alta**, **Média** ou **Baixa** relevância para a geração de conteúdo. Os critérios qualitativos foram propostos pelo Tomaz; as faixas de pontuação ligam esses critérios ao cálculo de `src/relevancia.py` (0 a 100) e são valores propostos, sujeitos a ajuste do time.

| Faixa | Pontuação | Critério de entrada | O que o motor faz hoje |
| :--- | :-: | :--- | :--- |
| 🔴 **Alta** | 60 a 100 | Conquistas profissionais (contratação, aprovação em processo seletivo, proposta de estágio, freela fechado), depoimentos espontâneos de superação e projetos concluídos ou entregues, de preferência com detalhe | Entra primeiro na amostra enviada à LLM. A LLM pode gerar o post de LinkedIn e o destaque de newsletter |
| 🟡 **Média** | 25 a 59 | Dúvidas técnicas recorrentes (por exemplo, nós condicionais no LangGraph, erros na OCI, integração de APIs) e relatos curtos ou sem palavra-chave de impacto | Dúvidas técnicas podem virar sugestão de FAQ (o tema, sem a solução técnica), encaminhada para a mentoria |
| 🟢 **Baixa** | 0 a 24 | Saudações e agradecimentos, conversas fora do escopo técnico, feedbacks curtos, mensagens sem contexto | **Não é descartada**: continua no total de interações do lote e disputa as vagas da amostra no seu grupo. Só mensagens sem texto são descartadas, na limpeza |

## Como a pontuação é calculada

Soma de três partes, com teto de 100:

1. **Tipo da mensagem:** 40 pontos para depoimento ou entrega de projeto, 25 para dúvida técnica e 10 para as demais.
2. **Palavras-chave de impacto:** 15 pontos por palavra encontrada (por exemplo, "vaga", "estágio", "aprovada", "freela", "projeto", "deploy").
3. **Detalhe:** 20 pontos para relatos com mais de 100 caracteres.

## Pontos em aberto

- **Feedbacks com conteúdo** pontuam hoje 10, como uma conversa curta, e caem em Baixa. Se o time quiser que um feedback detalhado conte mais, a pontuação precisa mudar.
- **O motor ainda não devolve a faixa por mensagem.** A pontuação reordena as mensagens e escolhe a amostra, mas Alta, Média e Baixa não aparecem na resposta.
- **`potencial_engajamento`** (Alto, Médio ou Baixo) é outra coisa: é uma estimativa da LLM para o post de LinkedIn, e não vem desta régua.
