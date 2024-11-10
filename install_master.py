#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import os
import socket
import subprocess
import time
import yaml
import json

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.82
===========================================================================
===========================================================================
""")

class Executa_comados():
    def __init__(self):
        pass
    
    def executar_comandos(self, comandos:list=[], ignorar_erros=False, exibir_resultados=True):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        resultados = {}
        for comando in comandos:
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
            resultados[comando] = []
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
        
        self.remove_container('traefik')
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
        #print('Porta interna para uso: 80')
        container = f"""docker run -d \
                    --name filebrowser \
                    --restart=always \
                    -p 8082:80 \
                    -v /:/srv \
                    -v {self.install_principal}/database_filebrowser/database.db:/database.db \
                    filebrowser/filebrowser
                """
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container, porta='80')
        
        comandos = [
            # f"rm -r {self.install_principal}/database_filebrowser",
            f"mkdir -p {self.install_principal}/database_filebrowser",
            f"touch {self.install_principal}/database_filebrowser/database.db",
            container,
            ]
        self.remove_container('filebrowser')
        resultados = self.executar_comandos(comandos)
        
    def instala_openlitespeed(self,):
        print("Instalando openlitespeed.")
        container = f"""docker run -d \
                            --name openlitespeed \
                            --restart=always \
                            -p 8088:8088 \
                            -p 7080:7080 \
                            -v {self.install_principal}/openlitespeed/vhosts:/var/www/vhosts/ \
                            -v {self.install_principal}/openlitespeed/conf:/usr/local/lsws/conf \
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
        nome_dominio = input('Digite o dominio: ')
        nome_dominio_ = nome_dominio.replace('.', '_')
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(nome_dominio, endereco='openlitespeed', porta='8088')
        sites_dir = f"{self.install_principal}/openlitespeed"
        # Diretório do site
        #/usr/local/lsws/
        site_dir = os.path.join(sites_dir, "vhosts", nome_dominio_)
        public_html = os.path.join(site_dir, "public_html")
        conf_dir = os.path.join(sites_dir, "conf", "vhosts", nome_dominio_)
        listener_conf_path = os.path.join(sites_dir, "conf", "httpd_config.conf")
        
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
        
        print(f"Configuração do site '{nome_dominio_}' criada com sucesso!")
        print(f"Arquivos criados em: {site_dir}")
        
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
        if not os.path.exists(caminho_index_js):
            # Escreve o conteúdo no arquivo package.json
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
                        node:latest 
                    """
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(self, dominio=nome_dominio, endereco=nome_dominio_, porta=porta)

        container += " bash -c \"npm install && npm start\""
        
        comandos = [
            container,
            ]
        self.remove_container(nome_dominio_)
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'webssh', numero_rede=1)
        
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
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container)
            
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
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
        
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}} {{.Names}}"],
            capture_output=True,
            text=True
        )
        container_info = result.stdout.strip().splitlines()
        db_encontrado = False
        for info in container_info:
            if 'mysql_5_7' in info:
                db_encontrado = True
                break
        if not db_encontrado:
            self.instala_mysql_5_7()
            print('aguarde terminando de instalar o banco de dados...')
            time.sleep(30)
        
        dominio_ = dominio.replace('.', '_')
        comando1 = f"docker exec -i mysql_5_7 mysql -uroot -prootpassword -e \"CREATE USER IF NOT EXISTS 'wordpress'@'%' IDENTIFIED BY 'wordpress';\""
        comando2 = f"docker exec -i mysql_5_7 mysql -uroot -prootpassword -e \"CREATE DATABASE IF NOT EXISTS {dominio_}; GRANT ALL PRIVILEGES ON {dominio_}.* TO 'wordpress'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        container = f"""docker run -d \
                        --name wp_{dominio_} \
                        --restart=always \
                        -e WORDPRESS_DB_HOST=mysql_5_7:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME={dominio_} \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
        
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'wp_{dominio_}')
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'wp_{dominio_}', numero_rede=1)
        
    def instala_wordpress(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        
        dominio_ = dominio.replace('.', '_')
        container_db = f"""docker run -d \
                        --name wp_{dominio_}_bd \
                        --restart=always \
                        -e MYSQL_DATABASE=wordpress \
                        -e MYSQL_USER=wordpress \
                        -e MYSQL_PASSWORD=wordpress \
                        -e MYSQL_RANDOM_ROOT_PASSWORD=wordpress \
                        -v {self.install_principal}/wordpress/{dominio_}/mysql:/var/lib/mysql \
                        mysql:5.7
                    """
        container = f"""docker run -d \
                        --name wp_{dominio_} \
                        --restart=always \
                        -e WORDPRESS_DB_HOST=wp_{dominio_}_bd:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME=wordpress \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'wp_{dominio_}_bd')
        self.remove_container(f'wp_{dominio_}')
        comandos = [
            container_db,
            container,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'wp_{dominio_}_bd', numero_rede=1)
        self.cria_rede_docker(associar_container_nome=f'wp_{dominio_}', numero_rede=1)

    def instala_docker(self,):
        # Executa o comando para verificar se o Docker está instalado
        comando = "command -v docker"
        resultados = self.executar_comandos([comando], ignorar_erros=True)
        if resultados[comando]:
            pass
            print("Intalação docker ok.")
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
        segundos = 90
        while True:
            print(f'\r{segundos}', end='')  # Atualiza a linha no terminal
            time.sleep(1)
            segundos -= 1
            if segundos <=1:
                exit()

        print('\nTempo esgotado!')
    
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
        # self.instala_docker()
        """Menu de opções"""
        opcoes_menu = [
            ("Força instalação docker", self.instala_docker_force),
            ("Instala portainer", self.instala_portainer),
            ("Instala traefik", self.instala_traefik),
            ("Adiciona roteamento e serviço ao traefik", self.adiciona_roteador_servico_traefik),
            ("Configura rede do container", self.configura_rede),
            ("Instala filebrowser", self.instala_filebrowser),
            ("Instala webserver ssh", self.instala_webserver_ssh),
            ("Instala mysql_5_7", self.instala_mysql_5_7),
            ("Instala wordpress", self.instala_wordpress),
            ("Instala wordpress puro", self.instala_wordpress_puro),
            ("Instala openlitespeed", self.instala_openlitespeed),
            ("Controle de sites openlitespeed", self.controle_sites_openlitespeed),
            ("Instala app nodejs", self.instala_app_nodejs),
            ("Instala grafana, prometheus, node-exporter", self.iniciar_monitoramento),
            ("Start sync pastas", self.start_sync_pastas),
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
        ("Contagem regressiva", servicos.contagem_regressiva),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("verificando status do sistema", servicos.verificando_status_sistema),
        ("Menu operações de sistema", servicos.opcoes_sistema),
        ("Menu Docker", servicos.menu_docker),
        ("Ecaminhamentos portas tuneis", servicos.ecaminhamentos_portas_tuneis),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()