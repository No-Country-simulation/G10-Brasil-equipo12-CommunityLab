import json
import oci

def testar_upload():
    print("1. Lendo as credenciais do seu computador...")
    config = oci.config.from_file()

    print("2. Conectando com a Oracle Cloud...")
    cliente = oci.object_storage.ObjectStorageClient(config)

    # ⚠️ Coloque o seu Namespace real da Oracle entre as aspas:
    namespace = "grub81prfzvo" 
    bucket_name = "communitylab-ativos-marketing"
    nome_arquivo = "teste-conexao.json"

    dados = {
        "projeto": "CommunityLab",
        "autor": "Denilson (Data Engineer)",
        "mensagem": "Conexão com OCI Object Storage funcionando com sucesso!"
    }

    print("3. Fazendo upload do JSON para o Bucket...")
    resposta = cliente.put_object(
        namespace_name=namespace,
        bucket_name=bucket_name,
        object_name=nome_arquivo,
        put_object_body=json.dumps(dados, indent=2, ensure_ascii=False).encode("utf-8")
    )

    if resposta.status == 200:
        print("🎉 SUCESSO TOTAL! O arquivo foi parar dentro do seu Bucket na Oracle!")
    else:
        print("Status retornado:", resposta.status)

if __name__ == "__main__":
    testar_upload()