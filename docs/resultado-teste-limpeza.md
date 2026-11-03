 Resultados de Testes de Limpeza dos Dados — Sprint 1

Registro da validação da função de limpeza sobre o dataset simulado. Serve de evidência do comportamento atual do pipeline antes da implementação da remoção de duplicatas.


## Resultado do teste de limpeza dos dados 23/10 SPRINT 1 ##

Arquivo testado: dados/casos_demo.json
Função testada: limpar_dados_comunidade(), em src/limpeza.py.

O que foi encontrado:
DEMO_04: a mensagem estava vazia e foi removida corretamente.
DEMO_05: a mensagem duplicada permaneceu, pois a função não identifica nem remove duplicatas.
DEMO_06: os erros de digitação permaneceram, como “projetooo”, “error” e “rdodar”.
DEMO_07: as abreviações, gírias, ruídos e emojis permaneceram, como “vc6”, “qd”, “dps”, “kkk” e 🛑😭.
DEMO_08: a mensagem curta foi mantida, pois continha texto.
DEMO_01, DEMO_02, DEMO_03, DEMO_09 e DEMO_10: foram mantidas, com os textos preservados.
Resultado geral:

Antes da limpeza, havia 10 interações. Depois, restaram 9. Apenas a mensagem vazia foi removida. Nenhuma duplicata foi eliminada e nenhum erro de digitação foi corrigido.

## Conclusão:

A função remove mensagens com texto vazio e normaliza espaços em branco e quebras de linha. Porém, não remove duplicatas, não corrige erros de digitação e não padroniza abreviações ou emojis.

O teste foi realizado em memória, sem alterar o arquivo JSON original.##