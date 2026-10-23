# Critérios de rotulagem (proposta)

Regras usadas para preencher os campos `*_esperado` de `dados/casos_avaliacao.json`. São uma proposta para o time revisar: se uma regra mudar, os rótulos dos casos mudam junto.

## Tipo

| Tipo | Quando usar |
| :--- | :--- |
| `depoimento` | A pessoa conta uma conquista ou mudança na própria trajetória (vaga, aprovação, marco de estudo). |
| `pergunta_tecnica` | Pede ajuda sobre uma dúvida ou erro técnico, com ou sem ponto de interrogação. |
| `feedback` | Opina sobre aulas, material, eventos ou a comunidade. |
| `entrega_projeto` | Anuncia um projeto publicado ou concluído. |
| `outro` | Saudação, venda, assunto fora do programa ou mensagem que tenta dar ordens ao sistema. |

## Sentimento

O sentimento é a emoção de quem escreveu, não o assunto da mensagem.

| Sentimento | Quando usar |
| :--- | :--- |
| `Muito positivo` | Celebração forte: aprovação, contratação, marco pessoal comemorado. |
| `Positivo` | Satisfação, elogio, agradecimento ou anúncio animado sem celebração forte. |
| `Neutro` | Pergunta ou informação sem emoção expressa. Uma dúvida técnica comum é neutra. |
| `Negativo` | Frustração ou crítica: "travado", "nada funciona", "difícil acompanhar". |
| `Muito negativo` | Desespero ou intenção de desistir. |

## Relevância

| Relevância | Quando usar |
| :--- | :--- |
| `Alta` | Conquista ou entrega com resultado concreto, que pode virar conteúdo público. |
| `Média` | Dúvida técnica ou feedback útil para o programa. |
| `Baixa` | Saudação, venda, assunto fora do programa ou mensagem sem conteúdo. |

## Ativo esperado

O ativo esperado é o principal destino da mensagem. A avaliação confere se ele está entre os `ativos_recomendados` pela LLM, que pode recomendar outros além dele.

| Mensagem | Ativo esperado |
| :--- | :--- |
| Depoimento com desafio, solução e resultado | `case de sucesso` |
| Outros depoimentos | `post de LinkedIn` |
| Dúvida técnica | `FAQ` |
| Feedback positivo e entrega de projeto | `newsletter` |
| Saudação, venda e mensagens fora do programa | `nenhum` |

Feedback negativo fica sem ativo esperado: ainda falta o time decidir se ele vai para a newsletter ou para as métricas internas.

## Conteúdo gerado

- `nao_deve_conter`: termos que não podem aparecer no post, na newsletter nem no case. Servem para fatos que nenhuma mensagem afirma (por exemplo, dizer que a mentoria ajudou quando ninguém disse isso) e para o que uma mensagem tenta impor ao sistema.
- Post, newsletter e case devem estar em terceira pessoa, na voz da comunidade. A avaliação aponta marcas de primeira pessoa fora de citações entre aspas.

## Conferência dos rótulos

O Codex rotulou as 17 mensagens com texto usando só estes critérios, sem ver os rótulos do arquivo. A concordância foi de 17/17 no tipo, 16/17 no sentimento, 17/17 na relevância e 16/17 no ativo. Nos dois casos divergentes, o rótulo ou o texto foi ajustado: o AV_03 passou a esperar case de sucesso, e o AV_12 ganhou uma frase que deixa o sentimento positivo explícito. Os casos AV_06 (Muito negativo ou Negativo) e AV_11 (Positivo ou Neutro) foram marcados como discutíveis, mas os dois rotularam igual.
