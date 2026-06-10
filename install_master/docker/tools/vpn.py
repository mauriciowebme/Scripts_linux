import os
import time

from install_master.core.docker_base import DockerBase


class MixinVPN(DockerBase):
    def instala_pritunel(self,):
        # Projeto: https://github.com/jippi/docker-pritunl
        caminho_pritunl = f'{self.install_principal}/pritunl'
        os.makedirs(caminho_pritunl, exist_ok=True)
        os.chmod(caminho_pritunl, 0o777)
        self.executar_comandos([f'sudo touch {caminho_pritunl}/pritunl.conf'], comando_direto=True)
        comandos = [
            f"""docker run -d \
                    --name pritunl \
                    --memory=512m \
                    --cpus=1 \
                    --privileged \
                    --publish 81:80 \
                    --publish 447:443 \
                    --publish 446:446 \
                    --publish 11944:11944 \
                    --publish 11944:11944/udp \
                    --dns 127.0.0.1 \
                    --restart=unless-stopped \
                    --detach \
                    --volume {caminho_pritunl}/pritunl.conf:/etc/pritunl.conf \
                    --volume {caminho_pritunl}:/var/lib/pritunl \
                    --volume {caminho_pritunl}/mongodb:/var/lib/mongodb \
                    ghcr.io/jippi/docker-pritunl
                """,
            ]
        self.remove_container('pritunl')
        resultados = self.executar_comandos(comandos)
        
        print("Aguarde enquanto o container é inicializado...")
        time.sleep(30)
        
        # Configuração inicial pós-instalação
        self.executar_comandos(['sudo docker exec pritunl pritunl reset-password'], comando_direto=True)

        print("Instalação concluída. Pritunl está pronto para uso.")
        print("porta de acesso: 447")
        print("Mude a porta da interface apos logar para: 446")
        print("Mude a porta do servidor apos logar para: 11944")
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos, exibir_executando=False)
