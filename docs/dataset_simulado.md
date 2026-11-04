# Dataset simulado — CommunityLab (Grupo 10)

> Documento de apoio ao arquivo `dados/dataset_simulado.json`.
> Elaborado em 24/10/2026. Este texto descreve o dataset e as decisões de proteção de dados do projeto; não é parecer jurídico.

## 1. O que é este dataset

É um conjunto de **50 interações simuladas** de uma comunidade digital de aprendizagem, criado para desenvolver e testar o motor de análise e geração de conteúdo do projeto CommunityLab (Hackathon ONE G10, Oracle Next Education & Alura).

**Os dados são fictícios.** Não foram extraídos, copiados nem adaptados de nenhuma comunidade, servidor de Discord, fórum ou plataforma reais.

## 2. Origem e geração

- O dataset foi **gerado com o apoio de uma ferramenta de IA generativa (Claude, da Anthropic)**, a partir de um prompt da equipe que pedia um dataset simulado para uso no projeto.
- O prompt **proibia expressamente** a inclusão de informações de pessoas reais e de dados sensíveis.
- Os nomes dos autores são **combinações comuns de nome e sobrenome geradas pela IA**, sem vínculo intencional com pessoas reais. Por serem nomes comuns, a coincidência com pessoas reais é possível, mas nenhuma mensagem se refere a uma pessoa real.
- Depois da geração, o conteúdo recebeu uma **revisão de conformidade em 24/10/2026** (varredura automática do arquivo e leitura das 50 mensagens), registrada na seção 8.

## 3. Finalidade e uso exclusivo

- O dataset existe **exclusivamente** para desenvolvimento, testes e demonstração deste projeto.
- Não deve ser usado para outras finalidades, como treinar modelos, compor bases de pesquisa ou ser apresentado como dados reais.
- Os textos gerados a partir dele (posts de LinkedIn, destaques de newsletter etc.) são **exemplos de demonstração** e não devem ser publicados em canais reais como se fossem fatos.

## 4. Natureza fictícia dos dados

- Nomes, nomes de usuário, mensagens, conquistas e vagas citadas são **inventados**.
- Qualquer semelhança com pessoas, empresas ou situações reais é **mera coincidência**.
- O campo `origem_comunidade` (`Discord_Grupo_ONE_G10`) e o campo `periodo_referencia` (`Semana_04`) seguem o exemplo do manual do projeto e funcionam apenas como rótulos.
- O único link presente (`https://example.com/meu-projeto`) usa um domínio reservado para exemplos.

## 5. Estrutura do arquivo

| Campo | Descrição |
|---|---|
| `origem_comunidade` | Rótulo da comunidade simulada |
| `periodo_referencia` | Rótulo do período simulado |
| `interacoes` | Lista de mensagens |
| `id` | Identificador da mensagem (`MSG_001` a `MSG_050`) |
| `autor` | Nome fictício ou nome de usuário fictício |
| `canal` | Canal simulado (por exemplo, `#conquistas-e-vagas`) |
| `tipo` | `depoimento`, `pergunta_tecnica`, `feedback`, `interacao_geral` ou `entrega_projeto` (o motor aceita esse quinto tipo, mas este dataset não tem mensagens dele) |
| `texto` | Conteúdo da mensagem |
| `cenario` | Campo auxiliar de teste que indica o tipo de situação da mensagem |

Os campos `id` e `cenario` não fazem parte do exemplo de entrada do manual (`autor`, `canal`, `tipo`, `texto`). Eles servem para organizar e avaliar os testes.

## 6. Composição

**Por tipo:** 12 depoimentos, 16 perguntas técnicas, 9 feedbacks e 13 interações gerais. Nenhuma mensagem é do tipo `entrega_projeto`.

**Por cenário de teste:** 37 mensagens `limpo` e 13 mensagens com situações propositais para testar a limpeza e a geração:

| Cenário | Mensagem(ns) | O que testa |
|---|---|---|
| `vazio` | MSG_017 | Mensagem sem texto |
| `duplicado` | MSG_020, MSG_035 | Mensagens repetidas |
| `ruido` | MSG_023 | Gírias, abreviações e emoji |
| `sentimento_misto` | MSG_024 | Elogio e crítica na mesma mensagem |
| `erro_digitacao` | MSG_026 | Erros de digitação |
| `so_emojis` | MSG_030 | Mensagem só com emojis |
| `caixa_alta` | MSG_036 | Texto todo em maiúsculas |
| `cuidado_com_fatos` | MSG_037 | Risco de o modelo inventar ou exagerar fatos |
| `misto_idioma` | MSG_039 | Português e inglês misturados |
| `espacos_e_quebras` | MSG_041 | Espaços extras e quebras de linha |
| `com_link` | MSG_042 | Mensagem com link |
| `ambiguo` | MSG_043 | Mensagem curta demais para classificar |

## 7. Proteção de dados e LGPD

A Lei Geral de Proteção de Dados (Lei nº 13.709/2018) protege **dados pessoais**, isto é, informações relacionadas a pessoa natural identificada ou identificável. Como as pessoas, os nomes e as mensagens deste dataset são fictícios e não se referem a indivíduos reais, a equipe entende que **o dataset não contém dados pessoais**. O projeto adota, mesmo assim, as práticas abaixo, para criar o hábito certo antes de qualquer uso com dados reais.

**Práticas adotadas agora**

1. **Finalidade clara:** o dataset serve apenas ao desenvolvimento e à demonstração do projeto.
2. **Sem dados pessoais reais no repositório:** nenhum nome, e-mail, telefone, documento ou mensagem real deve ser incluído no dataset.
3. **Segredos fora do Git:** chaves de API e credenciais da OCI ficam no arquivo `.env`, que está no `.gitignore`, e nunca são enviadas por chat ou commit.
4. **Transparência na demonstração:** ao apresentar o projeto, informar que os dados e os textos gerados são simulados.
5. **Novas mensagens:** se forem geradas com IA, repetir no prompt a proibição de pessoas reais e dados sensíveis e revisar o resultado antes de incluir no dataset.

**Se o motor for usado no futuro com dados reais de uma comunidade**

1. Definir a **finalidade** do tratamento e a **base legal** adequada antes de coletar qualquer mensagem.
2. Coletar apenas o **necessário** (minimização) e remover ou substituir nomes e identificadores (anonimização ou pseudonimização) antes de enviar o texto a um provedor de LLM ou a qualquer serviço em nuvem.
3. Verificar como o provedor de LLM e a nuvem tratam os dados enviados, inclusive o local de armazenamento.
4. Manter o armazenamento (por exemplo, o bucket na OCI) com acesso restrito e definir por quanto tempo os dados serão guardados.
5. Obter autorização das pessoas ou da organização responsável antes de publicar qualquer texto que cite nome, cargo ou conquista reais.
6. Consultar a orientação jurídica ou o encarregado de dados (DPO) da organização.

## 8. Revisão de risco LGPD do dataset (24/10/2026)

Revisão feita por varredura automática do arquivo e leitura das 50 mensagens.

| Item verificado | Resultado |
|---|---|
| E-mails, telefones, CPF, CEP, outros documentos e @handles | Nenhum encontrado |
| Links | 1 link, em domínio de exemplo (`example.com`) |
| Dados pessoais sensíveis (art. 5º, II: saúde, religião, opinião política, origem racial ou étnica, vida sexual, dado genético ou biométrico etc.) | Nenhuma mensagem trata desses temas |
| Mensagens sobre dificuldades pessoais (MSG_011, MSG_028, MSG_049) | Falam de dificuldade para estudar e de insegurança, sem condição de saúde ou diagnóstico. Risco baixo, mas pedem cuidado de uso (abaixo) |
| Nomes dos autores | 48 autores únicos: 42 com nome e sobrenome e 6 nomes de usuário, todos fictícios. Dois autores se repetem de propósito, nas mensagens duplicadas |
| Conteúdo ofensivo ou difamatório sobre pessoa identificável | Nenhum |
| Ferramentas e marcas citadas (Pandas, Streamlit, GitHub, n8n, LinkedIn, Python) | Sem relevância para a LGPD |

**Conclusão:** o risco do dataset em si é **baixo**. Os cuidados mais importantes estão no uso:

1. **Demonstração:** avisar que os dados e os textos gerados são simulados. Um post como "a aluna Camila Duarte foi contratada" não pode ser publicado como se fosse real.
2. **Mensagens de dificuldade** (MSG_011, MSG_028, MSG_049): usar apenas para análise de sentimento ou alerta interno, sem gerar post público com o nome do autor.
3. **Coincidência de nomes:** por serem nomes comuns, podem coincidir com pessoas reais. Isso não torna o dataset uma base de dados pessoais, já que nada nele descreve uma pessoa real. Ainda assim, evitar divulgar o dataset fora do projeto.
4. **Dados reais:** nunca trocar ou misturar dados reais ao dataset sem seguir a seção 7.
