# Resultados Esperados dos Casos de Demonstração

Tabela de validação do comportamento esperado do pipeline para os casos de teste do `casos_demo.json`:

Os mesmos valores estão nos campos `*_esperado` de cada caso em `dados/casos_demo.json`, que é o que o script `python -m src.avaliacao` usa. Ao mudar um caso, atualize os dois.

| ID | Tipo de Mensagem | Sentimento Esperado | Tópicos Esperados | Ativo Esperado | Relevância |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEMO_01** | depoimento | Muito positivo | Conquistas, Carreira, IA | post de LinkedIn | Alta |
| **DEMO_02** | pergunta_tecnica | Negativo | API Groq, OCI, Autenticação | FAQ | Média |
| **DEMO_03** | feedback | Positivo | Feedback, Material de Estudo, Sprint 1 | newsletter | Média |

> **Nota:** A escala de sentimentos segue estritamente os 5 níveis aceitos pelo pipeline: `Muito positivo`, `Positivo`, `Neutro`, `Negativo` e `Muito negativo`.
