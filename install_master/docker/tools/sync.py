import subprocess

from install_master.core.docker_base import DockerBase


class MixinSync(DockerBase):
    def start_sync_pastas(self):
        # Solicita ao usuário os caminhos da pasta de origem e destino
        nome = input("Digite um nome para o sincronizador: ")
        print("O sincronizador vai copiar o conteudo da pasta de origem para dentro da pasta de destino.")
        source_path = input("Digite o caminho da pasta de origem: ")
        target_path = input("Digite o caminho da pasta de destino: ")

        # Verifica se os parâmetros foram preenchidos
        if not source_path or not target_path:
            print("Erro: Ambos os caminhos de origem e destino são obrigatórios.")
            exit()

        # Define o caminho para o Dockerfile temporário em /tmp
        temp_dockerfile = "/tmp/Dockerfile-rsync-inotify"

        # Cria o Dockerfile temporário em /tmp
        with open(temp_dockerfile, "w") as f:
            f.write("""\
FROM eeacms/rsync
RUN apk add --no-cache inotify-tools
CMD ["sh", "-c", "\
    inotifywait -m -r -e modify,create,delete /data/source | \
    while read; do \
        rsync -av --delete /data/source/ /data/target/ >> /log/rsync_sync.log; \
        tail -n 1000 /log/rsync_sync.log > /log/rsync_sync.tmp && mv /log/rsync_sync.tmp /log/rsync_sync.log; \
        sleep 5; \
    done \
"]
""")
        # Comando para executar o container
        container = f"""docker run -d \
                            --name rsync-inotify-{nome} \
                            --restart=unless-stopped \
                            --memory=100m \
                            --cpus=0.1 \
                            -v {source_path}:/data/source \
                            -v {target_path}:/data/target \
                            -v /logs:/log \
                            rsync-inotify-{nome}
                    """
        comandos = [
            f"mkdir -p {source_path}",
            f"mkdir -p {target_path}",
        ]
        resultados = self.executar_comandos(comandos, ignorar_erros=True)
        comandos = [
            f"docker build -t rsync-inotify-{nome} -f {temp_dockerfile} .",
            f"rm {temp_dockerfile}",
            container,
        ]
        self.remove_container(f'rsync-inotify-{nome}')
        resultados = self.executar_comandos(comandos)
