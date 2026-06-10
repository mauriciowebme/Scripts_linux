import os
import secrets
import subprocess
import textwrap
import time

from install_master.core.docker_base import DockerBase


class MixinIDE(DockerBase):
    def instala_openvscode(self,):
        print('Instalando openvscode.')
        senha = input('Coloque a senha que deseja para acesso: ')
        comandos = [
            # f"""docker run -d \
            #         --name=code-server \
            #         --restart=unless-stopped \
            #         -p 8443:8443 \
            #         -e PASSWORD={senha} \
            #         -e SUDO_PASSWORD={senha} \
            #         -v {self.install_principal}/code-server:/config \
            #         lscr.io/linuxserver/code-server:latest
            #     """,
            f"""docker run -d \
                    --name openvscode \
                    --restart=unless-stopped \
                    --memory=1g \
                    --cpus=1 \
                    -p 3002:3000 \
                    -e PUID=1000 \
                    -e PGID=1000 \
                    -e TZ=America/Sao_Paulo \
                    -e CONNECTION_TOKEN='{senha}' \
                    -e SUDO_PASSWORD='{senha}' \
                    -v {self.install_principal}/openvscode/config:/config \
                    -v {self.install_principal}/openvscode/projetos:/home/workspace \
                    lscr.io/linuxserver/openvscode-server:latest
                """
            ]
        self.remove_container('openvscode')
        resultados = self.executar_comandos(comandos)
        time.sleep(30)  # Aguarda o container iniciar completamente
        print('\nInstalação concluída. openvscode está pronto para uso.')
        print(f'Acesso: https://SEU_HOST:8443/?tkn={senha}')
        
    def instala_vscode_oficial(self):
        print('Instalando vscode_oficial.')

        dockerfile = textwrap.dedent("""\
        # ------------ etapa 1: build ------------
        FROM debian:12-slim AS downloader
        ARG VSCODE_VERSION=latest
        ARG CHANNEL=stable
        RUN apt-get update && \
            apt-get install -y curl ca-certificates libicu72 libsecret-1-0 && \
            rm -rf /var/lib/apt/lists/*
        WORKDIR /opt
        RUN curl -L \
            "https://update.code.visualstudio.com/${VSCODE_VERSION}/server-linux-x64/${CHANNEL}" \
            -o vscode.tar.gz && \
            tar -xzf vscode.tar.gz && \
            mv vscode-server-* vscode-server

        # ------------ etapa 2: runtime ----------
        FROM debian:12-slim
        LABEL org.opencontainers.image.title="vscode-server"
        LABEL org.opencontainers.image.source="https://code.visualstudio.com/"
        RUN apt-get update && \
            apt-get install -y libicu72 libsecret-1-0 git openssh-client && \
            rm -rf /var/lib/apt/lists/*
        ENV VSCODE_HOME=/vscode-server
        COPY --from=downloader /opt/vscode-server ${VSCODE_HOME}
        RUN useradd -m coder
        USER coder
        WORKDIR /home/coder
        EXPOSE 8000
        ENTRYPOINT ["bash","-c","${VSCODE_HOME}/bin/code-server serve-web \
            --accept-server-license-terms \
            --port 8000 --host 0.0.0.0 \
            --connection-token $CONNECTION_TOKEN"]
        """)

        # caminho_principal = f"{self.install_principal}/vscode_oficial"
        # if os.path.exists(caminho_principal):
        #     if input(f"O caminho {caminho_principal} já existe. Deseja apagá-lo? (s/n): ").lower() == 's':
        #         print(f"Removendo diretório existente: {caminho_principal}")
        #         os.chmod(caminho_principal, 0o777)
        #         shutil.rmtree(caminho_principal)
        #     else:
        #         print("Mantendo diretório existente.")
        # else:
        #     print(f"Criando novo diretório: {caminho_principal}")

        # os.makedirs(f"{caminho_principal}/config", exist_ok=True)
        # os.makedirs(f"{caminho_principal}/projetos", exist_ok=True)
        # os.chmod(caminho_principal, 0o777)

        # porta = self.escolher_porta_disponivel()[0]
        # token = secrets.token_urlsafe(32)
        token = 'teste'

        run_args = [
            "--name", "vscode_oficial",
            "--restart=unless-stopped",
            # "-e", "PUID=1000",
            # "-e", "PGID=1000",
            # "-e", "TZ=America/Sao_Paulo",
            "-e", f"CONNECTION_TOKEN={token}",
            "-p", f"3004:8000",
            # "-v", f"{caminho_principal}/config:/config",
            # "-v", f"{caminho_principal}/projetos:/home/coder/projects",
            "-d"
        ]

        self.remove_container("vscode_oficial")
        self.executar_comandos_run_OrAnd_dockerfile(
            dockerfile_str=dockerfile,
            run_cmd=run_args
        )

        print("\nInstalação concluída.")
        print(f"Acesse: http://<seu_servidor>:3004/?tkn={token}")
