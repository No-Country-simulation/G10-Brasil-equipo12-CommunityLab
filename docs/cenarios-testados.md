# Cenários Testados

### 1. Arquivo `.json` inválido

* **O que a tela mostrou:** *"Não consegui carregar as mensagens. Arquivo inválido: Lote fora do formato esperado:"* seguido de uma lista técnica de erros de validação (ex.: `periodo_referencia: Input should be a valid string`, `interacoes.3.texto: Field required`).

* **Indicação:** Ok.

* **Observação:** Os índices das interações começam em `0` (por exemplo, `interacoes.3` refere-se ao quarto item). Isso pode confundir usuários que não são da área de programação.

### 2. Arquivo `.csv` inválido

* **O que a tela mostrou:** *"Não consegui carregar as mensagens. Arquivo inválido: Lote fora do formato esperado:"* seguido dos erros específicos de cada registro (ex.: `interacoes.0.tipo: Input should be 'depoimento', 'pergunta_tecnica', 'feedback', 'interacao_geral' ou 'entrega_projeto'`).

* **Indicação:** Ok.

* **Observação:** Os índices das interações começam em `0`. Isso pode confundir usuários que não são da área de programação.

### 3. Arquivo `.json` vazio (`0.0B`)

* **O que a tela mostrou:** *"Não consegui carregar as mensagens. Arquivo inválido: Expecting value: line 1 column 1 (char 0)"*.

* **Indicação:**  Adicionar o formato esperado.

* **Observação:** A mensagem exibiu `"Expecting value..."`, que é o texto cru da exceção do Python em inglês e não diz o que a pessoa deve fazer. Os cenários 1, 2, 4, 8 e 12 também mostram texto técnico em inglês.

### 4. Arquivo `.csv` vazio (`0.0B`)

* **O que a tela mostrou:** *"Não consegui carregar as mensagens. Arquivo inválido: Lote fora do formato esperado: • interacoes: List should have at least 1 item after validation, not 0"*.

* **Indicação:** Ok.

### 5. Arquivo de outro formato

* **Comportamento:** A interface rejeita arquivos de outros formatos.

### 6. Falta da chave no `.env`

* **O que a tela mostrou:** *"Não consegui gerar o conteúdo. A variável GROQ_API_KEY não foi encontrada. Confira o arquivo .env."*

* **Indicação:** Ok. Boa.

### 7. Aprovar sem preencher o nome do revisor

* **O que a tela mostrou:** *"Antes de decidir, escreva o seu nome no campo 'Seu nome (quem está revisando)', no começo desta área, e aperte Enter. Depois clique de novo."*

* **Indicação:** Ok. Boa.

### 8. Chave da Groq errada ou inválida

* **O que a tela mostrou:** *"Não consegui gerar o conteúdo. Falha ao chamar a API da Groq (AuthenticationError): Error code: 401 - {'error': {'message': 'Invalid API Key', 'type': 'invalid_request_error', 'code': 'invalid_api_key'}}"*

* **Indicação:** Ok.

* **Observação:** Diferente da ausência da chave (cenário 6), o retorno exibe os detalhes técnicos e o JSON de erro da API em inglês.

### 9. Sem internet na hora de gerar o conteúdo

* **O que a tela mostrou:** *"Não consegui gerar o conteúdo. Falha ao chamar a API da Groq (APIConnectionError): Connection error."*

* **Indicação:** Ok.

### 10. Arquivo `.csv` fora da codificação UTF-8 (ex.: ANSI)

* **O que a tela mostrou:** *"Não consegui carregar as mensagens. Não consegui ler o arquivo: salve-o em UTF-8."*

* **Indicação:** Ok. Boa.

### 11. Arquivo `.csv` sem o período preenchido

* **Comportamento:** O upload foi concluído normalmente, sem exibir mensagens de erro.

* **Observação:** Isso é esperado. O CSV não carrega o período dentro do arquivo, e a leitura usa o valor padrão `Semana_Atual` (`src/ingestao.py`). Por isso não há erro: o pacote gerado fica com o período `Semana_Atual`.

### 12. Lote que passa do limite de tokens da Groq

* **Como foi feito:** Em 18/11/2026, um arquivo `.csv` de 4 mensagens (uma delas mais longa que as do teste anterior) foi enviado e o botão "Gerar conteúdo" foi clicado.

* **O que a tela mostrou:** *"Não consegui gerar o conteúdo. Falha ao chamar a API da Groq (APIStatusError): Error code: 413 - {'error': {'message': 'Request too large for model `openai/gpt-oss-120b` ... on tokens per minute (TPM): Limit 8000, Requested 8387, please reduce your message size and try again. ...', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}"*.

* **Indicação:** A mensagem técnica em inglês não diz o que a pessoa deve fazer.

* **Observação:** O pedido sozinho passou do limite de 8.000 tokens por minuto que a conta tem para esse modelo, então clicar de novo não resolve. Uma alternativa é reduzir o tamanho do lote (menos mensagens ou textos mais curtos).
