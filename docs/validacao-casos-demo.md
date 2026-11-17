# Relatório de Validação dos Casos de Demonstração

## 1. Escopo
* **Casos validados:** DEMO_01 a DEMO_03, cobrindo os primeiros cenários de demonstração da interface.
* **Casos deixados de fora:** DEMO_04 a DEMO_10 (ficaram fora do escopo desta validação inicial).

## 2. Método
- **Abordagem:** Inspeção visual e conceitual direta do arquivo de dados oficial (`dados/casos_demo.json`), analisando os textos e estruturas fornecidos. Validado em 16/11/2026, sobre a `main` no commit atual.
- **Execução:** Não foi necessária a execução do pipeline de código localmente para esta validação de conteúdo.

## 3. O que foi conferido
- **Estrutura:** Verificação dos campos, tipos de dados e IDs dos cenários no arquivo JSON.
- **Linguagem neutra/inclusiva:** conferida apenas na entrada. Em DEMO_01 ("Desenvolvedora Júnior de IA"), a marca de gênero vem do próprio autor, e a regra de linguagem sem marca de gênero (`prompts/linkedin.md` e `prompts/newsletter.md`) vale para o texto gerado pelo sistema. Como o pipeline não foi executado nesta validação, o texto gerado não foi conferido aqui.

## 4. Resultado e Limites
- **Status:** Os cenários analisados (`DEMO_01` a `DEMO_03`) estão estruturados conforme esperado e alinhados às diretrizes do projeto. Nenhuma divergência crítica estrutural foi encontrada nestes casos.
- **Limites:** esta validação não executou o pipeline. A comparação "esperado x obtido" (resultado real do motor) está em `docs/resultados_esperados.md`. Também não foram conferidos DEMO_04 a DEMO_10.
