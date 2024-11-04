#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import subprocess

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.36
===========================================================================
===========================================================================
""")

class Executa_comados():
    def __init__(self):
        pass
    
    def executar_comandos(self, comandos:list=[], ignorar_erros=False):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        resultados = {}
        for comando in comandos:
            print("\n" + "*" * 40)
            print(" " * 5 + "---> Executando comando: <---")
            print(" " * 5 + f"{comando}")
            print("*" * 40 + "\n")
            processo = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )

            # Lê e exibe cada linha da saída conforme é produzida
            resultados[comando] = []
            for linha in processo.stdout:
                resultados[comando] += [linha]
                print(linha, end="")
            
            print('\n')

            # Espera o processo terminar e captura possíveis erros
            processo.wait()
            if processo.returncode != 0:
                print(f"\nErro ao executar comando: {comando}\n")
                for linha in processo.stderr:
                    print(linha, end="")
                if not ignorar_erros:
                    print("Saindo...")
                    exit()
                    
        return resultados

class Docker(Executa_comados):
    def __init__(self):
        Executa_comados.__init__(self)
        self.install_principal = '/install_principal'

    def cria_rede_docker(self):
        network_name = "net"

        # Verifica se a rede já existe
        result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)
        if network_name not in result.stdout:
            print(f"Rede '{network_name}' não encontrada. Criando rede...")
            subprocess.run(["docker", "network", "create", network_name])
            print(f"Rede '{network_name}' criada com sucesso.")
        # else:
        #     print(f"Rede '{network_name}' já existe.")

        # Associa todos os containers existentes à rede
        result = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
        container_ids = result.stdout.strip().splitlines()
        for container_id in container_ids:
            # Tenta conectar o container à rede e captura o erro, se houver
            connect_result = subprocess.run(
                ["docker", "network", "connect", network_name, container_id],
                capture_output=True, text=True
            )

            # Verifica se o container foi associado com sucesso ou já estava na rede
            if connect_result.returncode == 0:
                print(f"Container {container_id} associado à rede '{network_name}' com sucesso.")
            # elif "already exists in network" not in connect_result.stderr:
            #     print(f"Erro ao associar o container {container_id}: {connect_result.stderr.strip()}")

    def remove_container(self, nome_container):
        comandos = [
            f'docker rm -f {nome_container}',
            ]
        resultados = self.executar_comandos(comandos)
    
    def instala_traefik(self,):
        # self.remove_container('traefik')
        comandos = [
            f"""docker run -d \
                --name traefik \
                --restart always \
                -p 80:80 \
                -p 443:443 \
                -p 8080:8080 \
                -v /var/run/docker.sock:/var/run/docker.sock:ro \
                -v {self.install_principal}/traefik/lets-encrypt:/letsencrypt \
                -v {self.install_principal}/traefik:/etc/traefik/ \
                traefik:latest \
                --entrypoints.web.address=:80 \
                --entrypoints.websecure.address=:443 \
                --entrypoints.traefik.address=:8080 \
                --providers.docker=true \
                --providers.file.filename=/etc/traefik/dynamic_conf.yml \
                --providers.docker.exposedbydefault=false \
                --api.dashboard=true \
                --api.insecure=true \
                --certificatesResolvers.le.acme.email=mauriciowebme@gmail.com \
                --certificatesResolvers.le.acme.storage=/letsencrypt/acme.json \
                --certificatesResolvers.le.acme.httpChallenge.entryPoint=web \
                --log.level=INFO
                """,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker()
        
    def instala_filebrowser(self,):
        # self.remove_container('filebrowser')
        # --label traefik.enable=true \
        # --label traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https \
        # --label traefik.http.routers.filebrowser.rule="Host(`filebrowser.techupsistemas.com`)" \
        # --label traefik.http.routers.filebrowser.entrypoints=web,websecure \
        # --label traefik.http.routers.filebrowser.tls.certresolver=le \
        # --label traefik.http.services.filebrowser.loadbalancer.server.port=80 \
        comandos = [
            f"""docker run -d \
                    --name filebrowser \
                    --restart always \
                    -p 8082:80 \
                    -v /:/srv \
                    -v {self.install_principal}/database_filebrowser/database.db:/database.db \
                    filebrowser/filebrowser
                """,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker()
        
    def instala_portainer(self,):
        comandos = [
            f"""sudo docker run -d \
                    --name portainer \
                    --restart=always \
                    -p 8000:8000 \
                    -p 9443:9443 \
                    -v /var/run/docker.sock:/var/run/docker.sock \
                    -v {self.install_principal}/portainer:/data \
                    portainer/portainer-ce:latest
                """,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker()
        
    def instala_webserver_ssh(self,):
        self.remove_container('webssh')
        comandos = [
            f"""docker run -d \
                    --name webssh \
                    -p 8081:8080 \
                    --mount source=shellngn-data,target=/home/node/server/data \
                    -e HOST=0.0.0.0 \
                    shellngn/pro:latest
                """,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker()

    def instala_docker(self,):
        # Executa o comando para verificar se o Docker está instalado
        resultados = self.executar_comandos(["command -v docker"], ignorar_erros=True)
        # Verifica se há saída para o comando
        comando = "command -v docker"
        if resultados[comando]:
            print("Docker está instalado.")
        else:
            print("Docker não está instalado.")
            comandos = [
                "apt update && apt upgrade -y",
                "for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -y $pkg; done",
                "sudo apt-get update",
                "sudo apt-get install -y ca-certificates curl",
                "sudo install -m 0755 -d /etc/apt/keyrings",
                "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
                "sudo chmod a+r /etc/apt/keyrings/docker.asc",
                (
                    "echo "
                    "'deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] "
                    "https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable' | "
                    "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
                ),
                "sudo apt-get update",
                "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
            ]

            # Executa todos os comandos de instalação do Docker
            self.executar_comandos(comandos)
            self.cria_rede_docker()

class Sistema(Docker, Executa_comados):
    def __init__(self):
        Docker.__init__(self)
        Executa_comados.__init__(self)
    
    def mostrar_menu(self, opcoes_menu, principal=False):
        """Mostra o menu de opções para o usuário de forma dinâmica."""
        opcoes_menu.insert(0, ("Sair", self.sair))
        while True:
            print("\nMenu de Opções:")
            print('===========================================================================')
            for chave, detalhes in enumerate(opcoes_menu):
                print(f"{chave}. {detalhes[0]}")
            print('===========================================================================')
            escolha = input("\nSelecione uma opção: ")

            if int(escolha) >= 0 and int(escolha) <= (len(opcoes_menu)-1):
                for chave, detalhes in enumerate(opcoes_menu):
                    if escolha == str(chave):
                        detalhes[1]()
                        if principal:
                            break
                        else:
                            return
                        
            else:
                print("\nOpção inválida. Tente novamente.\n")
    
    def testes(self,):
        comandos = [
            f"echo 'Teste ok!'"
        ]
        resultado = self.executar_comandos(comandos)
    
    def adicionar_ao_fstab(self, dispositivo, ponto_montagem):
        try:
            # Verifica se o dispositivo ou ponto de montagem já está no /etc/fstab
            with open("/etc/fstab", "r") as fstab:
                conteudo_fstab = fstab.read()
                if dispositivo in conteudo_fstab or ponto_montagem in conteudo_fstab:
                    print(f"A partição {dispositivo} já está presente no /etc/fstab.")
                    return
            
            # Se não estiver, adiciona ao /etc/fstab
            linha_fstab = f"{dispositivo} {ponto_montagem} ext4 defaults 0 0\n"
            with open("/etc/fstab", "a") as fstab:
                fstab.write(linha_fstab)
            print(f"Partição {dispositivo} adicionada ao /etc/fstab para montagem automática em {ponto_montagem}.")
        except PermissionError:
            print("Erro: Permissões insuficientes para modificar /etc/fstab. Execute o script com sudo.")
    
    def listar_particoes(self,):
        print("Listando discos disponiveis:")
        comandos = [
            "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E 'disk|part|lvm'",
        ]
        resultado = self.executar_comandos(comandos)
        
    def cria_particao(self,):
        self.listar_particoes()
        # Solicita o nome do disco ao usuário
        disco = input("Digite o nome do disco (ex: sdb) onde deseja criar a partição: ")
        ponto_montagem = input("Digite o local onde deseja montar a partição (ex: /mnt/dados): ")
        
        print(f"Criando nova partição em /dev/{disco}...")
        
        # Tenta desmonatr as partições existentes no disco
        comandos = [
            f"sudo umount /dev/{disco}*",
        ]
        # Executa os comandos
        resultado = self.executar_comandos(comandos, ignorar_erros=True)
        
        comandos = [
            f"sudo mkdir -p {ponto_montagem}",
            f"sudo parted -s /dev/{disco} mklabel gpt",                              # Define o tipo de tabela de partição como GPT
            f"sudo parted -s -a opt /dev/{disco} mkpart primary ext4 0% 100%",       # Cria a partição ocupando todo o disco
            f"sudo mkfs.ext4 /dev/{disco}1"                                       # Formata a nova partição como ext4
        ]
        
        # Executa os comandos
        resultado = self.executar_comandos(comandos)
        
        print(f"Partição criada, formatada e montada com sucesso em {ponto_montagem}.")
            
        # Opcional: Adicionar ao /etc/fstab para montagem automática
        adicionar_fstab = input("Deseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.adicionar_ao_fstab(f"/dev/{disco}1", ponto_montagem)
    
    def fecha_tela_noot(self):
        # Caminho do arquivo de configuração
        config_path = "/etc/systemd/logind.conf"
        
        # Ler o conteúdo do arquivo
        with open(config_path, "r") as file:
            lines = file.readlines()
        
        # Modificar a linha HandleLidSwitch
        with open(config_path, "w") as file:
            for line in lines:
                if line.strip().startswith("#HandleLidSwitch") or line.strip().startswith("HandleLidSwitch"):
                    file.write("HandleLidSwitch=ignore\n")
                else:
                    file.write(line)
        
        comandos = [
            "sudo systemctl restart systemd-logind",
            ]
        self.executar_comandos(comandos)
    
    def opcoes_sistema(self):
        print("\nMenu de sistema.\n")
        """Menu de opções"""
        opcoes_menu = [
            ("cria_particao", self.cria_particao),
            ("listar_particoes", self.listar_particoes),
            ("fecha_tela_noot", self.fecha_tela_noot),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def menu_docker(self):
        print("\nBem-vindo ao Gerenciador Docker\n")
        """Menu de opções"""
        opcoes_menu = [
            ("Instala docker", self.instala_docker),
            ("Instala portainer", self.instala_portainer),
            ("Instala traefik", self.instala_traefik),
            ("Instala filebrowser", self.instala_filebrowser),
            ("Instala webserver ssh", self.instala_webserver_ssh),
        ]
        self.mostrar_menu(opcoes_menu)
    
    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        comandos = [
            "echo ' '",
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
            "echo ' '",
            "echo 'Tempo em execução'",
            "uptime",
            "echo ' '",
            "df -h",
            "echo ' '"
        ]
        self.executar_comandos(comandos)
    
    def menu_atualizacoes(self,):
        """Menu de opções"""
        opcoes_menu = [
            ("atualizar_sistema_simples", self.atualizar_sistema_simples),
            ("atualizar_sistema_completa", self.atualizar_sistema_completa),
            ("atualizar_sistema_completa_reiniciar", self.atualizar_sistema_completa_reiniciar),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def atualizar_sistema_simples(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema com update...")
        self.executar_comandos(['sudo apt-get update'])
        
    def atualizar_sistema_completa(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema com upgrade...")
        self.atualizar_sistema_simples()
        self.executar_comandos(['sudo apt-get upgrade -y'])
        
    def atualizar_sistema_completa_reiniciar(self,):
        """Executa o comando para atualizar o sistema."""
        print("Reiniciando o sistema...")
        self.atualizar_sistema_simples()
        self.atualizar_sistema_completa()
        self.executar_comandos(['reboot'])

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()

def main():
    """Função principal que controla o menu."""
    servicos = Sistema()
    opcoes_menu = [
        ("Testes", servicos.testes),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("verificando status do sistema", servicos.verificando_status_sistema),
        ("Menu operações de sistema", servicos.opcoes_sistema),
        ("Menu Docker", servicos.menu_docker),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()