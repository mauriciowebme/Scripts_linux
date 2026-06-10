from install_master.core.docker_base import DockerBase


class MixinPortainer(DockerBase):
    def instala_portainer(self,):
        self.remove_container('portainer')
        comandos = [
            f"""sudo docker run -d \
                    --name portainer \
                    --restart=unless-stopped \
                    --memory=256m \
                    --cpus=0.5 \
                    -p 8000:8000 \
                    -p 9443:9443 \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    -v {self.install_principal}/portainer:/data \
                    portainer/portainer-ce:latest
                """,
            ]
        resultados = self.executar_comandos(comandos)
        
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos)
        print('Porta de acesso: 9443')
