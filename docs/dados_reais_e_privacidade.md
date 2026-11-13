# Dados reais e privacidade

Projeto: G10 Brasil · Equipe 12 · CommunityLab (agente Pauta IA)

> Este documento **não é parecer jurídico** e **não afirma que o projeto cumpre a LGPD** (Lei nº 13.709/2018). Ele registra o que o projeto faz hoje com nomes e mensagens, o que **não** faz, e o que uma organização precisa decidir e conferir **antes** de usar a ferramenta com dados reais. Sobre o dataset de demonstração, veja [`dataset_simulado.md`](dataset_simulado.md).

## 1. Situação atual

- Todos os dados deste repositório são **simulados**. Nenhuma mensagem, nome ou conquista se refere a uma pessoa real.
- O repositório é **público**. Qualquer coisa enviada ao GitHub (arquivo, commit, mensagem de commit, descrição de PR, comentário, captura de tela) pode ser vista por qualquer pessoa e **não é possível apagar de verdade** depois: o histórico guarda o conteúdo.
- Este documento vale para o dia em que a ferramenta for usada com mensagens de uma comunidade real.

## 2. Regra de ouro

**Dados reais nunca entram no repositório.** Isso inclui:

- arquivos de mensagens (`.json` ou `.csv`) com nomes ou textos reais;
- a pasta `saida/` (já está no `.gitignore`: não force a inclusão);
- capturas de tela, trechos de mensagens e nomes em commits, PRs, issues e comentários;
- a chave da Groq (`.env`) e os dados da conta OCI (chaves `.pem`, OCIDs, namespace, arquivo `config`).

Onde guardar o arquivo de mensagens reais: **fora da pasta do projeto**, em um local com acesso restrito. O pipeline lê o arquivo pelo caminho informado, de qualquer pasta:

```bash
python -m src.pipeline "C:\caminho\fora\do\projeto\mensagens.json" --periodo Semana_Teste
```

## 3. Por onde passam os dados

A tabela descreve o que o código faz hoje. A coluna "O que conferir" lista pontos que **o projeto não resolve sozinho**.

| Etapa | O que contém | Onde fica | O que conferir |
| :--- | :--- | :--- | :--- |
| Arquivo de entrada | Autor, canal, tipo e texto de cada mensagem | Na máquina de quem roda | Guardar fora do repositório; acesso restrito; definir por quanto tempo manter |
| Envio à LLM (Groq) | Autor, canal, tipo e texto das mensagens da amostra (até 10), e o `id` quando existe. Nas mensagens de conversa geral o autor vira "Participante" antes do envio. Os nomes marcados como "não autorizados" na interface são trocados antes do envio | Serviço da Groq, fora do projeto | **Ler os termos e a política de privacidade da Groq** (retenção, uso para treinar modelos, onde os dados são tratados). Este projeto **não verificou** isso |
| Pacote gerado | Textos gerados (post, newsletter, FAQ), que podem citar nomes | `saida/` na máquina de quem roda (ignorada pelo Git) | Apagar quando não for mais necessário |
| Registro da curadoria | Texto original, texto final, **nome declarado** de quem revisou, data e hora, e as duas confirmações | `saida/` (`..._curadoria.json`), na máquina de quem roda | Contém os nomes que os textos citam; tratar como dado pessoal |
| Envio ao OCI (só com `--oci`) | O pacote gerado, em JSON | Bucket do OCI Object Storage | O código só envia o arquivo: **quem pode ler o bucket é definido na conta OCI**, e isso **não está documentado nem verificado** neste repositório. Conferir que o bucket é privado e definir prazo de retenção |
| Logs | Mensagens técnicas do pipeline | Terminal | O código registra os descartes **sem o nome da pessoa** |

A interface de curadoria **não envia nada ao OCI**. O envio é só pela linha de comando, com `--oci`.

## 4. Autorização para publicar nome

Regra do time (decisão 10 em [`regras_roteamento.md`](regras_roteamento.md)): nenhum conteúdo público pode sair com o nome da pessoa, seja o primeiro nome ou o nome completo, sem a **autorização dela**.

O que o projeto faz:

- Na interface, a pessoa que cura marca quem **não** autorizou o nome. Esses nomes são trocados por "uma pessoa da comunidade" (e "outra pessoa da comunidade") **antes** de o lote ir à Groq.
- Para aprovar um texto, a pessoa que cura confirma que conferiu os fatos e a autorização.

O que o projeto **não** faz:

- **Não verifica** se a autorização existe. O código não tem campo para isso: a confirmação é uma caixa marcada por uma pessoa.
- **Não garante o anonimato.** Apelido, cargo, empresa, cidade ou contexto ainda podem identificar alguém, e o nome também pode aparecer dentro do texto de outra pessoa. A revisão humana continua obrigatória.
- **Não confirma quem revisou.** O nome de quem aprova é declarado, sem login.

Recomendações para o uso real (não implementadas hoje):

- A autorização deve ser **específica** (dizer o que será publicado, onde e com qual nome), **registrada** (quem autorizou, quando e como) e **revogável** (a pessoa pode retirar; é preciso saber como retirar o conteúdo).
- Guardar o registro das autorizações **fora do repositório**.
- Em caso de dúvida, publicar **sem nome**.

## 5. Antes de usar com dados reais

Quem for responsável pela comunidade (a organização, não só a equipe técnica) precisa decidir e registrar:

- [ ] **Quem é responsável** pelos dados e quem responde pelas dúvidas e pedidos das pessoas participantes.
- [ ] **A base legal** para tratar as mensagens e para publicar nomes, com orientação jurídica ou da pessoa encarregada de proteção de dados, se a organização tiver uma. Este projeto não define isso.
- [ ] **Transparência:** avisar a comunidade que as mensagens serão analisadas por uma IA, por qual serviço e para quê.
- [ ] **Groq:** ler e aceitar os termos e a política de privacidade, e confirmar se o uso é adequado para dados reais.
- [ ] **OCI:** confirmar que o bucket é privado, quem tem acesso e por quanto tempo os arquivos ficam.
- [ ] **Login na interface**, para que o registro de quem aprovou e publicou seja fiel (hoje o nome é declarado).
- [ ] **Registro das autorizações** (seção 4).
- [ ] **Prazo e forma de apagar** os arquivos de entrada, o conteúdo de `saida/` e os objetos no OCI.
- [ ] **Teste com poucos dados** e revisão humana de todo texto antes de publicar.

## 6. Se dado real entrou no repositório

1. **Avise a equipe na hora.** Quanto antes, melhor.
2. **Não basta apagar em um novo commit:** o conteúdo continua no histórico e nas páginas de PR.
3. Se for uma chave ou senha, **revogue e gere outra** antes de qualquer outra coisa.

## 7. Limites deste documento

- Foi escrito pela equipe técnica, sem revisão jurídica.
- Não descreve a política da Groq nem a configuração da conta OCI da organização: essas conferências ficam com quem for operar a ferramenta.
- Reflete o código na data em que foi escrito (12/11/2026). Se o código mudar, este documento precisa ser revisado.
