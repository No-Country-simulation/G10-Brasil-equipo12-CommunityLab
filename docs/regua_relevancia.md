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

## Limitações conhecidas

- **A negação não é tratada na pontuação.** A palavra-chave soma 15 pontos mesmo depois de "não". No dataset simulado, a `MSG_037` ("Ainda não é a vaga", sobre uma segunda etapa de processo seletivo) soma 90 pontos e empata em 1º lugar com a `MSG_001` (aprovação de fato), porque "vaga" e "processo seletivo" pontuam. Sem a palavra "vaga", ela somaria 75.
  - **Decisão (Sprint 3): manter assim, sem tratar negação no código.** Motivos: o caso afeta 1 das 47 mensagens do dataset depois da limpeza; a mensagem é um depoimento legítimo e já entra na amostra por mérito; a LLM mantém os fatos corretos (o checklist de fidelidade conferiu que proposta não vira contratação); e uma regra simples de negação em português pode penalizar frases que não negam a palavra-chave. Tratar a negação também tiraria a `MSG_037` da amostra de 10 (entraria a `MSG_021`), o que exigiria refazer a auditoria de fidelidade.
  - **Quando reconsiderar:** se lotes reais maiores mostrarem relatos melhores ficando de fora da amostra por causa de uma negação. Nesse caso, a melhoria deve vir com teste cobrindo a frase.
  - Detalhes da conferência: [`checklist-fidelidade.md`](checklist-fidelidade.md).
