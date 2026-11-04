# Resultados de Testes de Limpeza dos Dados — Sprint 1

Serve de evidência do comportamento histórico do pipeline antes da implementação da remoção de duplicatas.

## Resultado do teste de limpeza dos dados (27/10 — Sprint 1)

* **Arquivo testado:** `dados/casos_demo.json`
* **Função testada:** `limpar_dados_comunidade()`, em `src/limpeza.py`.

### O que foi encontrado na execução original:
- **DEMO_04:** a mensagem estava vazia e foi removida corretamente.
- **DEMO_05:** a mensagem duplicada permaneceu na execução antiga, pois a função ainda não identificava nem removia duplicatas.
- **DEMO_06:** os erros de digitação permaneceram, como “projetooo”, “error” e “rdodar”.
- **DEMO_07:** as abreviações, gírias, ruídos e emojis permaneceram, como “vc6”, “qd”, “dps”, “kkk” e 🛑😭.
- **DEMO_08:** a mensagem curta foi mantida, pois continha texto.
- **DEMO_01, DEMO_02, DEMO_03, DEMO_09 e DEMO_10:** foram mantidas, com os textos preservados.

### Resultado geral:
Antes da limpeza, havia 10 interações. Depois, restaram 9. Apenas a mensagem vazia foi removida. A duplicata ainda estava como pendencia.

### Nota de Atualização (Pendente resolvido):
Com a atualização recente da branch `main` (PR #28, 30/10), a lógica de remoção de duplicatas já está implementada e integrada ao código. Com o pipeline atual, o mesmo lote passa de **10 para 8 interações** válidas, removendo tanto a mensagem vazia (`DEMO_04`) quanto a duplicada (`DEMO_05`).

## Conclusão:
A função remove mensagens com texto vazio e normaliza espaços em branco e quebras de linha. Com as melhorias recentes na `main`, o pipeline também passou a filtrar mensagens duplicadas com sucesso.

*O teste original foi realizado em memória, sem alterar o arquivo JSON original.*