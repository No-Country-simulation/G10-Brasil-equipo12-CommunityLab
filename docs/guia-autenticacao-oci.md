# Guia curto: autenticação com a OCI

Para quem vai rodar o envio ao OCI Object Storage (`--oci`) na própria máquina. O repositório é público: **nada deste guia deve conter chaves, OCIDs, namespace ou arquivos de configuração reais.**

## O que o projeto usa

O envio (`src/oracle_storage.py`) usa o SDK Python `oci` e lê um arquivo de configuração que fica **fora do repositório**. Por padrão, `~/.oci/config`, no perfil `DEFAULT`.

Variáveis opcionais no `.env` (valores padrão entre parênteses):

| Variável | Para que serve |
| :--- | :--- |
| `OCI_BUCKET` | Nome do bucket (`communitylab-ativos-marketing`) |
| `OCI_CONFIG_FILE` | Caminho do arquivo de configuração (`~/.oci/config`) |
| `OCI_PROFILE` | Perfil dentro do arquivo (`DEFAULT`) |

## 1. Montar o arquivo de configuração

O arquivo precisa dos campos `user`, `fingerprint`, `tenancy`, `region` e `key_file`. Modelo, com valores de exemplo que **devem ser trocados pelos seus**:

```ini
[DEFAULT]
user=ocid1.user.oc1..<seu_user_ocid>
fingerprint=<fingerprint_da_sua_chave>
tenancy=ocid1.tenancy.oc1..<seu_tenancy_ocid>
region=<sua_regiao>
key_file=<caminho_da_sua_chave_privada>.pem
```

Salve em `~/.oci/config` (ou aponte outro caminho em `OCI_CONFIG_FILE`).

## 2. Obter os valores

A chave de API (o arquivo `.pem`) é gerada no **perfil do seu usuário**, e não na área de Storage ou de Buckets. É com ela que o código prova quem você é; o bucket só entra depois, quando o script envia o pacote. O arquivo fica no seu computador e nunca vai para a nuvem nem para o GitHub.

Passo a passo no console da OCI (confirmado pelo Denilson no teste real de upload):

1. Clique no ícone do perfil, no canto superior direito, e selecione **Meu perfil** (ou **Configurações do usuário**).
2. No menu lateral esquerdo, em Recursos, clique em **Tokens e chaves** (em inglês, *Tokens and keys*).
3. Clique em **Adicionar chave de API**.
4. Mantenha selecionada a opção **Gerar par de chaves de API** e clique em **Fazer download da chave privada**. Esse download é o arquivo `.pem` que vai no `key_file`.
5. Clique em **Adicionar**.
6. O console mostra uma janela com o **trecho do arquivo de configuração** (em inglês, *Configuration file preview*). Copie o bloco inteiro, que já traz `user`, `fingerprint`, `tenancy` e `region`, e cole no `~/.oci/config`.
7. Confira o `key_file` do trecho colado: ele deve apontar para o caminho real do `.pem` que você baixou.

Os nomes dos menus podem mudar com o tempo. Em caso de dúvida, siga a [documentação oficial da Oracle](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).

## 3. Testar com um período de teste

```bash
python -c "from src.oracle_storage import salvar_no_oci; print(salvar_no_oci({'teste': 'ola'}, 'Semana_Teste'))"
```

O resultado esperado é `'status': 'salvo_com_sucesso'`. Use sempre um período de teste (como `Semana_Teste`): enviar **sobrescreve** o objeto do período, então nunca teste com `Semana_04`.

Para o pipeline completo:

```bash
python -m src.pipeline --oci --periodo Semana_Teste
```

## Se der erro

Se o bloco `armazenamento_oci` mostrar `falha_ao_salvar`, o campo `detalhe_erro` informa o tipo do erro (por exemplo, configuração da OCI ausente). A análise não se perde: o motivo aparece no próprio bloco. Se o erro apontar para permissão, peça a quem administra a conta que confira se o seu usuário pode gravar objetos nesse bucket.

## Cuidados

- Nunca colocar chave privada, OCIDs, namespace ou o arquivo `config` no repositório, em commits, em mensagens de chat ou em capturas de tela.
- O `.env` já está no `.gitignore`. O arquivo `~/.oci/config` fica na sua pasta de usuário, fora do projeto.
- Se uma chave aparecer em algum lugar público, revogue e gere outra.
