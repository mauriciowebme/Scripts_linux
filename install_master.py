#!/bin/bash

#pip install PyYAML requests

#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import os
import os.path
import socket
import subprocess
import time
import yaml
import json
import requests
from requests.auth import HTTPBasicAuth

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.133
===========================================================================
===========================================================================
""")

class Executa_comados():
    def __init__(self):
        pass
    
    def executar_comandos(self, comandos:list=[], ignorar_erros=False, exibir_resultados=True, comando_direto=False):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        resultados = {}
        for comando in comandos:
            resultados[comando] = []
            if comando_direto:
                comando_convertido = comando.split()
                try:
                    subprocess.run(comando_convertido, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao executar o comando: {e}")
                    print(f"Código de saída: {e.returncode}")
                    resultados[comando] += [e.returncode]
            else:
                if exibir_resultados:
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
                for linha in processo.stdout:
                    resultados[comando] += [linha]
                    if exibir_resultados:
                        print(linha, end="")

                # Espera o processo terminar e captura possíveis erros
                processo.wait()
                if processo.returncode != 0:
                    print(f"\nErro ao executar comando: {comando}\n")
                    resultados[comando] += ['Erro:True']
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
        self.redes_docker = ['_traefik', 'interno']
        self.atmoz_sftp_arquivo_conf = os.path.join(f"{self.install_principal}/atmoz_sftp/", "users.conf")
        
    def escolher_porta_disponivel(self, inicio=40000, fim=40500):
        for porta in range(inicio, fim + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Tenta se conectar na porta; se falhar, a porta está disponível
                if s.connect_ex(('localhost', porta)) != 0:
                    print(f"Porta {porta} está disponível e será usada.")
                    return porta
        
        # Se não houver portas disponíveis no intervalo
        print(f"Nenhuma porta disponível entre {inicio} e {fim}.")
        return None

    def cria_rede_docker(self, associar_todos=False, associar_container_nome=False, numero_rede=None):
        # Verifica se a rede já existe
        try:
            result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)
            for rede in self.redes_docker:
                if rede not in result.stdout:
                    print(f"Rede '{rede}' não encontrada. Criando rede...")
                    subprocess.run(["docker", "network", "create", rede])
                    print(f"Rede '{rede}' criada com sucesso.")
                # else:
                #     print(f"Rede '{network_name}' já existe.")
        
            if associar_container_nome:
                if numero_rede != None:
                    redes = [self.redes_docker[numero_rede]]
                else:
                    redes = self.redes_docker
                # Tenta conectar o container à rede e captura o erro, se houver
                for rede in redes:
                    connect_result = subprocess.run(
                        ["docker", "network", "disconnect", "bridge", associar_container_nome],
                        capture_output=True, text=True
                    )
                    
                    # Verifica se o container foi associado com sucesso ou já estava na rede
                    if connect_result.returncode == 0:
                        print(f"Container {associar_container_nome} desconectado da rede bridge com sucesso.")
                    # elif "already exists in network" not in connect_result.stderr:
                    #     print(f"Erro ao associar o container {container_id}: {connect_result.stderr.strip()}")
                    
                    connect_result = subprocess.run(
                        ["docker", "network", "connect", rede, associar_container_nome],
                        capture_output=True, text=True
                    )

                    # Verifica se o container foi associado com sucesso ou já estava na rede
                    if connect_result.returncode == 0:
                        print(f"Container {associar_container_nome} associado à rede '{rede}' com sucesso.")
                    # elif "already exists in network" not in connect_result.stderr:
                    #     print(f"Erro ao associar o container {container_id}: {connect_result.stderr.strip()}")
            
            if associar_todos:
                # Associa todos os containers existentes à rede
                result = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
                container_ids = result.stdout.strip().splitlines()
                for container_id in container_ids:
                    for rede in self.redes_docker:
                        # Tenta conectar o container à rede e captura o erro, se houver
                        connect_result = subprocess.run(
                            ["docker", "network", "connect", rede, container_id],
                            capture_output=True, text=True
                        )

                        # Verifica se o container foi associado com sucesso ou já estava na rede
                        if connect_result.returncode == 0:
                            print(f"Container {container_id} associado à rede '{rede}' com sucesso.")
                        # elif "already exists in network" not in connect_result.stderr:
                        #     print(f"Erro ao associar o container {container_id}: {connect_result.stderr.strip()}")
        
        except Exception as ex:
            pass

    def remove_container(self, nome_container):
        comandos = [
            f'docker rm -f {nome_container}',
            ]
        resultados = self.executar_comandos(comandos)
        
    def adiciona_redirecionamento_traefik(self, container, dominio=None, porta=None):
        """
        Exemplo de uso:
        
        container = f"docker run -d \
                        --name webssh \
                        --restart=always \
                        -p 8001:8000 \
                        liftoff/gateone
                    "
        OBS: Coloque 3 aspas no lugar de uma.
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container)
        
        """
        if dominio == None:
            dominio = input('Digite o dominio:')
        if porta == None:
            porta = input('Digite a porta do container:')
        
        container = container.replace( '  ', '' ).replace( '\n', '' )
        imagem = container.split()[-1]
        container = container[:-len(imagem)].rstrip()
        
        dominio_ = dominio.replace('.', '_')
        labels = f""" --network {self.redes_docker[0]} \
                --label traefik.enable=true \
                --label traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https \
                --label traefik.http.routers.{dominio_}.rule=\"Host(\`{dominio}\`)\" \
                --label traefik.http.routers.{dominio_}.entrypoints=web,websecure \
                --label traefik.http.routers.{dominio_}.tls.certresolver=le \
                --label traefik.http.services.{dominio_}.loadbalancer.server.port={porta} \
            """
        container = container + labels.replace( '  ', '' ) + imagem
        return container

    def iniciar_monitoramento(self):
        conteudo = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node_exporter'
    static_configs:
      - targets: ['node-exporter:9100']
"""
        caminho = f'{self.install_principal}/prometheus/prometheus.yml'
        comandos = [
            f"mkdir -p {self.install_principal}/prometheus/",
            f"touch {caminho}",
            f"echo '{conteudo}' > {caminho}",
            f"""docker run -d \
                --name prometheus \
                --restart=always \
                -p 9090:9090 \
                -v {self.install_principal}/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml \
                prom/prometheus
            """,
            f"""docker run -d \
                --name node-exporter \
                --restart=always \
                -p 9100:9100 \
                prom/node-exporter
            """,
            f"""docker run -d \
                --name grafana \
                --restart=always \
                -p 3000:3000 \
                grafana/grafana
            """,
        ]
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome='prometheus', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='node-exporter', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='grafana', numero_rede=1)
    
    
    def cria_dynamic_conf_traefik(self,):
        dynamic_conf = f'{self.install_principal}/traefik/dynamic_conf.yml'
        # dynamic_conf = f'C:\TESTES_C\dynamic_conf.yml'
        if not os.path.exists(dynamic_conf):
            email = input('Digite um e-mail para gerar o certificado: ')
            with open(dynamic_conf, "w") as f:
                f.write(f"""\
http:
  routers:
    exemplo_meu_dominio_com:
      rule: "Host(`exemplo.meu_dominio.com`)"
      entryPoints:
        - web
        - websecure
      service: exemplo_meu_dominio_com
      tls:
        certResolver: le

  services:
    exemplo_meu_dominio_com:
      loadBalancer:
        servers:
          - url: "http://10.0.0.1:80"

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true

  websecure:
    address: ":443"

certificatesResolvers:
  le:
    acme:
      email: "{email}"
      storage: "/letsencrypt/acme.json"
      httpChallenge:
        entryPoint: web

""")
        return dynamic_conf
        
    def adiciona_roteador_servico_traefik(self, dominio=None, endereco=None, porta=None):
        if dominio == None:
            dominio = input('Digite o dominio: ')
        if endereco == None:
            endereco = input('Coloque o endereço do container ou ip da rede que deseja apontar: ')
        if porta == None:
            porta = input('Digite a porta: ')
        
        self.cria_rede_docker(associar_container_nome=endereco, numero_rede=0)
        
        dynamic_conf = self.cria_dynamic_conf_traefik()
        
        # Carregar o arquivo de configuração YAML existente
        with open(dynamic_conf, 'r') as file:
            config = yaml.safe_load(file)

        # Definir o nome do serviço e do roteador com base no domínio
        router_name = dominio.replace('.', '_')
        service_name = f"{router_name}_service"
        
        if 'http' not in config:
            config['http'] = {}
        
        if 'routers' not in config['http']:
            config['http']['routers'] = {}
            
        if 'services' not in config['http']:
            config['http']['services'] = {}

        # Criar o roteador para o domínio
        config['http']['routers'][router_name] = {
            'rule': f"Host(`{dominio}`)",
            'entryPoints': ['web', 'websecure'],
            'service': service_name,
            'tls': {
                'certResolver': 'le'
            }
        }
        print(f"Roteador adicionado para o domínio: {dominio}")
    
        # Criar o serviço para o domínio com o URL de destino e a porta
        config['http']['services'][service_name] = {
            'loadBalancer': {
                'servers': [
                    {'url': f"http://{endereco}:{porta}"}
                ]
            }
        }
        print(f"Serviço adicionado para o domínio: {dominio}")

        # Salvar o arquivo de configuração atualizado
        with open(dynamic_conf, 'w') as file:
            yaml.dump(config, file)

    def instala_traefik(self,):
        dynamic_conf = self.cria_dynamic_conf_traefik()
        comandos = [
            f"""docker run -d \
                --name traefik \
                --restart=always \
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
        self.remove_container('traefik')
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome='traefik', numero_rede=0)
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos)
        print('Porta de acesso: 8080')
        
    def configura_rede(self,):
        print('\nAdicionando rede no container.')
        
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}} {{.Names}}"],
            capture_output=True,
            text=True
        )
        container_info = result.stdout.strip().splitlines()
        for info in container_info:
            print(info)
            
        nome_container = input('\nDigite o nome ou ID do container:')
        for x, y in enumerate(self.redes_docker):
            print(f'Rede:{x} {y}')
        rede_numero = input('\nDigite o numero da rede:')
        self.cria_rede_docker(associar_container_nome=nome_container, numero_rede=int(rede_numero))
        
    def instala_filebrowser(self,):
        porta = self.escolher_porta_disponivel()
        container = f"""docker run -d \
                    --name filebrowser \
                    --restart=always \
                    -p {porta}:80 \
                    -v /:/srv \
                    -v {self.install_principal}/database_filebrowser/database.db:/database.db \
                    filebrowser/filebrowser
                """
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container, porta='80')
        
        comandos = [
            # f"rm -r {self.install_principal}/database_filebrowser",
            f"mkdir -p {self.install_principal}/database_filebrowser",
            f"touch {self.install_principal}/database_filebrowser/database.db",
            container,
            ]
        self.remove_container('filebrowser')
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(endereco='filebrowser', porta='80')
            self.cria_rede_docker(associar_container_nome=f'filebrowser', numero_rede=0)
        print(f"Possiveis ip's para acesso:")
        comandos = [
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
        ]
        self.executar_comandos(comandos)
        print(f'Porta para uso local: {porta}')
        print(f'Usuario e senha padrão: admin, admin')
        
    def verifica_container_existe(self, container_name, install_function):
        """
        Exemplo de uso:
        self.verifica_container_existe('openlitespeed', self.instala_openlitespeed)
        """

        # Verifica se o container existe antes de instalar
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}} {{.Names}}"],
            capture_output=True,
            text=True
        )
        container_info = result.stdout.strip().splitlines()
        encontrado = False
        for info in container_info:
            if container_name in info:
                encontrado = True
                break

        if not encontrado:
            print(f"Container {container_name} não encontrado, instalando...")
            install_function()  # Chamada correta da função
            print('Aguarde terminando de instalar...')
            time.sleep(30)  # Aguarda 30 segundos ou um tempo adequado
            print(f"Container {container_name} instalado com sucesso.")
        
    def instala_openlitespeed(self,):
        print("Instalando openlitespeed.")
        conf_completa = f"{self.install_principal}/openlitespeed/conf_completa"
        copiar = False
        if os.path.exists(conf_completa):
            if os.path.isdir(conf_completa):
                if not os.listdir(conf_completa):  # Retorna vazio se a pasta não contém arquivos ou subpastas
                    # return f"A pasta '{conf_completa}' existe e está vazia."
                    copiar = True
                else:
                    # return f"A pasta '{conf_completa}' existe, mas não está vazia."
                    pass
            else:
                # return f"O caminho '{conf_completa}' existe, mas não é uma pasta."
                copiar = True
        else:
            # return f"A pasta '{conf_completa}' não existe."
            copiar = True
        
        if copiar:
            # os.rmdir(conf_completa)
            os.makedirs(conf_completa, exist_ok=True)
            os.chmod(conf_completa, 0o777)
            container = f"""docker run -d \
                            --name openlitespeed \
                            --restart=always \
                            litespeedtech/openlitespeed:latest
                    """
            
            self.remove_container('openlitespeed')
            comandos = [
                container,
                f"docker cp openlitespeed:/usr/local/lsws/. {conf_completa}",
                ]
            resultados = self.executar_comandos(comandos)
        
        container = f"""docker run -d \
                            --name openlitespeed \
                            --restart=always \
                            -p 8088:8088 \
                            -p 7080:7080 \
                            -v {self.install_principal}/openlitespeed/vhosts:/var/www/vhosts \
                            -v {conf_completa}:/usr/local/lsws \
                            litespeedtech/openlitespeed:latest
                    """
            
        self.remove_container('openlitespeed')
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'openlitespeed', numero_rede=0)
        
        print(" ")
        print("Configurações de openlitespeed concluídas.")
        print(" ")
        print("Caminho de instalação:")
        print(f"{self.install_principal}/vhosts")
        print(" ")
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos)
        print("Porta de acesso: 7080")
        print(" ")
        print("Acesso padrão:")
        print("Usuario: admin")
        print("Senha: 123456")
        print(" ")
        print("Vá para a seção Security no painel de administração.")
        print("Escolha a opção Admin Password.")
        print("Insira a nova senha desejada e salve as alterações.")
        print(" ")
    
    def controle_sites_openlitespeed(self,):
        
        self.verifica_container_existe('openlitespeed', self.instala_openlitespeed)
        
        nome_dominio = input('Digite o dominio: ')
        senha_ftp = input('Digite uma senha para o ftp: ')
        nome_dominio_ = nome_dominio.replace('.', '_')
        resposta_traefik = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta_traefik.lower() == 's':
            self.adiciona_roteador_servico_traefik(nome_dominio, endereco='openlitespeed', porta='8088')
        sites_dir = f"{self.install_principal}/openlitespeed"
        # Diretório do site
        #/usr/local/lsws/
        site_dir = os.path.join(sites_dir, "vhosts", nome_dominio_)
        public_html = os.path.join(site_dir, "public_html")
        conf_dir = os.path.join(sites_dir, "conf_completa", "conf", "vhosts", nome_dominio_)
        listener_conf_path = os.path.join(sites_dir, "conf_completa", "conf", "httpd_config.conf")
        
        # Cria os diretórios necessários
        os.makedirs(public_html, exist_ok=True)
        os.makedirs(conf_dir, exist_ok=True)
        
        # Cria um arquivo de índice básico
        index_path = os.path.join(public_html, "index.php")
        if not os.path.exists(index_path):
            with open(index_path, "w") as index_file:
                index_file.write("<?php echo 'Site criado com sucesso! ' . $_SERVER['HTTP_HOST']; ?>")
        
        # Configuração do Virtual Host
        vhost_conf_path = os.path.join(conf_dir, "vhconf.conf")
        with open(vhost_conf_path, "w") as vhost_file:
            vhost_file.write(f"""\
docRoot                   /var/www/vhosts/{nome_dominio_}/public_html
vhDomain                  {nome_dominio}
""")
        
        comandos = [
            f"sudo chmod -R 777 {conf_dir}",
            ]
        resultados = self.executar_comandos(comandos)
        
        # Configuração do Virtual Host e Listener no httpd_config.conf
        virtualhost_config = f"""
virtualhost {nome_dominio_} {{
  vhRoot                  /var/www/vhosts/{nome_dominio_}/
  configFile              $SERVER_ROOT/conf/vhosts/$VH_NAME/vhconf.conf
  allowSymbolLink         1
  enableScript            1
  restrained              1
}}
"""
        listener_config = f"""
listener Default {{
  address                 *:8088
  secure                  0
  map                     Example *
  map                     {nome_dominio_} {nome_dominio}
}}
"""
        
        # Adiciona a configuração do Virtual Host e Listener se não existirem
        with open(listener_conf_path, "r+") as listener_file:
            content = listener_file.read()
            if virtualhost_config.strip() not in content:
                listener_file.write(virtualhost_config)
                print(f"Virtual Host para '{nome_dominio_}' adicionado.")
            else:
                print(f"Virtual Host para '{nome_dominio_}' já existe.")
            
            if listener_config.strip() not in content:
                listener_file.write(listener_config)
                print(f"Listener para '{nome_dominio_}' adicionado.")
            else:
                print(f"Listener para '{nome_dominio_}' já existe.")
        
        self.gerenciar_usuarios_sftp(manual=False, simples_usuario=nome_dominio_, simples_senha=senha_ftp, simples_base_diretorio=public_html)
        
        print(f"Configuração do site '{nome_dominio_}' criada com sucesso!")
        print(f"Arquivos criados em: {site_dir}")
        
    def instala_windows_docker(self,):
        # link do projeto: https://github.com/dockur/windows
        
         # Verifica suporte à virtualização
        print("Verificando suporte à virtualização...")
        try:
            comandos_virtualizacao = ["egrep -c '(vmx|svm)' /proc/cpuinfo"]
            resultado_virtualizacao = self.executar_comandos(comandos_virtualizacao)
            # Captura a saída do comando
            virtualizacao_output = resultado_virtualizacao.get(comandos_virtualizacao[0], [])
            if not virtualizacao_output or "Erro:True" in virtualizacao_output:
                print("Erro ao executar o comando para verificar suporte à virtualização.")
                return
            # Converte a saída para inteiro
            virtualizacao = int(virtualizacao_output[0].strip())
            if virtualizacao == 0:
                print("Erro: Sua máquina não suporta virtualização. Ative o suporte na BIOS antes de continuar.")
                return
        except (KeyError, ValueError, IndexError) as e:
            print(f"Erro ao verificar suporte à virtualização: {e}")
            return

        # Verifica dispositivo KVM
        print("Verificando dispositivo KVM...")
        try:
            comandos_kvm = ["ls -l /dev/kvm"]
            resultado_kvm = self.executar_comandos(comandos_kvm)
            # Captura a saída do comando
            kvm_output = resultado_kvm.get(comandos_kvm[0], [])
            if not kvm_output or "No such file or directory" in kvm_output[0]:
                print("Erro: O dispositivo KVM não está disponível. Instale e configure KVM antes de continuar.")
                return
        except (KeyError, IndexError) as e:
            print(f"Erro ao verificar o dispositivo KVM: {e}")
            return
        print('\nIniciando instalação do container Windows.')
        local_install = input('\nDigite o local onde deseja instalar sem o / no final: ')
        nome_container = input('Digite o nome para o container Windows: ')
        senha = input('Digite a senha para acessar o Windows(o usuario sempre sera admin_win): ')
        memoria = input('Digite a quantidade de memoria (apenas numeros): ')
        cpu = input('Digite a quantidade de CPUs (apenas numeros): ')
        disco = input('Digite tamanho do disco (apenas numeros): ')
        print('\n')
        porta = self.escolher_porta_disponivel()
        self.remove_container(f'windows_{nome_container}')
        # -p 3389:3389/tcp \
        # -p 3389:3389/udp \
        comandos = [
            f"""sudo docker run -d \
                    --name windows_{nome_container} \
                    --restart=always \
                    -p {porta}:8006 \
                    --device=/dev/kvm \
                    --cap-add=NET_ADMIN \
                    -e RAM_SIZE="{memoria}G" \
                    -e CPU_CORES="{cpu}" \
                    -e DISK_SIZE="{disco}G" \
                    -e LANGUAGE="pt-BR" \
                    -e USERNAME="admin_win" \
                    -e PASSWORD="{senha}" \
                    -e LANGUAGE="pt-BR" \
                    -v {local_install}/windows_{nome_container}/win:/storage \
                    -v {local_install}/windows_{nome_container}/data:/data \
                    dockurr/windows:latest
                """
        ]
        resultados = self.executar_comandos(comandos)

        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        resultados = self.executar_comandos(comandos)
        print('Portas de acesso:')
        print(' - Usuario: admin_win')
        print(f' - Porta Web: {porta}')
        print(' - Porta RDP: 3389')
        
    def instala_rustdesk(self,):
        comandos = [
            f"""docker run -d \
                    --name rustdesk \
                    -p 21115:21115 \
                    -p 21116:21116 \
                    -v {self.install_principal}/rustdesk/config:/config \
                    rustdesk/rustdesk-server hbbs -r 21116 -k 21115
                """,
            ]
        self.remove_container('rustdesk')
        resultados = self.executar_comandos(comandos)
        
    def instala_portainer(self,):
        self.remove_container('portainer')
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
        
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos)
        print('Porta de acesso: 9443')
        
    def instala_app_nodejs(self,):
        nome_dominio = input('Digite o dominio ou nome do projeto: ')
        resposta_traefik = input('Deseja redirecionar com traefik?: S ou N: ')
        nome_dominio_ = nome_dominio.replace('.', '_')
        porta = self.escolher_porta_disponivel()
        diretorio_projeto = f"{self.install_principal}/node/{nome_dominio_}"
        os.makedirs(diretorio_projeto, exist_ok=True)
        
        # Define a estrutura do package.json
        package_json = {
            "name": nome_dominio_,
            "version": "1.0",
            "main": "index.js",
            "scripts": {
                "start": "node index.js"
            },
            "dependencies": {
                "express": "^4.17.1"
            }
        }
        # Caminho para o arquivo package.json
        caminho_package_json = os.path.join(diretorio_projeto, "package.json")
        if not os.path.exists(caminho_package_json):
            # Escreve o conteúdo no arquivo package.json
            with open(caminho_package_json, "w") as arquivo:
                json.dump(package_json, arquivo, indent=4)
            print(f"Arquivo package.json criado em {caminho_package_json}")
        
        index_js = f"""\
const express = require('express');
const app = express();
const PORT = {porta};

app.get('/', (req, res) => {{
  res.send('Servidor Node.js com Express funcionando!');
}});

app.listen(PORT, () => {{
  console.log(`Servidor rodando na porta {porta}`);
}});
"""
        # Caminho para o arquivo index.js
        caminho_index_js = os.path.join(diretorio_projeto, "index.js")
        #if not os.path.exists(caminho_index_js):
        # Escreve o conteúdo no arquivo index.js
        with open(caminho_index_js, "w") as arquivo:
            arquivo.write(index_js)
        print(f"Arquivo index.js criado em {caminho_index_js}")
        
        print(f'Porta interna para uso: {porta}')
        container = f"""docker run -d \
                        --name {nome_dominio_} \
                        --restart=always \
                        -p {porta}:{porta} \
                        -v {diretorio_projeto}:/usr/src/app \
                        -w /usr/src/app \
                        node:latest \
                        /bin/sh -c \"npm install && npm start\"
                    """
        
        comandos = [
            container,
            ]
        self.remove_container(nome_dominio_)
        resultados = self.executar_comandos(comandos)
        if resposta_traefik.lower() == 's':
            self.adiciona_roteador_servico_traefik(dominio=nome_dominio, endereco=nome_dominio_, porta=porta)
    
    def instala_ftp_sftpgo(self,):
        print('Instalando o ftp_sftpgo.\n')
        
        dir_dados = f"{self.install_principal}/ftp_sftpgo/dados"
        os.makedirs(dir_dados, exist_ok=True)
        os.chmod(dir_dados, 0o777)
        
        container = f"""docker run -d \
                        --name ftp_sftpgo \
                        --restart=always \
                        -p 2025:2022 \
                        -p 8085:8080 \
                        -v {self.install_principal}:/install_principal \
                        -v {dir_dados}:/var/lib/sftpgo \
                        drakkan/sftpgo
                    """
        comandos = [
            container,
            ]
        self.remove_container(f'ftp_sftpgo')
        resultados = self.executar_comandos(comandos)
        # self.cria_rede_docker(associar_container_nome=f'mysql_5_7', numero_rede=1)
        
    def gerenciar_usuarios_sftp(self, manual=True, simples_usuario=None, simples_senha=None, simples_base_diretorio=None):
        """
        Documentação:
        
        https://sftpgo.stoplight.io/docs/sftpgo/vjevihcqw0gy4-get-a-new-admin-access-token
        """
        
        self.verifica_container_existe('ftp_sftpgo', self.instala_ftp_sftpgo)
        
        print('\nUsuario e senha para permissão de administração FTP:')
        admin_usuario = input('Usuario admin: ')
        admin_senha = input('Senha: ')
        
        url = "http://localhost:8085/api/v2/token"
        response = requests.get(url, auth=HTTPBasicAuth(admin_usuario, admin_senha))
        if response.status_code == 200:
            print("Logado com sucesso\n")
            token = response.json()['access_token']
        else:
            print(f"Usuario sem pemissão ou não existe.")
            exit()
            # print(f"Erro: {response.status_code}")
            # print(response.json())
            
        if manual:
            print('Digite os dados para criação do novo usuario FTP:')
            simples_usuario = input('Digite o nome de usuario: ')
            simples_senha = input('Digite uma senha: ')
            simples_base_diretorio = input('Digite um diretorio dentro de /install_principal começando com /: ')
            print('\n')

        if '/' != simples_base_diretorio.split()[0]:
            simples_base_diretorio = '/'+simples_base_diretorio
        simples_base_diretorio = simples_base_diretorio.replace('//', '/')
        if '/install_principal' not in simples_base_diretorio:
            simples_base_diretorio = '/install_principal'+simples_base_diretorio
        
        os.makedirs(simples_base_diretorio, exist_ok=True)
        os.chmod(simples_base_diretorio, 0o777)
        
        # URL do endpoint para criar usuários
        url = "http://localhost:8085/api/v2/users"
        # Cabeçalhos com o token de autenticação
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # Corpo da requisição
        payload = {
            "status": 1,
            "username": simples_usuario,
            "password": simples_senha,
            "home_dir" : simples_base_diretorio ,
            "filesystem": {
                "provider": 0
            },
            "permissions": {
                "/": [
                "*"
                ]
            },
        }

        # Requisição POST para criar o usuário
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"Usuário '{simples_usuario}' criado com sucesso!")
            #print(response.json())
        else:
            print(f"Erro ao criar usuário '{simples_usuario}': {response.status_code}")
            print(response.json())
        pass
    
    def instala_webserver_ssh(self,):
        self.remove_container('webssh')
        print('Porta interna para uso: 8080')
        container = f"""docker run -d \
                        --name webssh \
                        --restart=always \
                        -p 8081:8080 \
                        --mount source=shellngn-data,target=/home/node/server/data \
                        -e HOST=0.0.0.0 \
                        shellngn/pro:latest
                    """
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container)
        
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(endereco='webssh', porta='8080')
            self.cria_rede_docker(associar_container_nome=f'webssh', numero_rede=0)
        self.cria_rede_docker(associar_container_nome=f'webssh', numero_rede=1)
        
    def instala_mysql_5_7(self,):
        print('Instalando o mysql.\n')
        # -e MYSQL_RANDOM_ROOT_PASSWORD=wordpress \
        container_db = f"""docker run -d \
                        --name mysql_5_7 \
                        --restart=always \
                        -p 3306:3306 \
                        -e MYSQL_DATABASE=db_testes \
                        -e MYSQL_USER=mysql \
                        -e MYSQL_PASSWORD=mysql \
                        -e MYSQL_ROOT_PASSWORD=rootpassword \
                        -v {self.install_principal}/mysql_bd:/var/lib/mysql \
                        mysql:5.7
                    """
        comandos = [
            container_db,
            ]
        self.remove_container(f'mysql_5_7')
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'mysql_5_7', numero_rede=1)
        
    def instala_wordpress_puro(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        
        self.verifica_container_existe('mysql_5_7', self.instala_mysql_5_7)
        
        dominio_ = dominio.replace('.', '_')
        comando1 = f"docker exec -i mysql_5_7 mysql -uroot -prootpassword -e \"CREATE USER IF NOT EXISTS 'wordpress'@'%' IDENTIFIED BY 'wordpress';\""
        comando2 = f"docker exec -i mysql_5_7 mysql -uroot -prootpassword -e \"CREATE DATABASE IF NOT EXISTS {dominio_}; GRANT ALL PRIVILEGES ON {dominio_}.* TO 'wordpress'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=always \
                        -e WORDPRESS_DB_HOST=mysql_5_7:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME={dominio_} \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
        
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'{dominio_}')
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(dominio, endereco=f'{dominio_}', porta='80')
            self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=0)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=1)
        
    def instala_wordpress(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        
        dominio_ = dominio.replace('.', '_')
        container_db = f"""docker run -d \
                        --name {dominio_}_bd \
                        --restart=always \
                        -e MYSQL_DATABASE=wordpress \
                        -e MYSQL_USER=wordpress \
                        -e MYSQL_PASSWORD=wordpress \
                        -e MYSQL_RANDOM_ROOT_PASSWORD=wordpress \
                        -v {self.install_principal}/wordpress/{dominio_}/mysql:/var/lib/mysql \
                        mysql:5.7
                    """
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=always \
                        -e WORDPRESS_DB_HOST={dominio_}_bd:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME=wordpress \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'{dominio_}_bd')
        self.remove_container(f'{dominio_}')
        comandos = [
            container_db,
            container,
            ]
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(dominio, endereco=f'{dominio_}', porta='80')
            self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=0)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}_bd', numero_rede=1)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=1)

    def limpeza_containers(self,):
        # "docker container prune -f",
        comandos = [
            "docker image prune -a -f",
            "docker volume prune -f",
            "docker network prune -f",
            "docker builder prune -f",
            "docker system prune -a --volumes -f",
        ]
        # "docker system df",
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
        for i in range(2):
            comandos = [
                "apt update && apt upgrade -y",
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
                "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
            ]

            # Executa todos os comandos de instalação do Docker
            resultados = self.executar_comandos(comandos, ignorar_erros=True)
            if 'erro:true' not in resultados[comandos[-1]][-1]:
                break
            else:
                comandos = [
                    f"""sudo rm /etc/apt/sources.list.d/docker.list""",
                    ]
                self.executar_comandos(comandos)

    def start_sync_pastas(self):
        # Solicita ao usuário os caminhos da pasta de origem e destino
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
                            --name rsync-inotify \
                            --restart=always \
                            -v {source_path}:/data/source \
                            -v {target_path}:/data/target \
                            -v /logs:/log \
                            rsync-inotify
                    """
        comandos = [
            f"mkdir -p {source_path}",
            f"mkdir -p {target_path}",
        ]
        resultados = self.executar_comandos(comandos, ignorar_erros=True)
        comandos = [
            f"docker build -t rsync-inotify -f {temp_dockerfile} .",
            f"rm {temp_dockerfile}",
            container,
        ]
        self.remove_container(f'rsync-inotify')
        resultados = self.executar_comandos(comandos)
 
class Sistema(Docker, Executa_comados):
    def __init__(self):
        Docker.__init__(self)
        Executa_comados.__init__(self)
        
    def contagem_regressiva(segundos):
        segundos = 150
        while True:
            print(f'\r{segundos}', end='')  # Atualiza a linha no terminal
            time.sleep(1)
            segundos -= 1
            if segundos <=1:
                exit()
    
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
        
    def ecaminhamentos_portas_tuneis(self,):
        comandos = [
            "",
            "habilitando encaminhamentos portas tuneis.",
            "",
            "Tunel do servidor para maquina que solicita.",
            "ssh -R 180:localhost:80 master@179.105.50.81",
            "Isso significa que qualquer requisição feita para o SERVIDOR na porta 180 será redirecionada para localhost:80 na sua máquina local.",
            "",
            "Tunel da maquina que solicita para o servidor.",
            "ssh -L 17080:localhost:7080 master@179.105.50.81",
            "Esse comando fará com que todo o tráfego na porta 8080 da sua máquina local seja redirecionado para localhost:7080 no seu servidor.",
            "",
            "Use isso para listar os tuneis no servidor:",
            "ps aux | grep \"ssh -fN -L\"",
            "",
            "Use isso para matar os processos de tuneis no servidor:",
            "pkill -f \"ssh -fN -L\"",
            "",
            "Habilitando encaminhamentos de portas:",
            "",
            "Criando backup",
            "sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak",
            "",
            "nano /etc/ssh/sshd_config",
            "Procure no arquivo por GatewayPorts e PermitRootLogin e remova o # dos dois",
            "GatewayPorts yes: assim que a linha tem que ficar.",
            "PermitRootLogin yes: assim que a linha tem que ficar.",
            "",
            "Reinicie o ssh.",
            "sudo systemctl restart ssh"
        ]

        resultado = self.executar_comandos(comandos)
        
    def instalar_interface_gnome_minimal(self,):
        processo = subprocess.run(
            "sudo apt install gnome-shell gnome-session gdm3 gnome-terminal -y",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
    def instalar_interface_xfce(self,):
        """
        Instala a interface XFCE4 se ainda não estiver instalada e a inicia.
        """
        try:
            print("Verificando se o XFCE4 já está instalado...")
            
            # Verifica se o XFCE4 está instalado
            processo = subprocess.run(
                "dpkg -l | grep -q xfce4",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if processo.returncode == 0:
                print("XFCE4 já está instalado.")
            else:
                print("XFCE4 não encontrado. Instalando XFCE4...")
                subprocess.run("sudo apt update", shell=True, check=True)
                subprocess.run("sudo apt install xfce4 -y", shell=True, check=True)
                print("XFCE4 instalado com sucesso.")
            
            # Inicia o XFCE4
            print("Iniciando XFCE4...")
            subprocess.run("startxfce4", shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Erro durante a execução do comando: {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
    
    def setup_wifi(self,):
        print('Instalando gerenciador de WIFI nmtui.')
        comandos = [
            "sudo apt update",
            "sudo apt install -y network-manager",
            "sudo systemctl enable NetworkManager",
            "sudo systemctl start NetworkManager",
            "sudo nmtui"
        ]
        print("Configurando Wi-Fi com NetworkManager...")
        self.executar_comandos(comandos)
    
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
        
    def configura_ip_fixo(self,):
        # Lista interfaces de rede disponíveis
        print("Interfaces de rede disponíveis:")
        interfaces = subprocess.check_output(["ip", "addr"])
        interfaces = interfaces.decode("utf-8").splitlines()
        for line in interfaces:
            if ":" in line:
                print(line.split(":")[1].strip())

        # Solicita o nome da interface
        interface = input("Digite o nome da interface de rede (ex: enp2s0f5): ")

        # Verifica se a interface de rede existe
        try:
            subprocess.check_output(["ip", "addr", "show", interface])
        except subprocess.CalledProcessError:
            print(f"Interface {interface} não encontrada. Verifique o nome e tente novamente.")
            return

        # Solicita o endereço IP e máscara
        ip_address = input("Digite o endereço IP com a máscara (ex: 192.168.0.80/24): ")

        # Solicita o gateway
        gateway = input("Digite o endereço do gateway (ex: 192.168.0.1): ")

        # Solicita os servidores de DNS
        dns = input("Digite os endereços de DNS separados por vírgula (ex: 8.8.8.8,8.8.4.4): ")
        dns_list = [dns.strip() for dns in dns.split(",")]

        # Nome do arquivo de configuração do Netplan
        config_file = "/etc/netplan/00-installer-config.yaml"

        # Fazendo backup do arquivo de configuração existente
        print("Criando backup do arquivo de configuração existente...")
        backup_file = config_file + "_old"
        subprocess.run(["sudo", "cp", config_file, backup_file], check=True)

        # Gerando a estrutura de configuração
        config_data = {
            "network": {
                "version": 2,
                "renderer": "networkd",
                "ethernets": {
                    interface: {
                        "addresses": [ip_address],
                        "routes": [{"to": "default", "via": gateway}],
                        "nameservers": {"addresses": dns_list}
                    }
                }
            }
        }

        # Escrevendo o novo arquivo de configuração em YAML
        print("Gerando novo arquivo de configuração...")
        try:
            with open(config_file, "w") as file:
                yaml.dump(config_data, file, default_flow_style=False)
        except IOError as e:
            print(f"Erro ao escrever no arquivo de configuração: {e}")
            return

        # Aplicando as configurações
        print("Aplicando as configurações...")
        try:
            subprocess.run(["sudo", "netplan", "apply"], check=True)
            print("Configuração concluída com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao aplicar as configurações: {e}")
        
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
            f"sudo parted -s /dev/{disco} mklabel gpt",                            # Define o tipo de tabela de partição como GPT
            f"sudo parted -s -a opt /dev/{disco} mkpart primary ext4 0% 100%",     # Cria a partição ocupando todo o disco
            f"sudo mkfs.ext4 /dev/{disco}1",                                       # Formata a nova partição como ext4
            f"sudo mount /dev/{disco}1 {ponto_montagem}",                          # Monta partição
        ]
        
        # Executa os comandos
        resultado = self.executar_comandos(comandos)
        
        print(f"Partição criada, formatada e montada com sucesso em {ponto_montagem}.")
            
        # Opcional: Adicionar ao /etc/fstab para montagem automática
        adicionar_fstab = input("Deseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.adicionar_ao_fstab(f"/dev/{disco}1", ponto_montagem)
    
    def gerenciar_permissoes(self):
        """
        Altera as permissões de uma pasta e de suas subpastas/arquivos recursivamente.
        Solicita informações ao usuário interativamente.
        """
        # Solicitar o caminho da pasta
        pasta = input("Digite o caminho da pasta: ").strip()
        
        if not os.path.exists(pasta):
            print(f"A pasta '{pasta}' não existe.")
            return
        
        if not os.path.isdir(pasta):
            print(f"'{pasta}' não é uma pasta.")
            return
        
        # Exibir permissões atuais da pasta principal
        permissoes_atual = os.stat(pasta).st_mode
        permissoes_octal = oct(permissoes_atual & 0o777)
        print(f"Permissões atuais de '{pasta}': {permissoes_octal}")
        
        # Solicitar novas permissões
        novas_permissoes = input("Digite as novas permissões em formato octal (ex: 755): ").strip()
        
        try:
            novas_permissoes = int(novas_permissoes, 8)  # Converter de string octal para inteiro
            
            # Alterar permissões da pasta principal
            os.chmod(pasta, novas_permissoes)
            print(f"Permissões de '{pasta}' alteradas para: {oct(novas_permissoes)}")
            
            # Alterar permissões de subpastas e arquivos
            for root, dirs, files in os.walk(pasta):
                for nome in dirs:
                    try:
                        caminho = os.path.join(root, nome)
                        os.chmod(caminho, novas_permissoes)
                        print(f"Permissões alteradas para a pasta: {caminho}")
                    except:
                        print(f"Erro ao alterar permissões para a pasta: {caminho}")
                
                for nome in files:
                    try:
                        caminho = os.path.join(root, nome)
                        os.chmod(caminho, novas_permissoes)
                        print(f"Permissões alteradas para o arquivo: {caminho}")
                    except:
                        print(f"Erro ao alterar permissões para o arquivo: {caminho}")
        except ValueError:
            print("Erro: Permissões inválidas. Certifique-se de digitar um número octal válido.")
        except PermissionError:
            print("Erro: Permissão negada. Execute o script como root para alterar permissões.")
        except Exception as e:
            print(f"Erro ao alterar permissões: {e}")
        
    def ver_uso_espaco_pasta(self):
        pasta = input('Digite o caminho absoluto da pasta que deseja ver o tamanho: ')
        # Garantir que o caminho seja absoluto
        if not pasta.startswith('/'):
            pasta = '/' + pasta
        
        # Validar se o caminho existe
        if not os.path.exists(pasta):
            print(f"O caminho '{pasta}' não existe.")
            return
        
        # Comando para obter tamanhos
        comandos = [
            f"du -h --max-depth=1 {pasta} | sort -hr",
            ]
        resultados = self.executar_comandos(comandos)
        
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
        
    def verificar_instalacao(self, pacote):
        """Verifica se um pacote está instalado no sistema."""
        try:
            resultado = subprocess.run(
                ["dpkg", "-s", pacote],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return resultado.returncode == 0
        except subprocess.CalledProcessError:
            return False
        
    def verifica_temperatura(self):
        if not self.verificar_instalacao("lm-sensors"):
            comandos = [
                "sudo apt update",
                "sudo apt install -y lm-sensors",
                "yes | sudo sensors-detect",
            ]
            self.executar_comandos(comandos)
        # Executar o comando sensors
        self.executar_comandos(["sensors"])
        
    def opcoes_sistema(self):
        print("\nMenu de sistema.\n")
        """Menu de opções"""
        opcoes_menu = [
            ("cria_particao", self.cria_particao),
            ("listar_particoes", self.listar_particoes),
            ("fecha_tela_noot", self.fecha_tela_noot),
            ("Instala interface xfce", self.instalar_interface_xfce),
            ("Instala interface gnome minimal", self.instalar_interface_gnome_minimal),
            ("Ecaminhamentos portas tuneis", self.ecaminhamentos_portas_tuneis),
            ("Instala gerenciador de WIFI nmtui", self.setup_wifi),
            ("Configura ip fixo", self.configura_ip_fixo),
            ("Ver uso do espaço em pasta", self.ver_uso_espaco_pasta),
            ("Gerenciar permissoes de pasta", self.gerenciar_permissoes),
            ("Verificar temperatura", self.verifica_temperatura),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def menu_docker(self):
        print("\nBem-vindo ao Gerenciador Docker\n")
        self.instala_docker()
        """Menu de opções"""
        opcoes_menu = [
            ("Força instalação docker", self.instala_docker_force),
            ("Instala portainer", self.instala_portainer),
            ("Instala traefik", self.instala_traefik),
            ("Adiciona roteamento e serviço ao traefik", self.adiciona_roteador_servico_traefik),
            ("Configura rede do container", self.configura_rede),
            ("Instala filebrowser", self.instala_filebrowser),
            ("Instala webserver ssh", self.instala_webserver_ssh),
            ("Gerenciador SFTP sftpgo", self.gerenciar_usuarios_sftp),
            ("Instala SFTP sftpgo", self.instala_ftp_sftpgo),
            ("Instala mysql_5_7", self.instala_mysql_5_7),
            ("Instala wordpress", self.instala_wordpress),
            ("Instala wordpress puro", self.instala_wordpress_puro),
            ("Instala openlitespeed", self.instala_openlitespeed),
            ("Controle de sites openlitespeed", self.controle_sites_openlitespeed),
            ("Instala app nodejs", self.instala_app_nodejs),
            ("Instala grafana, prometheus, node-exporter", self.iniciar_monitoramento),
            ("Start sync pastas com RSYNC", self.start_sync_pastas),
            ("Instala windows docker", self.instala_windows_docker),
            ("Instala rustdesk", self.instala_rustdesk),
        ]
        self.mostrar_menu(opcoes_menu)
    
    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        comandos = [
            "ip addr show | grep -vE '(docker|br-)' | grep 'inet ' | awk '{split($2, a, \"/\"); print a[1], $NF}'",
        ]
        self.executar_comandos(comandos)
        print('\n')
        
        input('Pressione enter para abrir o monitor de recusos')
        if not self.verificar_instalacao("glances"):
            comandos = [
                "sudo apt update",
                "sudo apt install glances -y",
            ]
            self.executar_comandos(comandos, comando_direto=True)
        comandos = [
                "glances",
            ]
        self.executar_comandos(comandos, comando_direto=True)
    
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
        ("Contagem regressiva", servicos.contagem_regressiva),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("verificando status do sistema", servicos.verificando_status_sistema),
        ("Menu de outras opções", servicos.opcoes_sistema),
        ("Menu Docker", servicos.menu_docker),
        # ("gerenciar_usuarios_sftp", servicos.gerenciar_usuarios_sftp),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()