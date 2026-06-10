import os
import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinDockerInstall(DockerBase):

    def limpeza_containers(self,):
        
        comandos = [
            # Comando para remover imagens Docker não utilizadas há mais de 24 horas
            "docker image prune -a --filter \"until=24h\" -f",
            # Comando para remover redes Docker não utilizadas há mais de 24 horas
            "docker network prune --filter \"until=24h\" -f",
            # Comando para remover dados de construção Docker não utilizados há mais de 24 horas
            "docker builder prune --filter \"until=24h\" -f",
            # isso remove todos os volumes que não estão referenciados por nenhum contêiner
            "docker volume prune -f",
        ]
        resultados = self.executar_comandos(comandos, ignorar_erros=True, exibir_resultados=False)
        
    def instala_docker(self,):
        # Executa o comando para verificar se o Docker está instalado
        comando = "command -v docker"
        resultados = self.executar_comandos([comando], ignorar_erros=True, exibir_resultados=False)
        if resultados[comando] and 'Erro:True' not in resultados[comando][0]:
            self.limpeza_containers()
            #print("Intalação docker ok.")
        else:
            print("Docker não está instalado.")
            self.instala_docker_force()
        self.cria_rede_docker()
            
    def instala_docker_force(self,):
        print("Instalando docker...")
        resposta = input("A instalação do Docker requer uma reinicialização do sistema. Deseja continuar? (s/n) ").strip().lower()
        if resposta != 's':
            print("Instalação cancelada pelo usuário.")
            os._exit(0)
        user = input("Digite o nome do usuário com permissões de acesso extra: ")
        for i in range(2):
            comandos = [
                "sudo apt update && sudo apt upgrade -y",
                "for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -y $pkg; done",
                # Add Docker's official GPG key:
                "sudo apt-get update",
                "sudo apt-get install ca-certificates curl",
                "sudo install -m 0755 -d /etc/apt/keyrings",
                "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
                "sudo chmod a+r /etc/apt/keyrings/docker.asc",

                # Add the repository to Apt sources:
                "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
                
                "sudo apt-get update",
                "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
            ]

            # Executa todos os comandos de instalação do Docker
            resultados = self.executar_comandos(comandos, ignorar_erros=True)
            if 'erro:true' in resultados[comandos[-1]][-1]:
                comandos = [
                    f"""sudo rm /etc/apt/sources.list.d/docker.list"""
                    ]
                self.executar_comandos(comandos)
            else:
                comandos = [
                    # adiona um tempo para aguardar de 10 segundos
                    "sleep 10",
                    f"sudo usermod -aG docker {user}",
                    # "newgrp docker",
                    "sudo reboot"
                    ]
                self.executar_comandos(comandos, comando_direto=True)
