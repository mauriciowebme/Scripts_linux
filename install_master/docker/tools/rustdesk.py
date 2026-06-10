import os
import time

from install_master.core.docker_base import DockerBase


class MixinRustdesk(DockerBase):
    def instala_rustdesk(self,):
        print('Instalando rustdesk.')
        
        comandos = []
        token = self.generate_password()
            
        comandos = [
            f"""docker run -d \
                    --name rustdesk-hbbs \
                    --restart=unless-stopped \
                    --memory=256m \
                    --cpus=1 \
                    -p 21114:21114 \
                    -p 21115:21115 \
                    -p 21116:21116 \
                    -p 21116:21116/udp \
                    -p 21118:21118 \
                    -v {self.install_principal}/rustdesk/rustdesk-hbbs:/root \
                    -e TOKEN="{token}" \
                    rustdesk/rustdesk-server hbbs
                """,
            f"""docker run -d \
                    --name rustdesk-hbbr \
                    --restart=unless-stopped \
                    --memory=256m \
                    --cpus=1 \
                    -p 21117:21117 \
                    -p 21119:21119 \
                    -v {self.install_principal}/rustdesk/rustdesk-hbbr:/root \
                    -e TOKEN="{token}" \
                    rustdesk/rustdesk-server hbbr
                """,
            ]
        self.remove_container('rustdesk-hbbs')
        self.remove_container('rustdesk-hbbr')
        resultados = self.executar_comandos(comandos)
        time.sleep(10)
        self.cria_rede_docker(associar_container_nome=f'rustdesk-hbbs', nome_rede='rustdesk')
        self.cria_rede_docker(associar_container_nome=f'rustdesk-hbbr', nome_rede='rustdesk')
        
        comandos = [
            f"docker logs rustdesk-hbbs",
        ]
        resultados = self.executar_comandos(comandos, exibir_resultados=False)[f"docker logs rustdesk-hbbs"]
        for x in resultados:
            if 'Key' in x:
                print(f"\nChave de acesso: {x.split('Key: ')[1]}")
