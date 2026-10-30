# 📊 Resultados Esperados dos Casos de Demonstração

Tabela de validação do comportamento esperado do pipeline para os casos de teste de [`dados/casos_demo.json`](../dados/casos_demo.json). Serve de "gabarito": depois de rodar o motor, comparamos o que a IA devolveu com o que está aqui.

A tabela mostra o comportamento esperado **por mensagem**; já o pipeline atual consolida o sentimento e os tópicos **por lote** (veja "Nível da análise" nas observações).

### Escala de sentimentos (referência)
`Altamente Positivo` · `Positivo` · `Neutro` · `Negativo` · `Altamente Negativo`

---

| ID | Entrada (resumo) | Tipo | Sentimento esperado | Tópicos esperados | Ativo esperado | Relevância | Ação sugerida |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEMO_01** | *"Pessoal, passei no processo seletivo para Desenvolvedora Júnior de IA!"* | `depoimento` | Altamente Positivo | Conquistas, Carreira, IA | post de LinkedIn | Alta | Destacar no canal de vitórias e publicar post comemorativo. |
| **DEMO_02** | *"Alguém conseguiu conectar a API da Groq no OCI sem dar erro de autenticação?"* | `pergunta_tecnica` | Negativo | API Groq, OCI, Autenticação | FAQ | Média | Encaminhar para a mentoria e criar tópico de FAQ. |
| **DEMO_03** | *"O material da Sprint 1 ficou excelente, mas a parte de JSON poderia ter mais exemplos."* | `feedback` | Positivo | Feedback, Material de Estudo, Sprint 1 | newsletter | Média | Registrar a sugestão de mais exemplos de JSON. |
| **DEMO_04** | *(mensagem vazia)* | `pergunta_tecnica` | Não se aplica | Não se aplica | Nenhum | Não se aplica | Descartada na limpeza. |
| **DEMO_05** | *Mesmo texto da DEMO_02 (repetida)* | `pergunta_tecnica` | Negativo | API Groq, OCI, Autenticação | Nenhum (duplicata) | Não se aplica | Contar uma só vez. ⚠️ A limpeza atual ainda não remove duplicatas. |
| **DEMO_06** | *"Gente meu projetooo deu error na execução e nao consig rdodar o script"* | `pergunta_tecnica` | Negativo | Erro de execução, Script | FAQ | Média | Encaminhar para a mentoria. |
| **DEMO_07** | *"vc6 sabem pq o OCI da erro 500 qd rodo o script??? ... 🛑😭"* | `pergunta_tecnica` | Negativo | OCI, Erro 500, Python | FAQ | Média | Encaminhar para a mentoria de infraestrutura e criar FAQ sobre OCI. |
| **DEMO_08** | *"Achei legal o encontro de hoje."* | `feedback` | Positivo | Feedback, Eventos | Resumo de satisfação | Baixa | Armazenar nas métricas gerais de engajamento. |
| **DEMO_09** | *"Pessoal, consegui finalizar meu primeiro projeto de análise de dados usando Python e pandas! ..."* | `depoimento` | Positivo | Python, Pandas, Análise de Dados, GitHub | post de LinkedIn | Alta | Destacar no canal de vitórias e sugerir publicação do projeto no LinkedIn. |
| **DEMO_10** | *"Estou montando um fluxo no LangGraph ... quando o texto contém duas dúvidas diferentes, o fluxo escolhe apenas uma categoria..."* | `pergunta_tecnica` | Negativo | LangGraph, Classificação de Mensagens, Roteamento, Processamento de Texto | FAQ | Média | Encaminhar para a mentoria e criar tópico de FAQ sobre roteamento no LangGraph. |

## Observações

- Os casos DEMO_01 a DEMO_03 são os casos "limpos". DEMO_04 a DEMO_08 testam a robustez: texto vazio, duplicata, erros de digitação, ruído (abreviações e emojis) e texto curto e ambíguo.
- **Valores em revisão:** as linhas DEMO_04 a DEMO_08 e a coluna "Ação sugerida" são propostas do time e podem ser ajustadas.
- **Escala de sentimento:** a escala acima é a referência para comparar os resultados. O prompt (`src/prompts.py`) lista esses 5 níveis e `src/schemas.py` recusa qualquer outro valor (ignorando diferenças de maiúsculas e acentos).
- **Nível da análise:** hoje o motor devolve o sentimento e os tópicos da **comunidade inteira**, não de cada mensagem. A comparação linha a linha depende de uma análise por mensagem, ainda não implementada.
- Relevância: `Alta`, `Média` e `Baixa` são a referência para a avaliação. O motor ainda não devolve esse campo por mensagem.

- **DEMO_09 — nuance de sentimento:** o caso relata conquista ("consegui finalizar") mas também dificuldades ("tive bastante dificuldade"). Foi classificado como `Positivo` (e não `Altamente Positivo`) para diferenciar do DEMO_01, que é comemoração pura. Decisão sujeita a ajuste do time.
- **DEMO_10 — múltiplos tópicos:** primeiro caso com 4 tópicos específicos em mensagem longa; bom teste para verificar se o motor extrai múltiplos tópicos (casos anteriores eram mais curtos).
