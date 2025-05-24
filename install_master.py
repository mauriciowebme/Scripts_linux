#!/bin/bash

# Execute com:
# wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import configparser
import shutil
import socket
import json
import random
import re
import tempfile
import os, sys, time, subprocess, textwrap
from pathlib import Path
from typing import List, Union
from datetime import datetime
try:
    import mysql.connector
except ImportError:
    pass
try:
    import yaml
except ImportError:
    pass

def get_ubuntu_version() -> float:
    """
    Retorna a versão do Ubuntu como float (ex: 22.04).
    Retorna 0.0 se não for possível identificar.
    """
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_ID"):
                    version_str = line.split("=")[1].strip().replace('"', '')
                    return float(version_str)
    except Exception:
        pass
    return 0.0  # padrão em caso de falha

VERSAO_UBUNTU = get_ubuntu_version()

def check_for_update():
    update_file = Path("/install_principal/update_check.txt")
    update_file.parent.mkdir(parents=True, exist_ok=True)

    if update_file.exists():
        return

    print("Primeira execução detectada. Atualizando o sistema...")
    subprocess.run("sudo apt-get update".split(), check=False)
    subprocess.run("sudo apt-get upgrade -y".split(), check=False)
    
    # Evitar espera de rede na inicialização
    subprocess.run("sudo systemctl disable NetworkManager-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl disable systemd-networkd-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl mask systemd-networkd-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl mask NetworkManager-wait-online.service".split(), check=False)
    
    try:
        subprocess.run(["timedatectl", "set-timezone", "America/Sao_Paulo"], check=True)
        subprocess.run(["timedatectl", "set-ntp", "true"], check=True)
    except Exception as ex:
        try:
            subprocess.run(["ln", "-sf", "/usr/share/zoneinfo/America/Sao_Paulo", "/etc/localtime"], check=True)
        except Exception as ex:
            print(f"⚠️  Erro ao atualizar o sistema: {ex}\n")
        
    update_file.write_text("Atualização realizada em: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("Atualização concluída.\n")
    
check_for_update()

def ensure_pip_installed():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"],
                              stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("pip não encontrado. Instalando com apt...")
        subprocess.check_call(["apt-get", "update"])
        subprocess.check_call(["apt-get", "install", "-y", "python3-pip"])
        print("pip instalado com sucesso.\n")
ensure_pip_installed()

def ensure(module: str,
           apt_pkg: str | None = None,
           pip_pkg: str | None = None) -> None:
    """
    Importa <module>. Se falhar:
        1. instala <apt_pkg> via APT (padrão: python3-<module>).
        2. se ainda faltar, instala <pip_pkg> via pip
           (padrão: mesmo nome do módulo).
    """
    import importlib, subprocess, sys, shutil

    # 0) já existe?
    try:
        importlib.import_module(module)
        return
    except ImportError:
        pass

    # 1) define nomes padrão caso não venham
    apt_pkg = apt_pkg or f"python3-{module.replace('.', '-')}"
    pip_pkg = pip_pkg or module

    # 2) tenta instalar via APT
    try:
        subprocess.run(["apt-get", "update", "-qq"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["apt-get", "install", "-y", "--no-install-recommends",
                        apt_pkg], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        importlib.import_module(module)  # checa de novo
        print(f"✓ {module} disponível via APT ({apt_pkg})")
        return
    except Exception:
        print(f"APT falhou para {apt_pkg}; tentando pip…")

    try:
        # 3) fallback: pip
        if shutil.which("pip") is None:
            subprocess.run(["apt-get", "install", "-y", "--no-install-recommends",
                            "python3-pip"], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        pip_cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", pip_pkg]
        if VERSAO_UBUNTU >= 24.04:
            pip_cmd.insert(4, "--break-system-packages")
            
        subprocess.run(pip_cmd, check=True)
        
        print(f"✓ {module} instalado via pip ({pip_pkg})")

        importlib.import_module(module)
        return
    except ImportError:
        print(f"✗ Falha ao instalar {module} via pip ({pip_pkg})")
        pass

# ---- dependências do script ----
ensure("mysql.connector",
       apt_pkg="python3-mysql.connector",
       pip_pkg="mysql-connector-python")
ensure("yaml",
       apt_pkg="python3-yaml",
       pip_pkg="PyYAML")

ensure("glances",
       apt_pkg="python3-glances",
       pip_pkg="glances[web]")


class Executa_comandos():
    def __init__(self):
        pass
    
    def executar_comandos(self, comandos:list=[], ignorar_erros=False, exibir_resultados=True, comando_direto=False, exibir_executando=True, intervalo:int=0):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        resultados = {}
        for comando in comandos:
            if intervalo > 0:
                time.sleep(intervalo)
            resultados[comando] = []
            if exibir_resultados and exibir_executando:
                print("\n" + "*" * 40)
                if comando_direto:
                    print(" " * 5 + "---> Executando comando direto: <---")
                else:
                    print(" " * 5 + "---> Executando comando: <---")
                print(" " * 5 + f"{comando}")
                print("*" * 40 + "\n")
                
            if comando_direto:
                comando_convertido = comando.split()
                try:
                    subprocess.run(comando_convertido, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao executar o comando: {e}")
                    print(f"Código de saída: {e.returncode}")
                    resultados[comando] += [e.returncode]
            else:
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

class Docker(Executa_comandos):
    def __init__(self):
        Executa_comandos.__init__(self)
        self.install_principal = '/install_principal'
        self.bds = self.install_principal+'/bds'
        self.redes_docker = ['_traefik', 'interno']
        self.atmoz_sftp_arquivo_conf = os.path.join(f"{self.install_principal}/atmoz_sftp/", "users.conf")
        
    def executar_comandos_run_OrAnd_dockerfile(self,
                                           run_cmd: list[str],
                                           dockerfile_str: str | None = None) -> None:
        print("\n" + "*" * 40)
        print(" " * 5 + "---> Executando comando: <---")
        print(" " * 5 + f"{run_cmd}")
        if dockerfile_str:
            print(" " * 5 + "---> Executando Dockerfile: <---")
            print(" " * 5 + dockerfile_str.strip().splitlines()[0])
        print("*" * 40 + "\n")

        if dockerfile_str:
            tag = f"img_{datetime.now():%Y%m%d%H%M%S}"
            with tempfile.TemporaryDirectory() as ctx:
                Path(ctx, "Dockerfile").write_text(dockerfile_str.strip() + "\n")
                subprocess.run(["docker", "build", "-t", tag, "."], cwd=ctx, check=True)
            # se quiser manter run_cmd como “somente opções”, adicione o comando aqui
            subprocess.run(["docker", "run", *run_cmd, tag], check=True)
        else:
            subprocess.run(["docker", "run", *run_cmd], check=True)
        
    def escolher_porta_disponivel(self, inicio=40000, fim=40500, quantidade=1):
        portas_disponiveis = []
        print(f"Escolhendo {quantidade} portas disponíveis entre {inicio} e {fim}...")
        for porta in range(inicio, fim + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Tenta se conectar na porta; se falhar, a porta está disponível
                if s.connect_ex(('localhost', porta)) != 0:
                    portas_disponiveis.append(porta)
                    if len(portas_disponiveis) == quantidade:
                        print(f"Portas {portas_disponiveis} estão disponíveis e serão usadas.")
                        return portas_disponiveis
        
        # Se não houver portas suficientes disponíveis no intervalo
        if len(portas_disponiveis) < quantidade:
            print(f"Nenhuma porta disponível entre {inicio} e {fim}.")
            return None

    def cria_rede_docker(self, associar_todos=False, associar_container_nome=False, numero_rede=None, nome_rede=None):
        # Verifica se a rede já existe
        try:
            result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)
            
            if nome_rede != None:
                self.redes_docker = [nome_rede]
                numero_rede = -1
                
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
        
    def comandos_in_container(self, nome_conatiner, comandos, tipo='bash'):
        comandos_conatiners = []
        for comando in comandos:
            comandos_conatiners += [f'docker exec -i -u root {nome_conatiner} {tipo} -c \'{comando}\'']
        self.executar_comandos(comandos_conatiners)
            
    def remove_container(self, nome_container):
        comandos = [
            f'docker rm -f {nome_container}',
            ]
        resultados = self.executar_comandos(comandos)
    
    def generate_password(self, length=16):
        ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
        digits = '0123456789'
        caracteres_especiais = "!@#$%_"  # Caracteres especiais permitidos
        
        # Define os caracteres permitidos: letras, dígitos e símbolos
        characters = ascii_uppercase + ascii_lowercase + digits + caracteres_especiais
        
        # Garante pelo menos um caractere de cada tipo (opcional)
        password = (
            random.choice(ascii_uppercase) +  # Pelo menos uma letra maiúscula
            random.choice(ascii_lowercase) +  # Pelo menos uma letra minúscula
            random.choice(digits) +           # Pelo menos um número
            random.choice(caracteres_especiais)      # Pelo menos um símbolo
        )
        
        # Completa a senha até o comprimento desejado
        password += ''.join(random.choice(characters) for _ in range(length - 4))
        
        # Embaralha os caracteres da senha para evitar padrões previsíveis
        password = ''.join(random.sample(password, len(password)))
        return password
    
    def gerenciar_permissoes_pasta(self, pasta:str=None, permissao:str=None):
        """
        Altera as permissões de uma pasta e de suas subpastas/arquivos recursivamente.
        Solicita informações ao usuário interativamente.
        """
        # Solicitar o caminho da pasta
        if pasta == None:
            pasta = input("Digite o caminho da pasta: ").strip()
        else:
            os.makedirs(pasta, exist_ok=True)
        
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
        if permissao == None:
            novas_permissoes = input("Digite as novas permissões em formato octal (ex: 777): ").strip()
        else:
            novas_permissoes = permissao.strip()
        
        try:
            novas_permissoes = int(novas_permissoes, 8)  # Converter de string octal para inteiro
            
            # Alterar permissões da pasta principal
            os.chmod(pasta, novas_permissoes)
            
            # Alterar permissões de subpastas e arquivos
            for root, dirs, files in os.walk(pasta):
                for nome in dirs:
                    try:
                        caminho = os.path.join(root, nome)
                        os.chmod(caminho, novas_permissoes)
                        # print(f"Permissões alteradas para a pasta: {caminho}")
                    except:
                        print(f"Erro ao alterar permissões para a pasta: {caminho}")
                
                for nome in files:
                    try:
                        caminho = os.path.join(root, nome)
                        os.chmod(caminho, novas_permissoes)
                        # print(f"Permissões alteradas para o arquivo: {caminho}")
                    except:
                        print(f"Erro ao alterar permissões para o arquivo: {caminho}")
            print(f"Permissões de '{pasta}', subpastas e itens alteradas para: {oct(novas_permissoes)}")
        except ValueError:
            print("Erro: Permissões inválidas. Certifique-se de digitar um número octal válido.")
        except PermissionError:
            print("Erro: Permissão negada. Execute o script como root para alterar permissões.")
        except Exception as e:
            print(f"Erro ao alterar permissões: {e}")
        
    def adiciona_redirecionamento_traefik(self, container, dominio=None, porta=None):
        """
        Exemplo de uso:
        
        container = f"docker run -d \
                        --name webssh \
                        --restart=unless-stopped \
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
        labels = rf""" --network {self.redes_docker[0]} \
                --label traefik.enable=true \
                --label traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https \
                --label traefik.http.routers.{dominio_}.rule="Host(`{dominio}`)" \
                --label traefik.http.routers.{dominio_}.entrypoints=web,websecure \
                --label traefik.http.routers.{dominio_}.tls.certresolver=le \
                --label traefik.http.services.{dominio_}.loadbalancer.server.port={porta} \
            """
        container = container + labels.replace( '  ', '' ) + imagem
        return container

    def iniciar_monitoramento(self):
        print("Iniciando instalação de monitoramento com Prometheus, Node Exporter e Grafana.")
        conteudo = textwrap.dedent("""\
        global:
          scrape_interval: 5s
          evaluation_interval: 5s

        scrape_configs:
          - job_name: 'prometheus'
            static_configs:
              - targets: ['mon_prometheus:9090']

          - job_name: 'node_exporter'
            static_configs:
              - targets: ['mon_node-exporter:9100']
        """)

        caminho_prometheus = f'{self.install_principal}/monitoramento/prometheus/prometheus.yml'
        os.makedirs(os.path.dirname(caminho_prometheus), exist_ok=True)
        os.chmod(os.path.dirname(caminho_prometheus), 0o777)
        if not os.path.exists(caminho_prometheus):
            with open(caminho_prometheus, 'w') as f:
                f.write(conteudo)
        
        caminho_grafana = f'{self.install_principal}/monitoramento/grafana'
        os.makedirs(caminho_grafana, exist_ok=True)
        os.chmod(caminho_grafana, 0o777)
        
        # -p 9090:9090 \
        # -p 9100:9100 \
        comandos = [
            f"""docker run -d \
            --name mon_prometheus \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -v {caminho_prometheus}:/etc/prometheus/prometheus.yml \
            prom/prometheus
            """,
            f"""docker run -d \
            --name mon_node-exporter \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            prom/node-exporter
            """,
            f"""docker run -d \
            --name mon_grafana \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -p 3000:3000 \
            -v {caminho_grafana}:/var/lib/grafana \
            grafana/grafana
            """,
        ]
        self.remove_container('mon_prometheus')
        self.remove_container('mon_node-exporter')
        self.remove_container('mon_grafana')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome='mon_prometheus', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='mon_node-exporter', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='mon_grafana', numero_rede=1)
        
        print('Acesse o Grafana em http://<seu_ip>:3000')
        print('Usuario e Senha padrão: admin/admin')
        resposta = input('Deseja ver um exemplo de json para o Grafana?: S ou N: ')
        if resposta.lower() == 's':
            print(textwrap.dedent("""\
            {
                "annotations": {
                    "list": [
                    {
                        "builtIn": 1,
                        "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --"
                        },
                        "enable": true,
                        "hide": true,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                    ]
                },
                "editable": true,
                "fiscalYearStartMonth": 0,
                "graphTooltip": 0,
                "id": 1,
                "links": [],
                "panels": [
                    {
                    "datasource": {
                        "type": "prometheus",
                        "uid": "belsuah7zhqm8d"
                    },
                    "fieldConfig": {
                        "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisBorderShow": false,
                            "axisCenteredZero": false,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "barWidthFactor": 0.6,
                            "drawStyle": "line",
                            "fillOpacity": 0,
                            "gradientMode": "none",
                            "hideFrom": {
                            "legend": false,
                            "tooltip": false,
                            "viz": false
                            },
                            "insertNulls": false,
                            "lineInterpolation": "smooth",
                            "lineStyle": {
                            "fill": "solid"
                            },
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {
                            "type": "linear"
                            },
                            "showPoints": "auto",
                            "spanNulls": false,
                            "stacking": {
                            "group": "A",
                            "mode": "none"
                            },
                            "thresholdsStyle": {
                            "mode": "off"
                            }
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                            {
                                "color": "green"
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                            ]
                        }
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 0
                    },
                    "id": 1,
                    "options": {
                        "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                        "showLegend": true
                        },
                        "tooltip": {
                        "hideZeros": false,
                        "mode": "single",
                        "sort": "none"
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "targets": [
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "disableTextWrap": false,
                        "editorMode": "code",
                        "expr": "100 - (avg by(instance)(\r\n        rate(node_cpu_seconds_total{mode=\"idle\"}[30s])\r\n      ) * 100)",
                        "fullMetaSearch": false,
                        "includeNullMetadata": true,
                        "legendFormat": "CPU",
                        "range": true,
                        "refId": " CPU",
                        "useBackend": false
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "100 * (\r\n  1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)\r\n)",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "RAM",
                        "range": true,
                        "refId": "RAM usada"
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "100 * (\r\n  1 - (node_memory_SwapFree_bytes / ignoring(job,instance) node_memory_SwapTotal_bytes)\r\n)\r\n\r\n",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "SWAP",
                        "range": true,
                        "refId": "SWAP"
                        }
                    ],
                    "title": "Painel principal",
                    "type": "timeseries"
                    },
                    {
                    "datasource": {
                        "type": "prometheus",
                        "uid": "belsuah7zhqm8d"
                    },
                    "fieldConfig": {
                        "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisBorderShow": false,
                            "axisCenteredZero": false,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "barWidthFactor": 0.6,
                            "drawStyle": "line",
                            "fillOpacity": 0,
                            "gradientMode": "none",
                            "hideFrom": {
                            "legend": false,
                            "tooltip": false,
                            "viz": false
                            },
                            "insertNulls": false,
                            "lineInterpolation": "smooth",
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {
                            "type": "linear"
                            },
                            "showPoints": "auto",
                            "spanNulls": false,
                            "stacking": {
                            "group": "A",
                            "mode": "none"
                            },
                            "thresholdsStyle": {
                            "mode": "off"
                            }
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                            {
                                "color": "green"
                            },
                            {
                                "color": "red",
                                "value": 80
                            }
                            ]
                        },
                        "unit": "decmbytes"
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 0
                    },
                    "id": 2,
                    "options": {
                        "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                        "showLegend": true
                        },
                        "tooltip": {
                        "hideZeros": false,
                        "mode": "single",
                        "sort": "none"
                        }
                    },
                    "pluginVersion": "12.0.0",
                    "targets": [
                        {
                        "editorMode": "code",
                        "expr": "rate(node_disk_read_bytes_total{device!~\"^(loop|ram|fd|sr0).*\"}[10s]) / 1024 / 1024",
                        "legendFormat": "Leitura",
                        "range": true,
                        "refId": "A"
                        },
                        {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "felsgfpj8hg5cb"
                        },
                        "editorMode": "code",
                        "expr": "rate(node_disk_written_bytes_total{device!~\"^(loop|ram|fd|sr0).*\"}[10s]) / 1024 / 1024\r\n",
                        "hide": false,
                        "instant": false,
                        "legendFormat": "Escrita",
                        "range": true,
                        "refId": "B"
                        }
                    ],
                    "title": "DISCO",
                    "type": "timeseries"
                    }
                ],
                "preload": false,
                "refresh": "auto",
                "schemaVersion": 41,
                "tags": [],
                "templating": {
                    "list": []
                },
                "time": {
                    "from": "now-5m",
                    "to": "now"
                },
                "timepicker": {},
                "timezone": "browser",
                "title": "Principal dashboard",
                "uid": "e5dc7514-6689-4a2c-a78f-3be4a3be041e",
                "version": 4
            }
            """))
    
    def cria_dynamic_conf_traefik(self, email=None):
        dynamic_conf = f'{self.install_principal}/traefik/dynamic_conf.yml'
        if not os.path.exists(f'{self.install_principal}/traefik/'):
            os.makedirs(f'{self.install_principal}/traefik/', exist_ok=True)
            os.chmod(f'{self.install_principal}/traefik/', 0o777)
        if not os.path.exists(dynamic_conf):
            if email == None:
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
        self.verifica_container_existe('traefik', self.instala_traefik)
        if dominio == None:
            dominio = input('Digite o dominio (sem o www): ')
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
    
        # Criar o serviço para o domínio com o URL de destino e a porta
        config['http']['services'][service_name] = {
            'loadBalancer': {
                'servers': [
                    {'url': f"http://{endereco}:{porta}"}
                ]
            }
        }

        # Salvar o arquivo de configuração atualizado
        with open(dynamic_conf, 'w') as file:
            yaml.dump(config, file)
            
        print(f"Roteador e Serviço adicionados para o domínio: {dominio}")
        print(f"Verifique o arquivo de configuração em: {dynamic_conf}")
        print("\n⚠️ O redirecionamento começa imediatamente, mas pode levar alguns minutos para o DNS se propagar e o Let's Encrypt gerar o certificado resultando em HTTPS ainda não seguro.\n")

    def instala_traefik(self,):
        print("Iniciando instalação do Traefik.")
        email = input('Digite um e-mail para gerar o certificado: ')
        dynamic_conf = self.cria_dynamic_conf_traefik(email=email)
        comandos = [
            f"""docker run -d \
                --name traefik \
                --restart=unless-stopped \
                --memory=1g \
                --cpus=1 \
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
                --certificatesResolvers.le.acme.email={email} \
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
        portas = self.escolher_porta_disponivel()
        container = f"""docker run -d \
                    --name filebrowser \
                    --restart=unless-stopped \
                    --memory=256m \
                    --cpus=1 \
                    -p {portas[0]}:80 \
                    -v /:/srv \
                    -v {self.install_principal}/filebrowser/database.db:/database.db \
                    filebrowser/filebrowser
                """
        
        comandos = [
            # f"rm -r {self.install_principal}/filebrowser",
            f"mkdir -p {self.install_principal}/filebrowser",
            f"touch {self.install_principal}/filebrowser/database.db",
            container,
            ]
        self.remove_container('filebrowser')
        resultados = self.executar_comandos(comandos)
        
        print(f"Possiveis ip's para acesso:")
        comandos = [
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
        ]
        self.executar_comandos(comandos)
        print(f'Porta para uso local: {portas[0]}')
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
                            --restart=unless-stopped \
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
                            --restart=unless-stopped \
                            --memory=1g \
                            --cpus=1 \
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
docRoot                   /var/www/vhosts/{nome_dominio_}/public_html/
vhDomain                  {nome_dominio}
indexFiles                index.php, index.html
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
        self.executar_comandos(['docker restart openlitespeed'], comando_direto=True)
        
        print(f"Configuração do site '{nome_dominio_}' criada com sucesso!")
        print(f"Arquivos criados em: {site_dir}")
        
    def instala_sistema_CISO_docker(self,):
        print("Iniciando instalação do container sistema_CISO.")

        nome = input("Digite o nome do container: ")
        nome = nome.replace('.', '_')
        
        caminho_dados = f"{self.install_principal}/sistema_CISO_{nome}/dados"
        caminho_isos = f"{self.install_principal}/sistema_CISO_{nome}/isos"
        os.makedirs(caminho_dados, exist_ok=True)
        os.makedirs(caminho_isos, exist_ok=True)
        os.chmod(caminho_dados, 0o777)
        os.chmod(caminho_isos, 0o777)
        
        if os.path.exists(f"{caminho_isos}/data.img"):
            resposta = input("A imagem data.img já existe. Deseja sobrescrever? (s/n): ")
            if resposta.lower() == 's':
                os.remove(f"{caminho_isos}/data.img")
            else:
                print("Instalação cancelada.")
                return

        while True:
            if os.path.exists(f"{caminho_isos}/image.iso"):
                break
            else:
                print(f"Coloque a imagem ISO do sistema na pasta {caminho_isos} e pressione ENTER para continuar.")
                input()
                if os.path.exists(f"{caminho_isos}/image.iso"):
                    break
                else:
                    print("A imagem ISO não foi encontrada. Tente novamente.")
        
        run_args = [
            "--name", f"sistema_CISO_{nome}",
            "--restart", "unless-stopped",
            "-e", "BOOT_MODE=legacy",
            "-e", "DISK_SIZE=50G",
            "-e", "BOOT=/boot.iso",
        ]
        # checa suporte KVM
        kvm = subprocess.run("lsmod | grep -q kvm", shell=True).returncode == 0
        if kvm:
            print("Suporte KVM detectado, usando aceleração KVM.")
            net  = "-netdev user,id=net0,hostfwd=tcp::3389-:3389 "
            net += "-device virtio-net-pci,netdev=net0"
            run_args += [
                "-e", 'DISK_TYPE=virtio-blk',
                "-e", f"ARGUMENTS={net} -cpu host -m 4G -smp 2 -vga std",
                # "-e", 'ARGUMENTS=-cpu host -m 4G -smp 2 -vga std',
                "--device", "/dev/kvm",
            ]
        else:
            print("Sem KVM, caindo para TCG (mais lento).")
            net  = "-netdev user,id=net0,hostfwd=tcp::3389-:3389 "
            net += "-device e1000,netdev=net0"
            run_args += [
                "-e", "DISK_TYPE=ide",
                "-e", 'KVM=N',
                "-e", f"ARGUMENTS={net} -accel tcg,thread=multi -cpu Westmere -m 2G -smp 2 -vga std"
                # "-e", 'ARGUMENTS=-accel tcg,thread=multi -cpu Westmere -m 2G -smp 2 -vga std',
            ]
        self.portas_disponiveis = self.escolher_porta_disponivel(quantidade=2)
        run_args += [
            "-p", f"{self.portas_disponiveis[0]}:8006",
            "-p", f"{self.portas_disponiveis[1]}:3389",
            "--cap-add", "NET_ADMIN",
            "--device", "/dev/net/tun",
            "-v", f"{caminho_isos}/image.iso:/boot.iso:ro",
            "-v", f"{caminho_dados}:/storage",
            "--stop-timeout", "120",
            "-d",
            "qemux/qemu",
        ]

        self.remove_container(f"sistema_CISO_{nome}")
        self.executar_comandos_run_OrAnd_dockerfile(
            run_cmd=run_args
        )

        print("\nInstalação do sistema_CISO concluída.\n")
        print("IPs possíveis para acesso:")
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        resultados = self.executar_comandos(comandos)
        print("Portas de acesso:")
        print(f" - Porta Web: {self.portas_disponiveis[0]}")
        print(f" - Porta RDP: {self.portas_disponiveis[1]}")
    
    def instala_windows_KVM_docker(self,):
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
        memoria = input('Digite a quantidade de memoria GB(apenas numeros): ')
        cpu = input('Digite a quantidade de CPUs (apenas numeros): ')
        disco = input('Digite tamanho do disco GB(apenas numeros): ')
        print('\n')
        portas = self.escolher_porta_disponivel(quantidade=2)
        self.remove_container(f'windows_{nome_container}')

        comandos = [
            f"""sudo docker run -d \
                    --name windows_{nome_container} \
                    --restart=unless-stopped \
                    -p {portas[0]}:3389/tcp \
                    -p {portas[0]}:3389/udp \
                    -p {portas[1]}:8006 \
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
        print(f' - Porta Web: {portas[1]}, desative no painel do portainer depois de usar apenas localmente!')
        print(f' - Porta RDP: {portas[0]}')
        
    def instala_nextcloud(self,):
        print('Instalando nextcloud...')
        local = input('Digite o local para armazenamento dos dados: Ex /install_principal/nextcloud: ')
        
        self.verifica_container_existe('mysql_8_0', self.instala_mysql_8_0)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        comando1 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'nextcloud'@'%' IDENTIFIED BY 'nextcloud';\""
        comando2 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS nextcloud_bd; GRANT ALL PRIVILEGES ON nextcloud_bd.* TO 'nextcloud'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        
        comandos = [
            f"""docker run -d \
                    --name nextcloud \
                    --restart=unless-stopped \
                    --memory=1g \
                    --cpus=1 \
                    -p 8585:80 \
                    -e MYSQL_DATABASE=nextcloud_bd \
                    -e MYSQL_PASSWORD=nextcloud \
                    -e MYSQL_USER=nextcloud \
                    -e MYSQL_HOST=mysql_8_0:3306 \
                    -v {local}:/var/www/html \
                    nextcloud
                """,
            ]
        self.remove_container('nextcloud')
        resultados = self.executar_comandos(comandos)
        time.sleep(30)
        
        service_name = "cron.php"
        
        # Conteúdo do arquivo de serviço
        service_content = f"""[Unit]
Description=Nextcloud Cron Job
ConditionPathExists=!/tmp/{service_name}.lock

[Service]
ExecStartPre=/bin/touch /tmp/{service_name}.lock
ExecStart=/usr/bin/docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php
ExecStartPost=/bin/rm -f /tmp/{service_name}.lock
TimeoutStartSec=900
User=root
    """
        timer_content = f"""[Unit]
Description=Run {service_name}.service every 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
    """

        # Caminho do arquivo de serviço
        service_path = f"/etc/systemd/system/{service_name}.service"
        timer_path = f"/etc/systemd/system/{service_name}.timer"

        try:
            # Escreve o arquivo de serviço
            with open(service_path, "w") as f:
                f.write(service_content)
            print(f"Serviço {service_name}.service criado com sucesso em {service_path}")
            
            with open(timer_path, "w") as f:
                f.write(timer_content)
            print(f"Serviço {service_name}.service criado com sucesso em {timer_path}")

            # Recarrega o systemd para reconhecer o novo serviço
            os.system("sudo systemctl daemon-reload")

            # Ativa o serviço
            os.system(f"sudo systemctl enable {service_name}.timer")
            os.system(f"sudo systemctl start {service_name}.timer")
            os.system(f"sudo systemctl status {service_name}.timer")
            print(f"Timer {service_name}.timer ativado e iniciado com sucesso.")

        except PermissionError:
            print("Erro: Permissão negada. Execute o script como superusuário (sudo).")
        except Exception as e:
            print(f"Erro ao criar o serviço: {e}")
        
        # comandos = [
        #     f"echo '*/15 * * * * docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php' | sudo crontab -",
        #     ]
        # self.executar_comandos(comandos)
        
        self.cria_rede_docker(associar_container_nome=f'nextcloud', numero_rede=1)
        print("Instalação concluída. Nextcloud está pronto para uso.")
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos, exibir_executando=False)
        print("porta de acesso: 8585")
        print("Processos para automatizar:")
        print("A cada 5 mimutos:")
        print("docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php")
        print("Rodar fora de orario de pico uma vez ao dia:")
        print("docker exec -u www-data nextcloud php occ maintenance:repair --include-expensive")
        
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
        
    def instala_code_server(self,):
        print('Instalando code-server.')
        senha = input('Coloque a senha que deseja para acesso: ')
        comandos = [
            f"""docker run -d \
                    --name=code-server \
                    --restart=unless-stopped \
                    -p 8443:8443 \
                    -e PASSWORD={senha} \
                    -e SUDO_PASSWORD={senha} \
                    -v {self.install_principal}/code-server:/config \
                    lscr.io/linuxserver/code-server:latest
                """,
            ]
        self.remove_container('code-server')
        resultados = self.executar_comandos(comandos)
        
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
        
    def instala_app_nodejs(self,):
        nome_dominio = input('Digite o dominio sem o www ou nome do projeto: ')
        desenvolvimento = input('O container é para desenvolvimento?: (s/n): ')
        
        if desenvolvimento.lower() != 's':
            senha_ftp = input('Digite uma senha para acessar por SFTP: ')
        
        # self.verifica_container_existe('redis', self.instala_redis_docker)
        nome_dominio_ = nome_dominio.replace('.', '_')
        portas = self.escolher_porta_disponivel()
        
        diretorio_projeto = f"{self.install_principal}/node/{nome_dominio_}"
        # Verifica se o diretório do projeto já existe
        if os.path.exists(diretorio_projeto):
            resposta = input(f"O diretório {diretorio_projeto} já existe. Deseja removê-lo? (s/n): ")
            if resposta.lower() == 's':
                comandos = [
                    f"rm -rf {diretorio_projeto}",
                ]
                self.executar_comandos(comandos)
        self.gerenciar_permissoes_pasta(diretorio_projeto, '777')
        
        dir_dados_arquivos = f"{diretorio_projeto}/arquivos"
        os.makedirs(dir_dados_arquivos, exist_ok=True)
        
        dir_dados_assets = f"{diretorio_projeto}/assets"
        os.makedirs(dir_dados_assets, exist_ok=True)
        
        dir_dados_assets_public = f"{dir_dados_assets}/public"
        os.makedirs(dir_dados_assets_public, exist_ok=True)
        
        dir_dados_assets_scripts_python = f"{dir_dados_assets}/scripts_python"
        os.makedirs(dir_dados_assets_scripts_python, exist_ok=True)
        
        dir_dados_assets_scripts_node = f"{dir_dados_assets}/scripts_node"
        os.makedirs(dir_dados_assets_scripts_node, exist_ok=True)
        
        if desenvolvimento.lower() != 's':
            self.gerenciar_usuarios_sftp(manual=False, simples_usuario=nome_dominio_, simples_senha=senha_ftp, simples_base_diretorio=diretorio_projeto)
        
        # Define a estrutura do package.json
        package_json = {
            "name": nome_dominio_,
            "version": "1.0",
            "main": "index.js",
            "scripts": {
                "prestart": "npm install",
                "start": "nodemon"
            },
            "dependencies": {
                "nodemon": "^2.0.0",
                "express": "^4.17.2"
            },
        }
        # Caminho para o arquivo package.json 
        caminho_package_json = os.path.join(diretorio_projeto, "package.json")
        if not os.path.exists(caminho_package_json):
            # Escreve o conteúdo no arquivo package.json
            with open(caminho_package_json, "w") as arquivo:
                json.dump(package_json, arquivo, indent=4)
            print(f"Arquivo package.json criado em {caminho_package_json}")
            
        sftp_json = {
            "name": "Nome do Projeto",
            "host": "seuservidorsftp.com",
            "username": "usuario",
            "password": "senha",
            "port": 2025,
            "protocol": "sftp",
            "remotePath": "/",
            "uploadOnSave": False,
            "syncMode": "full",
            "deleteRemote": True,
            "ignore": [
                "package-lock.json",
                "arquivos",
                ".git",
                "python_env",
                "node_modules"
            ]
        }
        # Caminho para o arquivo sftp.json
        caminho_sftp_json = os.path.join(diretorio_projeto, ".vscode", "sftp.json")
        os.makedirs(os.path.dirname(caminho_sftp_json), exist_ok=True)
        if not os.path.exists(caminho_sftp_json):
            # Escreve o conteúdo no arquivo nodemon.json
            with open(caminho_sftp_json, "w") as arquivo:
                json.dump(sftp_json, arquivo, indent=4)
            print(f"Arquivo nodemon.json criado em {caminho_sftp_json}")
            
        yml_content = textwrap.dedent("""\
            name: SFTP Deploy

            on:
            push:
                branches:
                - main

            concurrency:
            group: sftp-deploy
            cancel-in-progress: false

            jobs:
            deploy:
                name: Deploy via SFTP
                runs-on: ubuntu-latest

                steps:
                - name: Checkout repository
                    uses: actions/checkout@v3

                - name: Install LFTP
                    run: sudo apt-get install -y lftp

                - name: Deploy files to server
                    env:
                    SFTP_HOST: ${{ secrets.SFTP_HOST }}
                    SFTP_USER: ${{ secrets.SFTP_USER }}
                    SFTP_PASSWORD: ${{ secrets.SFTP_PASSWORD }}
                    run: |
                    lftp -u "$SFTP_USER","$SFTP_PASSWORD" sftp://$SFTP_HOST:2025 <<EOF
                    set sftp:connect-program "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
                    mirror --reverse --only-newer --ignore-time --verbose \\
                    --exclude-glob .git/ \\
                    --exclude-glob node_modules/ \\
                    --exclude-glob python_env/ \\
                    --exclude-glob arquivos/ \\
                    --exclude-glob package-lock.json \\
                    ./ /
                    bye
                    EOF
            """)
        
        caminho_yml = os.path.join(diretorio_projeto, ".github", "workflows", "sftp-deploy.yml")
        os.makedirs(os.path.dirname(caminho_yml), exist_ok=True)
        if not os.path.exists(caminho_yml):
            with open(caminho_yml, "w") as arquivo:
                arquivo.write(yml_content)
            print(f"Arquivo sftp-deploy.yml criado em {caminho_yml}")
            
        nodemon_json = {
            "ignore": [
                "/root/.npm/**/*",
                ".vscode",
                "package-lock.json",
                "arquivos",
                ".git",
                "python_env",
                "node_modules",
                "*.log*"
            ],
            "exec": "npm install && node index.js"
        }
        # Caminho para o arquivo nodemon.json
        caminho_nodemon_json = os.path.join(diretorio_projeto, "nodemon.json")
        if not os.path.exists(caminho_nodemon_json):
            # Escreve o conteúdo no arquivo nodemon.json
            with open(caminho_nodemon_json, "w") as arquivo:
                json.dump(nodemon_json, arquivo, indent=4)
            print(f"Arquivo nodemon.json criado em {caminho_nodemon_json}")
            
        index_html = textwrap.dedent("""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bem-vindo</title>
            <style>
                body {
                margin: 0;
                font-family: Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                background: linear-gradient(135deg, #6a11cb, #2575fc);
                color: white;
                text-align: center;
                }
                h1 {
                font-size: 3rem;
                margin-bottom: 0.5rem;
                }
                p {
                font-size: 1.5rem;
                margin-bottom: 1rem;
                }
                .button-container {
                margin-top: 2rem;
                }
                a {
                text-decoration: none;
                color: #ffffff;
                background-color: #ff7f50;
                padding: 0.8rem 1.5rem;
                border-radius: 5px;
                font-size: 1.2rem;
                transition: background-color 0.3s ease;
                }
                a:hover {
                background-color: #ff6347;
                }
            </style>
            </head>
            <body>
                <div>
                    <h1>Bem-vindo ao Servidor Node.js com Python.</h1>
                    <p>Seu ambiente está configurado e funcionando corretamente.</p>
                    <div class="button-container">
                    <a href="/teste">Ir para a pagina de teste</a>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Caminho para o arquivo index.html
        caminho_index_html = os.path.join(dir_dados_assets_public, "index.html")
        if not os.path.exists(caminho_index_html):
            # Cria e escreve o conteúdo no arquivo index.html
            with open(caminho_index_html, "w") as arquivo:
                arquivo.write(index_html)
            print(f"Arquivo index.html criado em {caminho_index_html}")

        index_js = textwrap.dedent(f"""\
            require('./assets/scripts_node/start.js');
            """)
        
        # Caminho para o arquivo index.js
        caminho_index_js = os.path.join(diretorio_projeto, "index.js")
        if not os.path.exists(caminho_index_js):
            # Escreve o conteúdo no arquivo index.js
            with open(caminho_index_js, "w") as arquivo:
                arquivo.write(index_js)
            print(f"Arquivo index.js criado em {caminho_index_js}")
            
        start_js = textwrap.dedent(f"""\
            // Importa o setupPythonEnv
            const {{ setupPythonEnv, runPythonScript }} = require('./setupPythonEnv');
            const express = require('express');
            const app = express();
            const PORT = {portas[0]};
            const path = require('path');

            // Diretório publico do projeto
            app.use('/public', express.static(path.join(__dirname, '../public')));

            // Diretório raiz do projeto
            const projectRoot = path.dirname(require.main.filename);

            pythonOutput = 'Aguardando ambiente Python...';

            app.listen(PORT, () => {{
            console.log(`Servidor rodando na porta {portas[0]}`);
            }});

            ///////////////////////////////////////////////////////////////////////////////////////////////////
            // Criação de rotas Nodejs adicionais aqui...

            // Rota de testes
            app.get('/teste', (req, res) => {{
            const responseText = `
            Servidor Node.js com Express funcionando!<br>
            ${{pythonOutput}}
            `;
            res.send(responseText);
            }});

            // Rota index.html
            app.get('/', (req, res) => {{
            const htmlPath = path.join(projectRoot, 'assets', 'public', 'index.html');
            res.sendFile(htmlPath);
            }});

            ///////////////////////////////////////////////////////////////////////////////////////////////////

            // Configura o ambiente Python em paralelo
            setupPythonEnv(() => {{
            console.log('Terminada a configuração do ambiente Python.');
            
            ///////////////////////////////////////////////////////////////////////////////////////////////////
            // Rotas dos scripts Python
            
            // Rota do start.py
            runPythonScript('start.py', (error, output) => {{
            if (error) {{
                console.error('Erro ao executar o script:', error);
                return;
            }}
                console.log('Saída recebida do script Python:', output);
                pythonOutput = output; // Armazena o resultado do script
            }});
            
            ///////////////////////////////////////////////////////////////////////////////////////////////////

            }});
            """)
        
        # Caminho para o arquivo start.js
        caminho_start_js = os.path.join(dir_dados_assets_scripts_node, "start.js")
        if not os.path.exists(caminho_start_js):
            # Escreve o conteúdo no arquivo start.js
            with open(caminho_start_js, "w") as arquivo:
                arquivo.write(start_js)
            print(f"Arquivo start.js criado em {caminho_start_js}")
        
        # Conteúdo do arquivo setupPythonEnv.js
        setup_python_env_js = textwrap.dedent("""\
            const { exec } = require('child_process');
            const path = require('path');
            const fs = require('fs');

            // Diretório raiz do projeto
            const projectRoot = path.dirname(require.main.filename);

            const scripts_python = path.join(projectRoot, 'assets', 'scripts_python'); // Diretório do ambiente virtual Python
            const pythonDir = path.join(projectRoot, 'python_env'); // Diretório do ambiente virtual Python
            const pythonBin = path.join(pythonDir, 'bin', 'python'); // Python do ambiente virtual
            const pipPath = path.join(pythonDir, 'bin', 'pip');
            const requirementsFile = path.join(projectRoot, 'requirements.txt');

            // Instala Python3 e ferramentas necessárias
            function installPython(callback) {
            const installCmd = 'apt update && apt install -y python3 python3-pip python3-venv';

            console.log('Instalando Python3 e ferramentas...');
            exec(installCmd, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao instalar Python3: ' + stderr);
                return;
                }
                console.log('Python3 e ferramentas instalados com sucesso.');
                if (callback) callback();
            });
            }

            // Cria o ambiente virtual, se necessário
            function createVirtualEnv(callback) {
            console.log('Criando ambiente virtual...');
            exec('python3 -m venv ' + pythonDir, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao criar o ambiente virtual: ' + stderr);
                return;
                }
                console.log('Ambiente virtual criado com sucesso.');
                if (callback) callback();
            });
            }

            // Instala dependências do arquivo requirements.txt
            function installDependencies(callback) {
            if (!fs.existsSync(requirementsFile)) {
                console.error('Erro: O arquivo requirements.txt não foi encontrado.');
                return;
            }

            console.log('Instalando dependências no ambiente virtual...');
            exec(pipPath + ' install -r ' + requirementsFile, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao instalar dependências: ' + stderr);
                return;
                }
                console.log('Dependências instaladas com sucesso.');
                if (callback) callback();
            });
            }

            // Configura o ambiente Python
            function setupPythonEnv(callback) {
            if (fs.existsSync(path.join(pythonDir, 'bin', 'python'))) {
                console.log('Ambiente virtual já existe. Instalando dependências...');
                installDependencies(() => {
                if (callback) callback();
                });
            } else {
                console.log('Ambiente virtual não encontrado. Atualizando ferramentas e criando...');
                installPython(() => {
                createVirtualEnv(() => {
                    installDependencies(() => {
                    if (callback) callback();
                    });
                });
                });
            }
            }

            // Função para garantir que um script Python exista (como "start.py")
            function createStartPy() {
            // Garante que o diretório de scripts Python exista
            if (!fs.existsSync(scripts_python)) {
                console.log(`Criando o diretório: ${scripts_python}`);
                fs.mkdirSync(scripts_python, { recursive: true });
                console.log(`Diretório ${scripts_python} criado com sucesso.`);
            }
            
            const scriptPath = path.join(scripts_python, 'start.py');
            if (!fs.existsSync(scriptPath)) {
                console.log(`Criando o script ${path.basename(scriptPath)}...`);
                const content = `# ${path.basename(scriptPath)}\nprint("O ambiente Python está funcionando corretamente!")\n`;
                fs.writeFileSync(scriptPath, content);
                console.log(`Script ${path.basename(scriptPath)} criado com sucesso.`);
            } else {
                console.log(`O script ${path.basename(scriptPath)} já existe.`);
            }
            }

            // Função para rodar o script Python com nome dinâmico e capturar a saída via callback
            function runPythonScript(scriptName, callback) {
            const scriptPy = path.join(scripts_python, scriptName);

            // Verifica se o script fornecido existe
            if (!fs.existsSync(scriptPy)) {
                console.warn(`O script "${scriptName}" não foi encontrado. Rodando o script padrão para testes "start.py"...`);
                createStartPy(); // Garante que start.py exista
                runPythonScript('start.py', callback); // Rechama a função para rodar o start.py
                return;
            }

            console.log(`Executando o script Python: ${scriptName}...`);

            exec(`${pythonBin} ${scriptPy}`, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao executar o script Python: ' + stderr);
                callback(stderr, null);
                return;
                }
                console.log('Script Python executado com sucesso.');
                // console.log(stdout);
                callback(null, stdout); // Passa a saída do script para o callback
            });
            }

            module.exports = { setupPythonEnv, runPythonScript };
            """)
        
        # Caminho para o arquivo setupPythonEnv.js
        caminho_setup_python_env_js = os.path.join(dir_dados_assets_scripts_node, "setupPythonEnv.js")
        if not os.path.exists(caminho_setup_python_env_js):
            # Escreve o conteúdo no arquivo setupPythonEnv.js
            with open(caminho_setup_python_env_js, "w") as arquivo:
                arquivo.write(setup_python_env_js)
            print(f"Arquivo setupPythonEnv.js criado em {caminho_setup_python_env_js}")
        
        # Lista de dependências
        dependencias = [
            "psycopg2",
            "xmltodict",
            "paramiko"
        ]
        # Caminho para o arquivo requirements.txt
        caminho_requirements = os.path.join(diretorio_projeto, "requirements.txt")
        # Escreve as dependências no arquivo
        if not os.path.exists(caminho_requirements):
            with open(caminho_requirements, "w") as arquivo:
                arquivo.write("\n".join(dependencias))
        desenvolvimento_atuvacao = 'npm start'
        if desenvolvimento.lower() == 's':
            desenvolvimento_atuvacao = 'sleep infinity'
            
        print(f'Porta interna para uso: {portas[0]}')
        
        comandos = [
            f"""docker run -d \
                --name {nome_dominio_} \
                --restart=unless-stopped \
                --memory=256m \
                --cpus=1 \
                -p {portas[0]}:{portas[0]} \
                -v {diretorio_projeto}:/usr/src/app:rw \
                -w /usr/src/app \
                node:latest \
                /bin/sh -c \"{desenvolvimento_atuvacao}\"
            """,
            ]
        self.remove_container(nome_dominio_)
        self.gerenciar_permissoes_pasta(diretorio_projeto, '777')
        self.executar_comandos(comandos)
        
        print("Instalação concluída. O projeto está pronto para uso.")
        print(f"Acesse o projeto pelo IP do servidor na porta {portas[0]}")
    
    def instala_ftp_sftpgo(self,):
        print('Instalando o ftp_sftpgo.\n')
        
        dir_dados = f"{self.install_principal}/ftp_sftpgo/dados"
        os.makedirs(dir_dados, exist_ok=True)
        os.chmod(dir_dados, 0o777)
        
        container = f"""docker run -d \
                        --name ftp_sftpgo \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -p 2025:2022 \
                        -p 8085:8080 \
                        -e SFTPGO_COMMON__IDLE_TIMEOUT=1 \
                        -e SFTPGO_COMMON__MAX_TOTAL_CONNECTIONS=200 \
                        -e SFTPGO_FILESYSTEM_UID=0 \
                        -e SFTPGO_FILESYSTEM_GID=0 \
                        -v {self.install_principal}:/install_principal \
                        -v {dir_dados}:/var/lib/sftpgo \
                        drakkan/sftpgo
                    """
        comandos = [
            container,
            ]
        self.remove_container(f'ftp_sftpgo')
        resultados = self.executar_comandos(comandos)
        print("sftpgo instalado com sucesso.")
        print("Instalação concluída. FTP SFTPGo está pronto para uso.")
        print("porta de acesso: 8085")
        print("Usuario e senha padrão: Vc cria no primeiro acesso. ")
        print("Crie o usuario admin e uma senha forte.")
        
    def gerenciar_usuarios_sftp(self, manual=True, simples_usuario=None, simples_senha=None, simples_base_diretorio=None):
        """
        Documentação:
        
        https://sftpgo.stoplight.io/docs/sftpgo/vjevihcqw0gy4-get-a-new-admin-access-token
        """
        
        self.verifica_container_existe('ftp_sftpgo', self.instala_ftp_sftpgo)
        
        max_attempts = 5
        admin_usuario = 'admin'
        admin_senha = 'admin'
        import requests
        from requests.auth import HTTPBasicAuth
        for attempt in range(max_attempts):
            if attempt > 0:
                print('\nUsuario e senha para permissão de administração FTP:')
                admin_usuario = input('Usuario admin: ')
                admin_senha = input('Senha: ')
            
            url = "http://localhost:8085/api/v2/token"
            response = requests.get(url, auth=HTTPBasicAuth(admin_usuario, admin_senha))
            if response.status_code == 200:
                print("Logado com sucesso\n")
                token = response.json()['access_token']
                break
            else:
                print(f"Usuario sem permissão ou não existe. Tentativas restantes: {max_attempts - attempt - 1}")
            if attempt == max_attempts - 1:
                print("Número máximo de tentativas atingido. Saindo...")
                exit()
            
        if manual:
            print('Digite os dados para criação do novo usuario FTP:')
            simples_usuario = input('Digite o nome de usuario: ')
            simples_senha = input('Digite uma senha: ')
            simples_base_diretorio = input('Digite um diretorio dentro de /install_principal começando com /. (Ex: /teste): ')
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
        
    def instala_webserver_guacamole(self,):
        self.verifica_container_existe('mysql_8_0', self.instala_mysql_8_0)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para acessar o MySQL e criar o banco: ")
            
        # Verifica se a senha está correta antes de prosseguir
        max_attempts = 3
        for attempt in range(max_attempts):
            test_cmd = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e 'SELECT 1;'"
            result = self.executar_comandos([test_cmd], exibir_resultados=False)
            
            # Verifica se o comando foi executado com sucesso (sem erro)
            if test_cmd in result and 'Erro:True' not in str(result[test_cmd]):
                print("Senha MySQL verificada com sucesso.")
                break
            else:
                if attempt < max_attempts - 1:
                    print(f"Senha incorreta. Tentativa {attempt + 1}/{max_attempts}")
                    self.mysql_root_password = input("Digite a senha root para o MySQL novamente: ")
                else:
                    print("Número máximo de tentativas excedido. Saindo...")
                    return
        
        # Verifica se a base de dados guacamole_db já existe
        comando_verifica_db = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"SHOW DATABASES LIKE 'guacamole_db';\""
        resultado = self.executar_comandos([comando_verifica_db])
        
        if not any('guacamole_db' in line for line in resultado[comando_verifica_db]):
            comando1 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'guacamole_user'@'%' IDENTIFIED BY 'guacamole_password';\""
            comando2 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS guacamole_db; GRANT ALL PRIVILEGES ON guacamole_db.* TO 'guacamole_user'@'%'; FLUSH PRIVILEGES;\""
            comando3 = f"docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > initdb.sql"
            comando4 = f"docker cp initdb.sql mysql_8_0:/initdb.sql"
            comando5 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' guacamole_db -e \"SOURCE /initdb.sql;\""
            self.executar_comandos([comando1, comando2, comando3, comando4, comando5])
        else:
            print("A base de dados guacamole_db já existe.")
        
        # caminho_guacamole = f"{self.install_principal}/guacamole"
        # self.gerenciar_permissoes_pasta(caminho_guacamole, '777')
        # -v {caminho_guacamole}/guacamole:/etc/guacamole \
        container_guacamole = f"""docker run -d \
            --name guacamole \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -p 8086:8080 \
            -e GUACD_HOSTNAME=guacamole_guacd \
            -e MYSQL_HOSTNAME=mysql_8_0 \
            -e MYSQL_DATABASE=guacamole_db \
            -e MYSQL_USER=guacamole_user \
            -e MYSQL_PASSWORD=guacamole_password \
            guacamole/guacamole:latest
        """
        # Container do Guacd
        container_guacd = """docker run -d \
            --name guacamole_guacd \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            guacamole/guacd:latest
        """
        
        comandos = [
            container_guacamole,
            container_guacd,
            ]
        self.remove_container('guacamole')
        self.remove_container('guacamole_guacd')
        resultados = self.executar_comandos(comandos)
        
        self.cria_rede_docker(associar_container_nome='guacamole', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='guacamole_guacd', numero_rede=1)
        
        print('Instalação do guacamole completa.\n')
        print('Acesse: http://<seu_ip>:8086/guacamole')
        print('Usuario: guacadmin')
        print('Senha: guacadmin')
        
    def instala_postgres(self, selecao=None):
        if not selecao:
            selecao = input('Selecione a versão: \n1 - 15 \n2 - 16 \n3 - 17\n')
        if selecao == "1" or selecao == "15":
            versao = '15'
            porta = '5433'
            porta_slave = '5435'
        elif selecao == "2" or selecao == "16":
            versao = '16'
            porta = '5434'
            porta_slave = '5436'
        elif selecao == "3" or selecao == "17":
            versao = '17'
            porta = '5435'
            porta_slave = '5437'
        else:
            print("Seleção incorreta.")
            return

        if not hasattr(self, 'postgres_password') or not self.postgres_password:
            self.postgres_password = input("Digite a senha do usuário postgres: ")

        versao_ = versao.replace('.', '_')

        replicacao = input('Habilitar a replicação de dados? (s/n): ')
        if replicacao.lower() == 's':
            local_slave = input(f'Informe o local para armazenar o Postgres SLAVE (/mnt/dados resultado: /mnt/dados/postgres/{versao_}_slave): ')

        print('Instalando o Postgres.\n')

        if replicacao.lower() == 's':
            container_db = f"""docker run -d \
            --name postgres_{versao_} \
            --restart=unless-stopped \
            --memory=1g \
            --cpus=1 \
            -p {porta}:5432 \
            -e POSTGRES_PASSWORD={self.postgres_password} \
            -v {self.bds}/postgres/{versao_}:/var/lib/postgresql/data \
            -v {local_slave}/postgres/{versao_}_slave:/mnt/_slave \
            postgres:{versao}"""
        else:
            container_db = f"""docker run -d \
            --name postgres_{versao_} \
            --restart=unless-stopped \
            --memory=1g \
            --cpus=1 \
            -p {porta}:5432 \
            -e POSTGRES_PASSWORD={self.postgres_password} \
            -v {self.bds}/postgres/{versao_}:/var/lib/postgresql/data \
            postgres:{versao}"""

        comandos = [container_db]
        self.remove_container(f'postgres_{versao_}')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'postgres_{versao_}', numero_rede=1)

        time.sleep(30)

        if replicacao.lower() == 's':
            container_db_slave = f"""docker run -d \
                                --name postgres_{versao_}_slave \
                                --restart=unless-stopped \
                                --memory=1g \
                                --cpus=1 \
                                -p {porta_slave}:5432 \
                                -e POSTGRES_PASSWORD={self.postgres_password} \
                                -v {local_slave}/postgres/{versao_}_slave:/var/lib/postgresql/data \
                                postgres:{versao}"""

            comandos = [container_db_slave]
            self.remove_container(f'postgres_{versao_}_slave')
            self.executar_comandos(comandos)
            self.cria_rede_docker(associar_container_nome=f'postgres_{versao_}_slave', numero_rede=1)
            
            time.sleep(30)

            master_container = f"postgres_{versao_}"
            slave_container = f"postgres_{versao_}_slave"

            replication_user = 'replication_user'

            replication_password = self.generate_password()

            self.configure_postgres_replication(master_container, slave_container, replication_user, replication_password)

        print(f'Instalação do Postgres completa.\n')
        print(f'Acesso:')
        print(f' - ssh -L {porta}:localhost:{porta} usuario@servidor_remoto')
        print(f' - Local instalação: {self.bds}/postgres/{versao_}')
        print(f' - Usuario: postgres')
        print(f' - Senha: {self.postgres_password}')
        print(f' - Porta interna: 5432')
        print(f' - Porta externa: {porta}')
        
    def configure_postgres_replication(self, master_container, slave_container, replication_user, replication_password):
        try:
            print("Configurando replicação...")

            # 1. Configurar o Master
            print("Configurando o Master...")
            master_commands = [
                f"docker exec {master_container} bash -c \"echo 'wal_level = replica' >> /var/lib/postgresql/data/postgresql.conf\"",
                f"docker exec {master_container} bash -c \"echo 'max_wal_senders = 5' >> /var/lib/postgresql/data/postgresql.conf\"",
                f"docker exec {master_container} bash -c \"echo 'host replication {replication_user} 0.0.0.0/0 md5' >> /var/lib/postgresql/data/pg_hba.conf\"",
                f"docker exec {master_container} bash -c \"psql -U postgres -c \\\"CREATE ROLE {replication_user} REPLICATION LOGIN ENCRYPTED PASSWORD '{replication_password}';\\\"\"",
            ]

            self.executar_comandos(master_commands)

            # Reiniciar o Master para aplicar as mudanças
            self.executar_comandos([f"docker restart {master_container}"])
            print("Master configurado com sucesso.")

            # 2. Preparar o Slave
            print("Preparando o Slave...")
            self.executar_comandos([f"docker stop {slave_container}"])
            self.executar_comandos([
                f"docker exec {master_container} bash -c \"rm -rf /mnt/_slave/*\"",
                f"docker exec {master_container} bash -c \"pg_basebackup -h localhost -D /mnt/_slave -U {replication_user} -Fp -Xs -P -R\""
            ])
            self.executar_comandos([f"docker start {slave_container}"])
            time.sleep(10)
            self.executar_comandos([
                f"docker exec {slave_container} bash -c \"echo \\\"primary_conninfo = 'host={master_container} port=5432 user={replication_user} password={replication_password}'\\\" >> /var/lib/postgresql/data/postgresql.auto.conf\""
            ])
            self.executar_comandos([f"docker restart {slave_container}"])
            print("Slave preparado com sucesso.")

        except Exception as ex:
            print(f"Erro na configuração da replicação: {ex}")

    def instala_mysql_5_7(self,):
        self.instala_mysql('5.7')
    
    def instala_mysql_8_0(self,):
        self.instala_mysql('8.0')
    
    def instala_mysql(self, selecao=None):
        
        if not selecao:
            selecao = input('Selecione a versão: \n1 - 5.7 \n2 - 8.0\n')
        if selecao == "1" or selecao == "5.7":
            versao = '5.7'
            porta = '3316'
            porta_slave = '3318'
        elif selecao == "2" or selecao == "8.0":
            versao = '8.0'
            porta = '3317'
            porta_slave = '3319'
        else:
            print("Seleção incorreta.")
            return
        
        versao_ = versao.replace('.', '_')
        novo_db = True
        pasta_bd = f'{self.bds}/mysql/{versao_}'
        
        if os.path.exists(pasta_bd):
            print('Tem uma pasta de instalação de banco de dados existente.')
            resposta = input('Deseja remover a pasta de banco de dados existente? s|n: ')
            
            if resposta.lower() == 's':
                shutil.rmtree(pasta_bd)
                os.makedirs(pasta_bd, exist_ok=True)
                os.chmod(pasta_bd, 0o777)
                # Verifica se o objeto 'self' possui o atributo 'root_password'.
                if not hasattr(self, 'root_password') and novo_db:
                    self.mysql_root_password = input("Digite a senha root para o MySQL: ")
            
            else:
                novo_db = False
                self.mysql_root_password = ''
        else:
            # Verifica se o objeto 'self' possui o atributo 'root_password'.
            if not hasattr(self, 'root_password') and novo_db:
                self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        if novo_db:
            replicacao = input('Habilitar a replicação de dados? (s/n): ')
            if replicacao.lower() == 's':
                local_slave = input(f'Informe o local para armazenzar o Mysql SLAVE (/mnt/dados resultado: /mnt/dados/mysql/{versao_}_slave): ')
        
        print('Instalando o mysql.\n')
        # self.gerenciar_permissoes_pasta(f"{self.install_principal}/mysql/{versao_}", permissao="777")
        
        # docker_file = textwrap.dedent(f"""\
        #     FROM mysql:8.0

        #     # Instala cron
        #     RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

        #     # Cria diretório de backup
        #     RUN mkdir -p /backup

        #     # Adiciona script de backup diretamente
        #     RUN echo '#!/bin/bash\n\
        #     DATE=$(date +%F_%H-%M)\n\
        #     BACKUP_DIR="/backup"\n\
        #     MYSQL_USER="root"\n\
        #     MYSQL_PASS="$MYSQL_ROOT_PASSWORD"\n\
        #     MYSQL_HOST="localhost"\n\
        #     mysqldump -h $MYSQL_HOST -u$MYSQL_USER -p$MYSQL_PASS --all-databases > $BACKUP_DIR/backup_$DATE.sql\n'\
        #     > /usr/local/bin/backup.sh && chmod +x /usr/local/bin/backup.sh

        #     # Cria agendamento no crontab (todo dia às 2h da manhã)
        #     RUN echo '0 2 * * * root /usr/local/bin/backup.sh >> /var/log/cron.log 2>&1' > /etc/cron.d/mysql-backup

        #     # Aplica o cron agendado
        #     RUN crontab /etc/cron.d/mysql-backup

        #     # Cria log para o cron
        #     RUN touch /var/log/cron.log

        #     # Comando para iniciar cron e MySQL juntos
        #     CMD service cron start && docker-entrypoint.sh mysqld
        #     """)
        # self.executar_comandos_run_OrAnd_dockerfile(dockerfile_str=docker_file, run_cmd=None)
        
        container_db = f"""docker run -d \
                        --name mysql_{versao_} \
                        --restart=unless-stopped \
                        --memory=1g \
                        --cpus=1 \
                        -p {porta}:3306 \
                        -e MYSQL_DATABASE=db_testes \
                        -e MYSQL_USER=testes \
                        -e MYSQL_PASSWORD=testes \
                        -e MYSQL_ROOT_PASSWORD="{self.mysql_root_password}" \
                        -v {self.bds}/mysql/{versao_}:/var/lib/mysql \
                        mysql:{versao} \
                        --server-id=1 \
                        --log-bin=mysql-bin \
                        --binlog-format=row \
                        --default-authentication-plugin=mysql_native_password
                    """
        comandos = [
            container_db,
        ]
        self.remove_container(f'mysql_{versao_}')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'mysql_{versao_}', numero_rede=1)
        
        if novo_db:
            # Remove o usuário root com host '%', mantendo apenas o usuário root com host 'localhost'.
            # time.sleep(30)
            # comando para limitar as permissões do root
            # comandos = [
            #     # f"docker exec -i mysql_{versao_} mysql -uroot -p'{self.mysql_root_password}' -e \"UPDATE mysql.user SET Host='172.%' WHERE User='root' AND Host='%'; FLUSH PRIVILEGES;\""
            #     f"docker exec -i mysql_{versao_} mysql --user=root --password=\"{self.mysql_root_password}\" -e \"UPDATE mysql.user SET Host='172.%' WHERE User='root' AND Host='%'; FLUSH PRIVILEGES;\""
            # ]
            # self.executar_comandos(comandos)
            
            if replicacao.lower() == 's':
                # time.sleep(10)
                # self.gerenciar_permissoes_pasta(f"{local_slave}/mysql/{versao_}_slave", permissao="777")
                container_db = f"""docker run -d \
                                --name mysql_{versao_}_slave \
                                --restart=unless-stopped \
                                -p {porta_slave}:3306 \
                                -e MYSQL_DATABASE=db_testes \
                                -e MYSQL_USER=testes \
                                -e MYSQL_PASSWORD=testes \
                                -e MYSQL_ROOT_PASSWORD={self.mysql_root_password} \
                                -v {local_slave}/mysql/{versao_}_slave:/var/lib/mysql \
                                mysql:{versao} \
                                --server-id=2 \
                                --log-bin=mysql-bin \
                                --binlog-format=row \
                                --default-authentication-plugin=mysql_native_password
                            """
                comandos = [
                    container_db,
                ]
                self.remove_container(f'mysql_{versao_}_slave')
                resultados = self.executar_comandos(comandos)
                self.cria_rede_docker(associar_container_nome=f'mysql_{versao_}_slave', numero_rede=1)
                
                # Remove o usuário root com host '%', mantendo apenas o usuário root com host 'localhost'.
                time.sleep(30)
                comandos = [
                    f"docker exec -i mysql_{versao_}_slave mysql -uroot -p'{self.mysql_root_password}' -e \"UPDATE mysql.user SET Host='172.%' WHERE User='root' AND Host='%'; FLUSH PRIVILEGES;\""
                ]
                self.executar_comandos(comandos)
                
                master_container = f"mysql_{versao_}"
                master_host = f'localhost'
                master_user = 'root'
                master_password = self.mysql_root_password
                master_porta = f'{porta}'
                
                slave_container = f"mysql_{versao_}_slave"
                slave_host = f'localhost'
                slave_user = 'root'
                slave_password = self.mysql_root_password
                slave_porta = f'{porta_slave}'
                
                replication_user = 'replication_user'
                replication_password = self.generate_password()
                
                time.sleep(10)
                self.configure_mysql_replication(master_container, master_host, master_user, master_password, master_porta,
                                                slave_container, slave_host, slave_user, slave_password, slave_porta,
                                                replication_user, replication_password)
        else:
            del self.mysql_root_password
        
        time.sleep(10)
        print(f'Instalação do Mysql completa.')
        print(f'Acesso:')
        print(f' - ssh -L {porta}:localhost:{porta} usuario@servidor_remoto')
        print(f' - Local instalação: {self.bds}/mysql/{versao_}')
        print(f' - Usuario: root')
        if hasattr(self, 'mysql_root_password'):
            print(f' - Senha: {self.mysql_root_password}')
        else:
            print(f' - Senha: já definida anteriormente.')
        print(f' - Porta interna: 3306')
        print(f' - Porta externa: {porta}')
        
    def configure_mysql_replication(self, master_container, master_host, master_user, master_password, master_porta,
                                slave_container, slave_host, slave_user, slave_password, slave_porta,
                                replication_user, replication_password):
        try:
            # ------------------------- Conectar ao Master -----------------------------
            print("Conectando ao Master...")
            erro_conect = False
            for x in range(10):
                try:
                    master_conn = mysql.connector.connect(
                        host=master_host,
                        user=master_user,
                        password=master_password,
                        port=master_porta
                    )
                    master_cursor = master_conn.cursor()
                    print("Conexão com o Master estabelecida.")
                    erro_conect = False
                    # time.sleep(10)
                    break
                except Exception as ex:
                    time.sleep(10)
                    erro_conect = True
                    
            if erro_conect:
                print('Erro ao conectar ao Master.')
                return
            # -------------------------------------------------------------------------
            
            # ------------------------- Conectar ao Slave -----------------------------
            print("Conectando ao Slave...")
            erro_conect = False
            for x in range(10):
                try:
                    slave_conn = mysql.connector.connect(
                        host=slave_host,
                        user=slave_user,
                        password=slave_password,
                        port=slave_porta
                    )
                    slave_cursor = slave_conn.cursor()
                    print("Conexão com o Slave estabelecida.")
                    erro_conect = False
                    # time.sleep(10)
                    break
                except Exception as ex:
                    time.sleep(10)
                    erro_conect = True
                    
            if erro_conect:
                print('Erro ao conectar ao Slave.')
                return
            # -------------------------------------------------------------------------

            # Criar usuário de replicação no Master
            master_cursor.execute(f"CREATE USER IF NOT EXISTS '{replication_user}'@'172.%' IDENTIFIED BY '{replication_password}';")
            master_cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{replication_user}'@'172.%';")
            master_cursor.execute("FLUSH PRIVILEGES;")
            print("Usuário de replicação criado com sucesso no Master.")
            
            # Criar usuário de replicação no Slave
            slave_cursor.execute(f"CREATE USER IF NOT EXISTS '{replication_user}'@'172.%' IDENTIFIED BY '{replication_password}';")
            slave_cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{replication_user}'@'172.%';")
            slave_cursor.execute("FLUSH PRIVILEGES;")
            print("Usuário de replicação criado com sucesso no Slave.")

            # Obter informações do log binário do Master
            master_cursor.execute("SHOW MASTER STATUS;")
            result = master_cursor.fetchone()
            if result:
                master_log_file = result[0]
                master_log_pos = result[1]
                print(f"Master Log File: {master_log_file}, Position: {master_log_pos}")
            else:
                print("Erro: Não foi possível obter o status do log binário do Master.")
                return
            
            # Obter informações do log binário do Slave
            slave_cursor.execute("SHOW MASTER STATUS;")
            result = slave_cursor.fetchone()
            if result:
                slave_log_file = result[0]
                slave_log_pos = result[1]
                print(f"Slave Log File: {slave_log_file}, Position: {slave_log_pos}")
            else:
                print("Erro: Não foi possível obter o status do log binário do Slave.")
                return

            # Configurar o Master com informações do Slave
            master_cursor.execute("STOP SLAVE;")
            porta_interna = '3306'
            master_cursor.execute(f"""
                CHANGE MASTER TO
                MASTER_HOST='{slave_container}',
                MASTER_PORT={porta_interna},
                MASTER_USER='{replication_user}',
                MASTER_PASSWORD='{replication_password}',
                MASTER_LOG_FILE='{slave_log_file}',
                MASTER_LOG_POS={slave_log_pos};
            """)
            master_cursor.execute("START SLAVE;")
            print("Replicação configurada com sucesso no Slave.")
            
            # Configurar o Slave com informações do Master
            slave_cursor.execute("STOP SLAVE;")
            porta_interna = '3306'
            slave_cursor.execute(f"""
                CHANGE MASTER TO
                MASTER_HOST='{master_container}',
                MASTER_PORT={porta_interna},
                MASTER_USER='{replication_user}',
                MASTER_PASSWORD='{replication_password}',
                MASTER_LOG_FILE='{master_log_file}',
                MASTER_LOG_POS={master_log_pos};
            """)
            slave_cursor.execute("START SLAVE;")
            print("Replicação configurada com sucesso no Slave.")
            
            # Verificar a versão do Master
            master_cursor.execute("SELECT VERSION();")
            master_version = master_cursor.fetchone()[0]
            print(f"Versão do Master: {master_version}")
            
            # Verificar a versão do Slave
            slave_cursor.execute("SELECT VERSION();")
            slave_version = slave_cursor.fetchone()[0]
            print(f"Versão do Slave: {slave_version}")

            # Verificar o status do Master com base na versão
            if master_version.startswith("5.7"):
                print("Verificando status da replicação para MASTER MySQL 5.7...")
                master_cursor.execute("SHOW SLAVE STATUS;")
            else:
                print("Verificando status da replicação para MASTER MySQL 8.0...")
                master_cursor.execute("SHOW REPLICA STATUS;")
            for row in master_cursor:
                print(row)
                
            # Verificar o status do Slave com base na versão
            if slave_version.startswith("5.7"):
                print("Verificando status da replicação para SLAVE MySQL 5.7...")
                slave_cursor.execute("SHOW SLAVE STATUS;")
            else:
                print("Verificando status da replicação para SLAVE MySQL 8.0...")
                slave_cursor.execute("SHOW REPLICA STATUS;")
            for row in slave_cursor:
                print(row)

        except Exception as ex:
            print(f"Erro: {ex}")

        finally:
            # Fechar conexões
            if 'master_conn' in locals() and master_conn.is_connected():
                master_cursor.close()
                master_conn.close()
                print("Conexão com o Master fechada.")
            if 'slave_conn' in locals() and slave_conn.is_connected():
                slave_cursor.close()
                slave_conn.close()
                print("Conexão com o Slave fechada.")
        
    def instala_wordpress_puro(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        
        self.verifica_container_existe('mysql_5_7', self.instala_mysql_5_7)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        dominio_ = dominio.replace('.', '_')
        comando1 = f"docker exec -i mysql_5_7 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'wordpress'@'%' IDENTIFIED BY 'wordpress';\""
        comando2 = f"docker exec -i mysql_5_7 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS {dominio_}; GRANT ALL PRIVILEGES ON {dominio_}.* TO 'wordpress'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
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
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        dominio_ = dominio.replace('.', '_')
        container_db = f"""docker run -d \
                        --name {dominio_}_bd \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -e MYSQL_DATABASE=wordpress \
                        -e MYSQL_USER=wordpress \
                        -e MYSQL_PASSWORD=wordpress \
                        -e MYSQL_RANDOM_ROOT_PASSWORD={self.mysql_root_password} \
                        -v {self.install_principal}/wordpress/{dominio_}/mysql:/var/lib/mysql \
                        mysql:5.7
                    """
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
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
        print("A instalação do Docker requer uma reinicialização do sistema. Deseja continuar? (s/n)")
        resposta = input().strip().lower()
        if resposta != 's':
            print("Instalação cancelada pelo usuário.")
            os._exit(0)
        user = input("Digite o nome do usuário com permissões de acesso extra: ")
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
                    "reboot"
                    ]
                self.executar_comandos(comandos, comando_direto=True)

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
 
    def instala_open_webui(self):
        caminho_ollama = f"{self.install_principal}/ollama"
        
        print("Escolha o modelo:")
        print("1. llama3.3")
        print("2. llama2")
        print("3. Instalar ambos")
        print("4. Instalar modelo manualmente posteriormente")
        escolha = input('Digite o número do modelo: ').strip()
        
        if escolha == '1':
            modelos = ['llama3.3']
        elif escolha == '2':
            modelos = ['llama2']
        elif escolha == '3':
            modelos = ['llama3.3', 'llama2']
        elif escolha == '4':
            modelos = []
            print("Para instalar um modelo manualmente posteriormente, use o comando:")
            print("docker exec -it ollama bash -c \"ollama pull llama3.3\"")
        else:
            print("Opção inválida. Escolha entre '1', '2', '3' ou '4'.")
            return
        
        comandos = [
            "docker network create ollama-network",
            f"""docker run -d \
            --name ollama \
            --network ollama-network \
            -p 11434:11434 \
            -v {caminho_ollama}:/root \
            ollama/ollama""",
        ]
        
        for modelo in modelos:
            comandos.append(f"""docker exec -it ollama bash -c "ollama pull {modelo}" """)
        
        comandos += [
            """docker exec -it ollama bash -c "ollama list" """,
            """docker run -d \
            --name open-webui \
            --network ollama-network \
            -p 3000:8080 \
            -e OLLAMA_BASE_URL=http://ollama:11434 \
            ghcr.io/open-webui/open-webui:main"""
        ]
        
        # Adiciona permissão 777 no caminho persistente do container ollama
        self.gerenciar_permissoes_pasta(caminho_ollama, '777')
        
        self.remove_container(f'open-webui')
        self.remove_container(f'ollama')
        self.executar_comandos(comandos, ignorar_erros=True)
        
    def instala_redis_docker(self):
        print("Iniciando instalação redis:")
        senha = input("Configure uma senha para acessar: ")
        container = f"""docker run -d \
                        --name redis \
                        --restart=unless-stopped \
                        --memory=512m \
                        --cpus=1 \
                        -p 6379:6379 \
                        redis redis-server --requirepass "{senha}"
                    """
        comandos = [container]
        self.remove_container('redis')
        resultados = self.executar_comandos(comandos)
        print("Instalação do Redis concluída.")
        print("")
        print("Porta de acesso: 6379")
        print("")
        print("Realize testes assim:")
        print("docker exec -it redis redis-cli")
        print("")
        print("AUTH sua_senha_aqui")
        print('set meu-teste "funcionando"')
        print("get meu-teste")
        print("")
        
    def ubuntu(self):
        """Instala e executa o ubuntu."""
        print("Iniciando instalação ubuntu:")

        nome = "teste"
        senha = "teste"
        # nome = input("Digite um nome para o container: ")
        # senha = input("Configure uma senha para acessar: ")
        
        os.makedirs(f"{self.install_principal}/ubuntu_{nome}", exist_ok=True)
        os.chmod(f"{self.install_principal}/ubuntu_{nome}", 0o777)
        self.remove_container(f"ubuntu_{nome}")
        porta = self.escolher_porta_disponivel()[0]

        dockerfile = textwrap.dedent(f"""\
        FROM ubuntu:22.04

        ENV DEBIAN_FRONTEND=noninteractive
        ENV container=docker

        # instala o servidor
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            openssh-server \
            sudo \
            systemd systemd-sysv dbus \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # Instala os pacotes básicos
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            wget \
            gdebi \
            python3 \
            python3-pip \
            htop \
            unzip p7zip-full unrar \
            xarchiver thunar-archive-plugin \
            && apt-get clean && rm -rf /var/lib/apt/lists/*

        # cria usuário não-root
        ARG USER=master
        ARG UID=1000
        RUN useradd -m -u $UID -s /bin/bash $USER \
            && echo "$USER:{senha}" | chpasswd \
            && usermod -aG sudo $USER \
            && echo "$USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

        # habilita login por chave SSH
        RUN mkdir -p /home/$USER/.ssh && chown $USER:$USER /home/$USER/.ssh

        # prepara o diretório do daemon
        RUN mkdir /var/run/sshd
        
        # habilita o serviço SSH para subir junto com o systemd
        RUN systemctl enable ssh
        EXPOSE 22
        
        # --- GUI ---
        RUN apt-get update && \
            apt-get install -y xfce4 xfce4-goodies xrdp && \
            systemctl enable xrdp \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        EXPOSE 3389
            
        # ----- Instala o chrome -----
        # Instala dpendencias do chrome
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            libxss1 \
            libappindicator3-1 \
            libindicator7 \
            fonts-liberation \
            libatk-bridge2.0-0 \
            libgtk-3-0 \
            xdg-utils \
            libgbm-dev \
            dbus-x11 \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # Instala o Google Chrome
        RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
            | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg && \
            echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] \
            http://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list && \
            apt-get update && \
            apt-get install -y --no-install-recommends google-chrome-stable \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
            
        # Instala atalho Google Chrome
        # Cria o wrapper sem here-doc
        RUN mkdir -p /usr/local/bin && \
            echo '#!/bin/bash' > /usr/local/bin/chrome-wrapper.sh && \
            echo 'exec /usr/bin/google-chrome-stable --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu "$@"' \
            >> /usr/local/bin/chrome-wrapper.sh && \
            chmod +x /usr/local/bin/chrome-wrapper.sh

        # Cria o atalho do Chrome no menu apontando pro wrapper
        RUN mkdir -p /usr/share/applications && \
            echo '[Desktop Entry]'                                       > /usr/share/applications/google-chrome.desktop && \
            echo 'Name=Google Chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Comment=Navegador Web'                                >> /usr/share/applications/google-chrome.desktop && \
            echo 'Exec=/usr/local/bin/chrome-wrapper.sh %U'             >> /usr/share/applications/google-chrome.desktop && \
            echo 'Terminal=false'                                       >> /usr/share/applications/google-chrome.desktop && \
            echo 'Type=Application'                                     >> /usr/share/applications/google-chrome.desktop && \
            echo 'Icon=google-chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Categories=Network;WebBrowser'                        >> /usr/share/applications/google-chrome.desktop && \
            echo 'StartupNotify=true'                                   >> /usr/share/applications/google-chrome.desktop && \
            chmod +x /usr/share/applications/google-chrome.desktop
        # ----- termina instalação do chrome -----
        
        VOLUME [ "/sys/fs/cgroup" ]
        
        STOPSIGNAL SIGRTMIN+3
        CMD ["/sbin/init"]
        """)

        run_args = [
            "--name", f"ubuntu_{nome}",
            "-p", "2222:22",
            "-p", "3389:3389",
            "--cgroupns=host",
            "--privileged",
            "-v", "/sys/fs/cgroup:/sys/fs/cgroup:rw",
            "-d"
        ]

        self.executar_comandos_run_OrAnd_dockerfile(
            dockerfile_str=dockerfile,
            run_cmd=run_args
        )

        print("\nInstalação do ubuntu concluída.")
        
    def desktop_ubuntu_webtop(self):
        """Instala e executa o Webtop."""
        print("Iniciando instalação webtop:")

        dockerfile = textwrap.dedent("""\
        FROM linuxserver/webtop:ubuntu-xfce

        RUN echo 'Executa como root e evita prompts interativos'
        USER root
        ENV DEBIAN_FRONTEND=noninteractive

        RUN echo 'Atualiza o sistema'
        RUN apt-get update && \
            apt-get upgrade -y
        
        RUN echo 'Instala os pacotes básicos'
        #--no-install-recommends
        RUN apt-get install -y \
            wget \
            curl \
            gdebi \
            python3 \
            python3-pip \
            htop \
            unzip p7zip-full unrar \
            file-roller xarchiver thunar-archive-plugin
            
        RUN echo 'Instala dpendencias do chrome'
        RUN apt-get install -y \
            libxss1 \
            libappindicator3-1 \
            libindicator7 \
            fonts-liberation \
            libatk-bridge2.0-0 \
            libgtk-3-0 \
            xdg-utils \
            libgbm-dev \
            dbus-x11
        
        RUN echo 'Instala o Google Chrome'
        RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
            | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg && \
            echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] \
            http://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list && \
            apt-get update && \
            apt-get install -y --no-install-recommends google-chrome-stable && \
            apt-get clean && rm -rf /var/lib/apt/lists/*
            
        RUN echo 'Instala atalho Google Chrome'
        RUN echo 'Cria o wrapper sem here-doc'
        RUN mkdir -p /usr/local/bin && \
            echo '#!/bin/bash' > /usr/local/bin/chrome-wrapper.sh && \
            echo 'exec /usr/bin/google-chrome-stable --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu "$@"' \
            >> /usr/local/bin/chrome-wrapper.sh && \
            chmod +x /usr/local/bin/chrome-wrapper.sh

        RUN echo 'Cria o atalho do Chrome no menu apontando pro wrapper'
        RUN mkdir -p /usr/share/applications && \
            echo '[Desktop Entry]'                                       > /usr/share/applications/google-chrome.desktop && \
            echo 'Name=Google Chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Comment=Navegador Web'                                >> /usr/share/applications/google-chrome.desktop && \
            echo 'Exec=/usr/local/bin/chrome-wrapper.sh %U'             >> /usr/share/applications/google-chrome.desktop && \
            echo 'Terminal=false'                                       >> /usr/share/applications/google-chrome.desktop && \
            echo 'Type=Application'                                     >> /usr/share/applications/google-chrome.desktop && \
            echo 'Icon=google-chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Categories=Network;WebBrowser'                        >> /usr/share/applications/google-chrome.desktop && \
            echo 'StartupNotify=true'                                   >> /usr/share/applications/google-chrome.desktop && \
            chmod +x /usr/share/applications/google-chrome.desktop

        RUN apt-mark hold google-chrome-stable
        
        RUN echo 'Habilita universe'
        RUN apt-get update \
            && apt-get install -y --no-install-recommends software-properties-common \
            && add-apt-repository universe \
            && rm -rf /var/lib/apt/lists/*
        
        RUN echo 'Instala suporte a pt_BR e IBus para XFCE'
        RUN apt-get update \
            && apt-get install -y --no-install-recommends \
            locales \
            language-pack-pt-base \
            hunspell-pt-br \
            ibus \
            ibus-gtk \
            ibus-gtk3 

        RUN echo 'Gera e define o locale pt_BR.UTF-8'
        RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
            && locale-gen pt_BR.UTF-8 \
            && update-locale LANG=pt_BR.UTF-8 LANGUAGE=pt_BR:pt LC_ALL=pt_BR.UTF-8

        RUN echo 'Define como default para todo o container'
        ENV LANG=pt_BR.UTF-8 \
            LANGUAGE=pt_BR:pt \
            LC_ALL=pt_BR.UTF-8
            
        RUN echo 'Adiciona ABNT2 ao iniciar o XFCE'
        RUN echo "setxkbmap -layout br -variant abnt2" >> /etc/xdg/xfce4/xinitrc
        
        RUN curl https://rclone.org/install.sh | sudo bash
        
        RUN echo 'Realiza limpeza'
        RUN apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # # volta ao usuário “abc” (ou UID/GID correto)
        # USER abc
        """)
        
        nome = input("Digite um nome para o container: ")
        self.remove_container(f"webtop_{nome}")
        
        senha = ''
        caminho_principal = f"{self.install_principal}/webtop_{nome}"
        # Verificar se o caminho já existe
        if os.path.exists(caminho_principal):
            resposta = input(f"O caminho {caminho_principal} já existe. Deseja apagá-lo? (s/n): ")
            if resposta.lower() == 's':
                print(f"Removendo diretório existente: {caminho_principal}")
                try:
                    os.chmod(caminho_principal, 0o777)
                    shutil.rmtree(caminho_principal)
                    print(f"Diretório {caminho_principal} removido com sucesso.")
                except Exception as e:
                    print(f"Erro ao remover diretório: {e}")
                    return
                senha = input("Configure uma senha para acessar o webtop: ")
            else:
                print("Mantendo diretório existente.")
        else:
            senha = input("Configure uma senha para acessar o webtop: ")
            print(f"Criando novo diretório: {caminho_principal}")
        
        # Criar o diretório para o container
        os.makedirs(caminho_principal, exist_ok=True)
        os.chmod(caminho_principal, 0o777)
        
        porta = self.escolher_porta_disponivel()[0]
        run_args = [
            "--name", f"webtop_{nome}",
            "--restart=unless-stopped",
            "-e", "PUID=1000",
            "-e", "PGID=1000",
            "-e", "TZ=America/Sao_Paulo",
            "-e", "CUSTOM_USER=master",
            "-e", f"PASSWORD={senha}",
            "-p", f"{porta}:3000",
            "--shm-size", f"2g",
            "-v", f"{self.install_principal}/webtop_{nome}/config:/config",
            "-d"
        ]
        
        self.executar_comandos_run_OrAnd_dockerfile(
            dockerfile_str=dockerfile,
            run_cmd=run_args
        )

        print("\nInstalação do Webtop concluída.")
        print(f"Acesse: http://<seu_servidor>:{porta}")
        print("Usuário: master")
        print(f"Senha: {senha}")
        
    def rclone(self):
        """Instala e executa o rclone."""
        print("\nIniciando instalação rclone:")
        print(40*"*")
        print(40*"*")
        print("Para mais informações acesse: https://rclone.org")
        print(40*"*")
        print(40*"*")
        
        self.remove_container("rclone-setup")
        self.remove_container("rclone")

        conf_path = f"{self.install_principal}/rclone/config"
        run_args1 = [
            "--name", "rclone-setup",
            "-it",
            "-v", f"{conf_path}:/config/rclone",
            "--rm",
            "rclone/rclone:latest",
            "config",
        ]

        self.executar_comandos_run_OrAnd_dockerfile( run_cmd=run_args1 )
        
        # 1) Carrega o arquivo
        read_conf_path = os.path.join(conf_path, "rclone.conf")
        config = configparser.ConfigParser()
        config.read(read_conf_path)

        # 2) Para cada seção (remote), cria a pasta no host
        base_mount = f"{self.install_principal}/rclone/rclone_remotes"
        base_container = "/data"
        entrypoint = []
        for remote in config.sections():
            # remote é algo como 'gdrive', 'nextcloud', 'dropbox', etc.
            dest = os.path.join(base_mount, remote)
            dest_cont = os.path.join(base_container, remote)
            subprocess.run(["fusermount3", "-u", dest], check=False)
            os.makedirs(dest, exist_ok=True)
            os.chmod(dest, 0o777)
            entrypoint.append(f"mkdir -p {dest_cont} && chmod 777 {dest_cont}; ")
            # --no-update-config
            # entrypoint.append(f"rclone mount {remote}: /data/{remote} & ")
            # entrypoint.append(f"rclone mount {remote}: /data/{remote} --vfs-cache-mode=full & ")
            entrypoint.append(f"rclone mount {remote}: /data/{remote} "
                    f"--vfs-cache-mode=full "
                    f"--vfs-cache-max-size=10M "
                    f"--vfs-cache-max-age=1m "
                    f"--dir-cache-time=30s "
                    f"--poll-interval=30s "
                    f"& ")
        
        entrypoint.append("wait")
        # Concatena tudo numa única string
        entrypoint = "".join(entrypoint)
        print(entrypoint)
        
        pasta_cache = f"{self.install_principal}/rclone/cache"
        os.makedirs(pasta_cache, exist_ok=True)
        os.chmod(pasta_cache, 0o777)
        
        run_args = [
            "--name", "rclone",
            "--restart=unless-stopped",
            "--memory=256m",
            "--cpus=1",
            "-e", "RCLONE_CONFIG=/config/rclone/rclone.conf",
            "-v", f"{conf_path}:/config/rclone",
            "-v", f"{base_mount}:/data:shared",
            "-v", f"{pasta_cache}:/root/.cache/rclone",
            "-v", "/etc/passwd:/etc/passwd:ro",
            "-v", "/etc/group:/etc/group:ro",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--device", "/dev/fuse",
            "--cap-add", "SYS_ADMIN",
            "--security-opt", "apparmor:unconfined",
            "-d",
            "--entrypoint", "sh",
            "rclone/rclone:latest",
            "-c", entrypoint
        ]
        
        self.executar_comandos_run_OrAnd_dockerfile( run_cmd=run_args )
        self.cria_rede_docker(associar_container_nome='rclone', numero_rede=1)

        print("\nInstalação do rclone concluída.")
    
    def instala_selenium_firefox(self):
        print("Iniciando instalação selenium_firefox:")
        # senha = input("Configure uma senha para acessar: ")
        container = f"""docker run -d \
                --name selenium-firefox \
                --restart=unless-stopped \
                -e SE_NODE_MAX_SESSIONS=2 \
                -e SE_NODE_SESSION_TIMEOUT=20 \
                -p 4444:4444 \
                -p 7900:7900 \
                --shm-size=2g \
                selenium/standalone-firefox:latest
                """
        comandos = [container]
        self.remove_container('selenium-firefox')
        resultados = self.executar_comandos(comandos,)
        print("Instalação do selenium_firefox concluída.")
        print("")
        print("Porta de acesso: 7900 - VNC")
        print("Porta de acesso: 4444 - Selenium")
        print("Aponte seus testes do WebDriver para http://servidor:4444")
        print("")

class Sistema(Docker, Executa_comandos):
    def __init__(self):
        Docker.__init__(self)
        Executa_comandos.__init__(self)
        
    def Reiniciar(self):
        comandos = [
            f"reboot"
        ]
        self.executar_comandos(comandos, comando_direto=True)
                
    def Desligar(self):
        comandos = [
            f"poweroff"
        ]
        self.executar_comandos(comandos, comando_direto=True)
    
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
        
    def instalar_interface_gnome(self,):
        escolha = input("Deseja uma instalação completa ou mais simples? (Digite '1' para completa ou '2' para simples): ").strip()
        self.atualizar_sistema_completa()
        if escolha == "1":
            self.executar_comandos([
                "sudo apt install ubuntu-gnome-desktop -y",
                "sudo apt install gnome-software -y",
                "reboot",
                ], comando_direto=True)
        elif escolha == "2":
            self.executar_comandos([
            "sudo apt install gnome-shell gdm3 gnome-session -y",
            "sudo systemctl enable gdm",
            "sudo systemctl start gdm",
            "reboot",
            ], comando_direto=True)
        else:
            print("Opção inválida. Nenhuma ação foi realizada.")
        
    def menu_swap(self,):
        menu = input('Digite: \n1 para ver a memoria \n2 para configurar \n')
        comandos = []
        if menu == '1':
            print("Verificando o arquivo de swap existente...")
            comandos += ["sudo swapon --show"]
            comandos += ["free -h"]
        elif menu == '2':
            novo_tamanho = input('Digite o novo tamanho em GB da swap (apenas numeros): ')
            print("Realizando configuração...")
            comandos += ["sudo swapoff /swap.img"]
            comandos += ["sudo rm /swap.img"]
            comandos += [f"sudo fallocate -l {novo_tamanho}G /swap.img"]
            comandos += [f"sudo chmod 600 /swap.img"]
            comandos += [f"sudo mkswap /swap.img"]
            comandos += [f"sudo swapon /swap.img"]
            print("Configuração realizada.")
        
        self.executar_comandos(comandos, comando_direto=True, exibir_executando=False)
        
        # Verificar se /swap.img já está no /etc/fstab
        try:
            with open('/etc/fstab', 'r') as f:
                fstab_lines = f.readlines()

            swap_fstab_line = '/swap.img none swap sw 0 0\n'

            if swap_fstab_line not in fstab_lines:
                with open('/etc/fstab', 'a') as f:
                    f.write(swap_fstab_line)
        except:
            print("Erro ao abrir o arquivo /etc/fstab. Verifique se você tem permissões adequadas.")
            
        try:
            # Definir o swappiness temporariamente
            value = '10'
            self.executar_comandos([f'sudo sysctl vm.swappiness={value}'], comando_direto=False, exibir_resultados=False)
            # subprocess.run(['sudo', 'sysctl', f'vm.swappiness={value}'], check=True)
            
            # Verificar se a configuração já existe em /etc/sysctl.conf
            with open('/etc/sysctl.conf', 'r') as f:
                lines = f.readlines()
            
            # Se a configuração já existe, atualizar o valor; caso contrário, adicionar a linha
            swappiness_line = f'vm.swappiness={value}\n'
            found = False
            
            for i, line in enumerate(lines):
                if line.startswith('vm.swappiness='):
                    lines[i] = swappiness_line
                    found = True
                    break
            
            if not found:
                lines.append(swappiness_line)
            
            # Escrever as alterações de volta ao arquivo
            with open('/etc/sysctl.conf', 'w') as f:
                f.writelines(lines)
            
            # Aplicar a configuração permanente
            self.executar_comandos([f'sudo sysctl -p'], comando_direto=False, exibir_resultados=False)
            # subprocess.run(['sudo', 'sysctl', '-p'], check=True)
            
            # print(f"vm.swappiness definido para {value} com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao definir vm.swappiness: {e}")
        except PermissionError:
            print("Erro: Permissão negada. Execute o script com permissões de superusuário (sudo).")
        
    def instalar_deb(self,):
        caminho = input('Insira o caminho absoluto do .deb para instalar: ')
        self.atualizar_sistema_completa()
        
        comandos = [
                f"sudo dpkg -i {caminho}",
                f"sudo apt-get install -f",
            ]
        self.executar_comandos(comandos, comando_direto=True)
        self.atualizar_sistema_completa()
        
    def instalar_interface_xfce(self,):
        """
        Instala ou reinstala a interface XFCE4 e a inicia.
        Permite que o usuário escolha reinstalar mesmo que já esteja instalada.
        """
        try:
            print("Verificando se o xfce4 já está instalado...")
            
            if self.verificar_instalacao('xfce4'):
                print("xfce4 já está instalado.")
                resposta = input("Deseja reinstalar o xfce4? (s/n): ").lower()
                
                if resposta == 's':
                    print("Reinstalando xfce4...")
                    self.atualizar_sistema_completa()
                    comandos = [
                        "sudo apt remove --purge xfce4* -y",
                        "sudo apt autoremove -y",
                        "sudo apt install -y xfce4 xfce4-goodies lightdm dbus-x11 xinit",
                        "sudo dpkg-reconfigure lightdm",
                        "sudo systemctl enable lightdm --now",
                        "rm -f ~/.Xauthority ~/.cache/sessions/*",
                        "reboot",
                    ]
                    self.executar_comandos(comandos, comando_direto=True)
                    print("xfce4 reinstalado com sucesso.")
                else:
                    # Apenas inicia o xfce4
                    print("Iniciando xfce4...")
                    self.executar_comandos(["startxfce4 "], comando_direto=True)
            else:
                print("xfce4 não encontrado. Instalando xfce4...")
                self.atualizar_sistema_completa()
                comandos = [
                    # "sudo apt install xfce4 -y",
                    "sudo apt install xfce4 xfce4-goodies lightdm dbus-x11 xinit",
                    "sudo dpkg-reconfigure lightdm",
                    "sudo systemctl enable lightdm --now",
                    "rm -f ~/.Xauthority ~/.cache/sessions/*",
                    "reboot",
                ]
                self.executar_comandos(comandos, comando_direto=True)
                print("xfce4 instalado com sucesso.")
                
                # Iniciar o xfce4 após a instalação
                print("Iniciando xfce4...")
                self.executar_comandos(["startxfce4 "], comando_direto=True)
            
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
        self.executar_comandos(comandos, comando_direto=True)
    
    def gerenciar_fstab(self, ponto_montagem, acao='adicionar', dispositivo=None):
        try:
            # Lê o conteúdo atual do /etc/fstab
            with open("/etc/fstab", "r") as fstab:
                linhas = fstab.readlines()
            
            # Identifica a linha correspondente ao ponto de montagem
            linha_existente = None

            for linha in linhas:
                if ponto_montagem in linha and 'ext4' in linha:
                    linha_existente = linha
                    break

            if acao == 'adicionar':
                if not dispositivo:
                    print("Erro: Para adicionar, você deve fornecer o dispositivo.")
                    return

                if linha_existente:
                    print(f"O ponto de montagem {ponto_montagem} já está presente no /etc/fstab.")
                    return
                
                # Adiciona a nova linha ao /etc/fstab
                linha_fstab = f"{dispositivo} {ponto_montagem} ext4 defaults 0 0\n"
                with open("/etc/fstab", "a") as fstab:
                    fstab.write(linha_fstab)
                print(f"Partição {dispositivo} adicionada ao /etc/fstab para montagem automática em {ponto_montagem}.")

            elif acao == 'desmontar':
                if linha_existente:
                    # Comenta a linha existente
                    novas_linhas = []
                    for x in linhas:
                        if ponto_montagem in x and 'ext4' in x:
                            novas_linhas.append(f"#{x}")
                        else:
                            novas_linhas.append(x)

                    with open("/etc/fstab", "w") as fstab:
                        fstab.writelines(novas_linhas)
                    print(f"Ponto de montagem {ponto_montagem} comentado no /etc/fstab para evitar montagem automática.")
                else:
                    print(f"O ponto de montagem {ponto_montagem} não está presente no /etc/fstab.")

        except PermissionError:
            print("Erro: Permissões insuficientes para modificar /etc/fstab. Execute o script com sudo.")
        except Exception as e:
            print(f"Erro: {e}")
    
    def listar_particoes(self,):
        print("Listando discos disponiveis:")
        comandos = [
            "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E 'disk|part|lvm|raid'",
        ]
        resultado = self.executar_comandos(comandos)
        
    def listar_particoes_detalhadas(self,):
        print("Listando discos disponiveis:")
        comandos = [
            "sudo parted -l",
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
        dns = input("Digite os endereços de DNS separados por vírgula (ex: 8.8.8.8, 8.8.4.4): ")
        dns_list = [dns.strip() for dns in dns.split(",")]

        # Nome do arquivo de configuração do Netplan
        config_file = "/etc/netplan/00-installer-config.yaml"
        if not os.path.exists(config_file):
            config_file = "/etc/netplan/50-cloud-init.yaml"
            with open("/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg", "w") as file:
                file.write("network: {config: disabled}")

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
        
    def formata_cria_particao(self,):
        self.listar_particoes()
        # Solicita o nome do disco ao usuário
        print("O disco sera formatado e montado.")
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
            self.gerenciar_fstab(dispositivo=f"/dev/{disco}1", ponto_montagem=ponto_montagem)
        
    def verificar_boot_mode(self):
        """Verifica se o sistema está usando BIOS (Legacy) ou UEFI"""
        if os.path.exists("/sys/firmware/efi"):
            return "UEFI"
        return "BIOS"
    
    def estado_raid(self, tempo_real=True):
        """Exibe o estado atual do RAID e suas configurações."""
        print('Exibindo o estado atual do RAID:')
        if tempo_real:
            comandos = [
                "watch cat /proc/mdstat"
            ]
        else:
            comandos = [
                "cat /proc/mdstat"
            ]
        resultado = self.executar_comandos(comandos, comando_direto=True)
    
    def formatar_criar_particao_raid(self):
        """Formata um disco e adiciona ao RAID"""
        self.listar_particoes()
        
        # exibir o stado da raid atual
        self.estado_raid(tempo_real=False)

        # Solicita o nome do disco ao usuário
        print("Inicializando a formatação e adição de disco ao RAID...")
        print("\n⚠️ O disco será formatado e adicionado ao RAID!")
        disco_input = input("Digite o nome do disco (ex: sdb): ").strip()
        disco = disco_input if disco_input.startswith("/dev/") else f"/dev/{disco_input}"
        raid_device_input = input("Digite o nome do dispositivo RAID (ex: md0): ").strip()
        raid_device = raid_device_input if raid_device_input.startswith("/dev/") else f"/dev/{raid_device_input}"
        
        # Detecta se o sistema está rodando em UEFI ou BIOS
        boot_mode = self.verificar_boot_mode()
        print(f"\n🖥️ Sistema detectado como: {boot_mode}")

        # Verifica se o disco existe
        if not os.path.exists(disco):
            print(f"❌ ERRO: O disco {disco} não foi encontrado!")
            return

        # Confirmação antes de formatar
        confirm = input(f"⚠️ Tem certeza que deseja apagar TODAS as partições de {disco}? (sim/não): ").strip().lower()
        if confirm != "sim":
            print("❌ Operação cancelada!")
            return

        print(f"\n💾 Atualiza a tabela de partições {disco}...")
        
        # Comandos para limpeza do disco
        comandos_lipeza = [
            f"sudo umount {disco}*", # Desmonta qualquer partição ativa
            f"sudo mdadm --stop /dev/md127",  # Para o RAID
            f"sudo mdadm --zero-superblock {disco}",  # Remove metadados de RAID
            f"sudo wipefs -a {disco}",  # Apaga assinaturas de arquivos e RAID
            f"sudo partprobe {disco}", # Atualiza a tabela de partições no kernel
            f"sudo partx -u {disco}", # Atualiza a tabela de partições no kernel
            f"sudo udevadm settle", # Forçar atualização
            # f"sudo mdadm --stop /dev/md127",  # Para o RAID
        ]
        # Reppete os comandos para ter certeza que tudo foi limpo
        self.executar_comandos(comandos_lipeza, intervalo=5, ignorar_erros=True)
        self.executar_comandos(comandos_lipeza, intervalo=5, ignorar_erros=True)
        
        # Atualizar a tabela de partições
        comandos = [
            f"sudo parted -s {disco} mklabel gpt",  # Define GPT como esquema de partições
            f"sudo partprobe {disco}",  # Atualiza a tabela de partições no kernel
            f"sudo udevadm settle",  # Forçar atualização
        ]
        self.executar_comandos(comandos, intervalo=1)

        comandos = []
        # Configuração para BIOS (Legacy)
        if boot_mode == "BIOS":
            print("\n📝 Criando partições para BIOS (Legacy)")
            comandos += [
                f"sudo parted -s {disco} mkpart bios_grub 1MiB 2MiB",   # Partição necessária para GRUB (Legacy)
                f"sudo parted -s {disco} set 1 bios_grub on",           # Define a partição 1 como bios_grub
                f"sudo parted -s {disco} mkpart primary 2MiB 100%",     # Partição para RAID
                f"sudo parted -s {disco} set 2 raid on",                # Define a partição 2 como RAID
            ]

        # Configuração para UEFI
        elif boot_mode == "UEFI":
            print("\n📝 Criando partições para UEFI")
            comandos += [
                f"sudo parted -s {disco} mkpart ESP fat32 1MiB 512MiB",  # Partição EFI
                f"sudo parted -s {disco} set 1 boot on",                 # Define a partição EFI como bootável
                f"sudo parted -s {disco} mkpart primary 512MiB 100%",    # Partição para RAID
                f"sudo parted -s {disco} set 2 raid on",                 # Define a partição 2 como RAID
            ]
        self.executar_comandos(comandos, intervalo=1)

        # para o RAID
        # self.executar_comandos([f"sudo mdadm --stop /dev/md127"], intervalo=5, ignorar_erros=True)

        # Formatar e adicionar ao RAID
        print(f"\n🔗 Adicionando {disco}2 ao RAID {raid_device}...")
        comandos = [
            f"sudo mdadm --add {raid_device} {disco}2"
        ]
        self.executar_comandos(comandos, intervalo=5)

        # Instalar o GRUB no novo disco
        print(f"\n⚙️ Instalando o GRUB em {disco}...")
        if boot_mode == "BIOS":
            comandos = [
                f"sudo grub-install --target=i386-pc --recheck {disco}",
                "sudo update-grub"  # Atualizar a configuração do GRUB
            ]
        elif boot_mode == "UEFI":
            comandos = [
                f"sudo grub-install --target=x86_64-efi --efi-directory=/boot/efi --recheck {disco}",
                "sudo update-grub"  # Atualizar a configuração do GRUB
            ]
        self.executar_comandos(comandos)

        # Monitorar a sincronização do RAID
        self.estado_raid(tempo_real=True)

    def gerenciar_raid(self):
        """
        Automatiza a expansão ou redução do RAID com base na escolha do usuário via input.
        """
        
        print("\n📌 Controle de tamanho do RAID.")
        
        # 🔹 Exibir informações iniciais
        self.listar_particoes()  # Lista partições antes de iniciar
        self.estado_raid(tempo_real=False)  # Exibe estado atual do RAID

        # 🔹 Passo 1: Solicitar os parâmetros do usuário
        raid_device = "/dev/" + input("\nDigite o dispositivo RAID (ex: md0): ").strip()
        particao = input("Digite o número da partição a ser ajustada (ex: 2): ").strip()
        particao_completa = f"{raid_device}p{particao}"

        print("\n🔹 Escolha uma opção:")
        print("[1] Aumentar o tamanho do RAID")
        print("[2] Diminuir o tamanho do RAID")
        escolha = input("\nDigite 1 para aumentar ou 2 para diminuir: ").strip()

        if escolha == "1":
            acao = "aumentar"
            print("\n📌 Você deseja definir um novo tamanho ou usar o máximo disponível?")
            print("[1] Definir um tamanho específico")
            print("[2] Usar o tamanho máximo disponível (padrão)")
            escolha_tamanho = input("\nDigite 1 para definir um tamanho ou 2 para usar o máximo: ").strip()

            if escolha_tamanho == "1":
                try:
                    novo_tamanho = int(input("\nDigite o novo tamanho desejado (em GB): ").strip())
                    novo_tamanho = f"{novo_tamanho}G"
                except ValueError:
                    print("❌ ERRO: O tamanho deve ser um número inteiro.")
                    return
            else:
                novo_tamanho = "max"

        elif escolha == "2":
            acao = "diminuir"
            try:
                novo_tamanho = int(input("\nDigite o novo tamanho desejado (em GB): ").strip())
                novo_tamanho = f"{novo_tamanho}G"
            except ValueError:
                print("❌ ERRO: O tamanho deve ser um número inteiro.")
                return
        else:
            print("❌ Opção inválida.")
            return

        # 🔍 Passo 2: Verificar o tamanho atual do RAID
        print("\n🔍 Obtendo o tamanho atual do RAID...")
        resultado_tamanho = self.executar_comandos([f"sudo mdadm --detail {raid_device}"])
        resultado_tamanho_str = "".join(resultado_tamanho.get(f"sudo mdadm --detail {raid_device}", []))

        # Extração segura do tamanho atual do RAID
        match = re.search(r"Array Size\s*:\s*(\d+)", resultado_tamanho_str)
        tamanho_atual = int(match.group(1)) // (1024 ** 2) if match else None

        if not tamanho_atual:
            print("❌ ERRO: Não foi possível determinar o tamanho atual do RAID.")
            return

        print(f"📌 Tamanho atual do RAID: {tamanho_atual} GB")

        # 🔍 Verificar se o novo tamanho é válido
        if acao == "aumentar" and novo_tamanho != "max":
            if int(novo_tamanho.replace("G", "")) <= tamanho_atual:
                print(f"❌ ERRO: O novo tamanho ({novo_tamanho}) deve ser maior que o tamanho atual ({tamanho_atual} GB).")
                return

        if acao == "diminuir":
            if int(novo_tamanho.replace("G", "")) >= tamanho_atual:
                print(f"❌ ERRO: O novo tamanho ({novo_tamanho}) deve ser **menor** que o tamanho atual ({tamanho_atual} GB).")
                return

        # 🔍 Passo 3: Expandir a partição
        print("\n📌 Expandindo a partição GPT...")
        self.executar_comandos([f"sudo parted --script {raid_device} print fix"], comando_direto=True)
        self.executar_comandos([f"sudo parted --script {raid_device} resizepart {particao} {'100%' if novo_tamanho == 'max' else novo_tamanho}"], comando_direto=True)
        
        # 🔍 Passo 4: Expandir o sistema de arquivos
        print("\n🔍 Verificando o sistema de arquivos...")
        resultado = self.executar_comandos([f"sudo blkid {particao_completa}"])
        resultado_str = "".join(resultado.get(f"sudo blkid {particao_completa}", []))
        tipo_fs = re.search(r'TYPE="(\w+)"', resultado_str)
        tipo_fs = tipo_fs.group(1) if tipo_fs else None

        if not tipo_fs:
            print(f"❌ ERRO: Não foi possível determinar o tipo de sistema de arquivos. Saída:\n{resultado_str}")
            return

        print(f"\n📌 Sistema de arquivos detectado: {tipo_fs}")

        if tipo_fs == "ext4":
            fs_comando = f"sudo resize2fs {particao_completa}"
        elif tipo_fs == "xfs":
            fs_comando = f"sudo xfs_growfs /"
        else:
            print(f"❌ Sistema de arquivos desconhecido: {tipo_fs}. Operação cancelada.")
            return

        print("\n📌 Expandindo o sistema de arquivos...")
        if not self.executar_comandos([fs_comando]):
            print("❌ Falha ao expandir o sistema de arquivos. Abortando!")
            return

        print(f"\n✅ Operação de {'expansão' if acao == 'aumentar' else 'redução'} do RAID concluída com sucesso!")

    def menu_raid(self):
        print("\nMenu de raids.\n")
        """Menu de opções"""
        opcoes_menu = [
            ("Exibe o estado atual da raid", self.estado_raid),
            ("Formata o disco para usar em raid existente", self.formatar_criar_particao_raid),
            ("Controle de tamanho do raid", self.gerenciar_raid),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def monta_particao(self,):
        self.listar_particoes()
        particao = input('\nDigite a partição que deseja monta (sda1): ')
        print('\nO ponto de montagem sera criado com 777 caso não exista!')
        ponto_montagem = input('Digite o ponto de montagem (/mnt/dados): ')
        self.gerenciar_permissoes_pasta(ponto_montagem, '777')
        comandos = [
            f"sudo mount /dev/{particao} {ponto_montagem}",
        ]
        resultado = self.executar_comandos(comandos)
        self.listar_particoes()
        adicionar_fstab = input("\nDeseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.gerenciar_fstab(dispositivo=f"/dev/{particao}", ponto_montagem=ponto_montagem)
    
    def desmontar_particao(self,):
        self.listar_particoes()
        ponto_montagem = input('Digite o ponto de montagem para desmontar (/mnt/dados): ')
        comandos = [
            f"sudo umount /mnt/sdc1",
        ]
        resultado = self.executar_comandos(comandos)
        self.listar_particoes()
        
        self.gerenciar_fstab(ponto_montagem=ponto_montagem, acao='desmontar')
    
    def menu_particoes(self):
        print("\nMenu de partições.\n")
        """Menu de opções"""
        opcoes_menu = [
            ("Menu RAID", self.menu_raid),
            ("Listar particoes", self.listar_particoes),
            ("Listar particoes detalhadas", self.listar_particoes_detalhadas),
            ("Monta particao", self.monta_particao),
            ("Desmontar particao", self.desmontar_particao),
            ("Formata o disco e cria partição e monta", self.formata_cria_particao),
        ]
        self.mostrar_menu(opcoes_menu)
    
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
        """
        Verifica se um pacote está instalado no sistema.
        Exemplo:
        if not self.verificar_instalacao("nome_pacote"):
            pass
            #instale o pacote
        
        """
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
        
    def verifica_velocidade(self):
        if not self.verificar_instalacao("speedtest-cli"):
            comandos = [
                "sudo apt update",
                "sudo apt-get install -y speedtest-cli",
            ]
            self.executar_comandos(comandos)
        # Executar o comando sensors
        self.executar_comandos(["speedtest "], comando_direto=True)

    def rsync_sync(
        self,
        origem: str | None = None,
        destino: str | None = None,
        delete: bool = True,
        verbose: bool = True,
        extra_opts: Union[List[str], None] = None,
        max_retries: int = 100,
    ) -> None:
        """
        Sincroniza o conteúdo de 'origem' para 'destino' usando rsync.

        Se algum arquivo falhar, rsync continua com o restante; o laço repete
        até não restarem pendências (exit-code 0) ou estourar `max_retries`.

        Lança
        -----
        subprocess.CalledProcessError – se rsync retornar erro “fatal”.
        """
        # 1) garante que rsync existe
        if not shutil.which("rsync"):
            print("rsync não encontrado. Instalando…")
            self.executar_comandos(
                ["sudo apt update", "sudo apt install -y rsync"], comando_direto=True
            )
            if not shutil.which("rsync"):
                raise RuntimeError("Falha ao instalar rsync.")

        # 2) obtém caminhos caso não passem via parâmetro
        origem = origem or input("Digite o caminho da pasta de origem: ").strip()
        destino = destino or input("Digite o caminho da pasta de destino: ").strip()

        if not os.path.exists(origem):
            raise FileNotFoundError(f"Caminho de origem não existe: {origem}")

        os.makedirs(destino, exist_ok=True)

        # 3) monta comando base
        cmd = [
            "rsync",
            "-rltD",             # recursivo, preserva links, tempos, devices (mas não perms)
            "--no-owner",        # não mantém owner
            "--no-group",        # não mantém grupo
            "--partial",         # mantém partes de arquivos grandes
            "--inplace",         # continua baixando no mesmo arquivo
            "--progress",
            "--info=progress2",
            "-h",
        ]
        if verbose:
            cmd.append("-v")
        if delete:
            cmd.append("--delete")
        if extra_opts:
            cmd.extend(extra_opts)

        origem_path = origem.rstrip("/") + "/"
        destino_path = destino.rstrip("/") + "/"
        cmd.extend([origem_path, destino_path])

        print(f"\n🔄  Sincronizando: {origem_path} ➡️  {destino_path}\n")

        # 4) executa até concluir ou exceder tentativas
        for tentativa in range(1, max_retries + 1):
            self.gerenciar_permissoes_pasta(destino, "777")
            result = subprocess.run(cmd)
            rc = result.returncode

            if rc == 0:
                print("✅  Sincronização concluída sem pendências.")
                return

            # 23/24: arquivos faltando ou removidos ─ tentar de novo
            if rc in (23, 24):
                print(f"[{tentativa}/{max_retries}] Ainda há arquivos pendentes "
                    f"(exit-code {rc}). Nova tentativa em 5 s…")
                time.sleep(5)
                continue

            # 11: erro de I/O – tenta ajustar permissões e repetir
            if rc == 11 and tentativa < max_retries:
                print(f"[{tentativa}/{max_retries}] Erro de I/O.")
                time.sleep(5)
                continue

            # demais códigos ou fim das tentativas → aborta
            raise subprocess.CalledProcessError(rc, cmd)

        raise RuntimeError(f"Falhou após {max_retries} tentativas.")

    def vnstat(self):
        """
        Instala e configura o vnstat, caso ainda não esteja instalado.
        Em seguida, exibe as estatísticas mensais de uso de rede.
        """
        if not self.verificar_instalacao("vnstat"):
            print("Instalando o vnstat...")
            comandos = [
                "sudo apt update",
                "sudo apt install -y vnstat",
                "sudo systemctl enable vnstat",
                "sudo systemctl start vnstat",
            ]
            self.executar_comandos(comandos, comando_direto=True)
            print("vnstat instalado e iniciado com sucesso.")
            print("Aguarde alguns minutos para que o vnstat colete dados de uso de rede.")
        else:
            print("\nExibindo estatísticas mensais de uso de rede:")
            self.executar_comandos(["vnstat -m"], comando_direto=True)
        
    def setup_inicializar_service(self):
        """
        1. Cria /install_principal/inicializar.py (com log simples) se não existir.
        2. Cria /etc/systemd/system/inicializar.service apontando para ele se não existir.
        3. Recarrega o systemd e habilita o serviço.

        → Execute como root ou via sudo.
        """
        script_path = Path("/install_principal/inicializar.py")
        service_path = Path("/etc/systemd/system/inicializar.service")

        # 1) script de exemplo (somente se não existir)
        if not script_path.exists():
            script_code = textwrap.dedent("""\
            #!/usr/bin/env python3

            ## Para iniciar o serviço
            # sudo systemctl start inicializar.service
            ## Para parar o serviço
            # sudo systemctl status inicializar.service
            ## reiniciar o serviço
            # sudo systemctl restart inicializar.service

            import os
            from datetime import datetime
            import subprocess
            import time

            time.sleep(30)

            class inicializar:
                def __init__(self):
                    self.escrever_log("Script inicializar.py executado.")
                    self.start()
                    
                def start(self,):
                    while True:
                        print("Executando o script inicializar.py...")
                        
                        # Espera 1 hora
                        time.sleep(60*60*1)

                def escrever_log(self, mensagem):
                    # Escreve uma mensagem no arquivo de log.
                    with open(self.log_path, "a") as f:
                        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S} – {mensagem}')
            
            if __name__ == "__main__":
                inicializar()
            """)
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(script_code)
            script_path.chmod(0o755)         # torna executável
            print(f"✔ Script criado em {script_path}")
        else:
            print(f"✓ Script {script_path} já existe, mantendo o arquivo existente")

        # 2) unidade systemd (somente se não existir)
        if not service_path.exists():
            unit = textwrap.dedent(f"""\
                [Unit]
                Description=Inicializar.py automático
                After=network.target

                [Service]
                Type=simple
                ExecStart=/usr/bin/python3 {script_path}
                Restart=on-failure

                [Install]
                WantedBy=multi-user.target
            """)
            service_path.write_text(unit)
            print(f"✔ Serviço criado em {service_path}")
        else:
            print(f"✓ Serviço {service_path} já existe, mantendo o arquivo existente")

        # 3) recarrega e ativa
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "--now", service_path.name], check=True)

        print("✔ Serviço ativado e em execução – verifique com:")
        print(f"   sudo systemctl status inicializar.service")
        print("✔ Para desativar, use:")
        print(f"   sudo systemctl disable --now inicializar.service")
        print("✔ Para iniciar, use:")
        print(f"   sudo systemctl start inicializar.service")
        print("✔ Para parar, use:")
        print(f"   sudo systemctl stop inicializar.service")
        
    def configura_ssh(self):
        try:
            # Solicitar nova porta e senha
            new_port = int(input("Digite a nova porta para o SSH: "))
            new_password = input("Digite a nova senha para o usuário: ")
            
            # Alterar a porta no arquivo de configuração SSH
            print("Alterando a porta do SSH...")
            subprocess.run(
                ["sudo", "sed", "-i", f"s/^#\\?Port .*/Port {new_port}/", "/etc/ssh/sshd_config"],
                check=True
            )
            # Reiniciar o serviço SSH
            subprocess.run(["sudo", "systemctl", "restart", "ssh"], check=True)
            print(f"Porta SSH alterada para {new_port}.")
            
            # Listar usuários com acesso ao shell
            try:
                result = subprocess.check_output(
                    "awk -F: '($7 ~ /(\\/bin\\/bash|\\/bin\\/sh|\\/bin\\/dash)$/) {print $1}' /etc/passwd", 
                    shell=True, 
                    text=True
                )
                ssh_users = result.strip().split("\n")
            except subprocess.CalledProcessError:
                ssh_users = []
            
            # Alterar senha para cada usuário encontrado
            for username in ssh_users:
                try:
                    print(f"Alterando a senha do usuário: {username}...")
                    subprocess.run(
                        ["sudo", "passwd", username],
                        input=f"{new_password}\n{new_password}",
                        text=True,
                        check=True
                    )
                    print(f"Senha alterada com sucesso para o usuário: {username}.")
                except subprocess.CalledProcessError as e:
                    print(f"Erro ao alterar a senha do usuário {username}: {e}")
            
            # Mensagem de conclusão
            print(f"Configuração concluída: SSH na porta {new_port} e senhas atualizadas.")
        
        except ValueError:
            print("Erro: Porta deve ser um número.")
        except Exception as e:
            print(f"Erro inesperado: {e}")
        
    def opcoes_sistema(self):
        print("\nMenu de sistema.\n")
        """Menu de opções"""
        opcoes_menu = [
            ("Menu partições", self.menu_particoes),
            ("Menu swap", self.menu_swap),
            ("Cria o .py para inicializar", self.setup_inicializar_service),
            ("instalar deb", self.instalar_deb),
            ("fecha_tela_noot", self.fecha_tela_noot),
            ("Instala/Inicia interface xfce", self.instalar_interface_xfce),
            ("Instala interface gnome", self.instalar_interface_gnome),
            ("Ecaminhamentos portas tuneis", self.ecaminhamentos_portas_tuneis),
            ("Instala gerenciador de WIFI nmtui", self.setup_wifi),
            ("Configura ip fixo", self.configura_ip_fixo),
            ("Ver uso do espaço em pasta", self.ver_uso_espaco_pasta),
            ("Gerenciar permissoes de pasta", self.gerenciar_permissoes_pasta),
            ("Verificar temperatura", self.verifica_temperatura),
            ("Verificar velocidade da internet", self.verifica_velocidade),
            ("configura ssh", self.configura_ssh),
            ("Faz copia inteligente com rsync", self.rsync_sync),
            ("Inatala/Executa monitor de rede vnstat", self.vnstat),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def menu_docker(self):
        print("\nBem-vindo ao Gerenciador Docker\n")
        self.instala_docker()
        if not os.path.exists(self.install_principal):
            os.makedirs(self.install_principal, exist_ok=True)
            os.chmod(self.install_principal, 0o777)
        """Menu de opções"""
        opcoes_menu = [
            ("Força instalação docker", self.instala_docker_force),
            ("Instala portainer", self.instala_portainer),
            ("Instala filebrowser", self.instala_filebrowser),
            ("Instala traefik", self.instala_traefik),
            ("||| Conf ||| Adiciona roteamento e serviço ao traefik", self.adiciona_roteador_servico_traefik),
            ("||| Conf ||| Configura rede do container", self.configura_rede),
            ("Instala SFTP sftpgo", self.instala_ftp_sftpgo),
            ("||| Conf ||| Gerenciador SFTP sftpgo", self.gerenciar_usuarios_sftp),
            ("Instala openlitespeed", self.instala_openlitespeed),
            ("||| Conf ||| Controle de sites openlitespeed", self.controle_sites_openlitespeed),
            ("Instala webserver guacamole", self.instala_webserver_guacamole),
            ("** BD ** Instala mysql", self.instala_mysql),
            ("** BD ** Instala postgres", self.instala_postgres),
            ("Instala wordpress", self.instala_wordpress),
            ("Instala wordpress puro", self.instala_wordpress_puro),
            ("Instala app nodejs", self.instala_app_nodejs),
            ("Instala grafana, prometheus, node-exporter", self.iniciar_monitoramento),
            ("Start sync pastas com RSYNC", self.start_sync_pastas),
            ("Instala windows KVM docker", self.instala_windows_KVM_docker),
            ("Instala Sistema CISO docker", self.instala_sistema_CISO_docker),
            ("Instala deskto ubuntu webtop", self.desktop_ubuntu_webtop),
            ("Instala Ubuntu", self.ubuntu),
            ("Instala rustdesk", self.instala_rustdesk),
            ("Instala pritunel", self.instala_pritunel),
            ("Instala nextcloud", self.instala_nextcloud),
            ("Instala code-server", self.instala_code_server),
            ("Instala Open WebUI", self.instala_open_webui),
            ("Instala Redis Docker", self.instala_redis_docker),
            ("Instala selenium-firefox", self.instala_selenium_firefox),
            ("Instala rclone", self.rclone),
        ]
        self.mostrar_menu(opcoes_menu)
    
    def exibe_ip(self,):
        comandos = [
            "ip addr show | grep -vE '(docker|br-)' | grep 'inet ' | awk '{split($2, a, \"/\"); print a[1], $NF}'",
        ]
        resultados = self.executar_comandos(comandos, exibir_executando=False, exibir_resultados=False)
        ip_result = "\n".join(line.strip() for line in resultados[comandos[0]] if "127.0.0.1" not in line)
        # print(ip_result)
        return ip_result
    
    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        print('\n')
        
        if not self.verificar_instalacao("glances"):
            comandos = [
                "sudo apt update",
                "sudo apt install glances -y",
            ]
            self.executar_comandos(comandos, comando_direto=True)

        print('Pressione H para ver as opções de ajuda')
        print('Pressione Q para sair')
        
        resposta = input("Para ver o modo web digite 'w' ou 'Outra tecla' para o modo normal. (w / Outra tecla): ")
        if resposta.lower() == "w":
            print("Iniciando o modo web do glances...")
            comandos = [
                "/usr/local/bin/glances -w",
            ]
        else:
            print("Iniciando o modo terminal do glances...")
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
        self.executar_comandos(['sudo apt-get update'], comando_direto=True)
        
    def atualizar_sistema_completa(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema com upgrade...")
        self.atualizar_sistema_simples()
        self.executar_comandos(["sudo apt-get upgrade -y"], comando_direto=True)
        
    def atualizar_sistema_completa_reiniciar(self,):
        """Executa o comando para atualizar o sistema."""
        print("Reiniciando o sistema...")
        self.atualizar_sistema_simples()
        self.atualizar_sistema_completa()
        self.executar_comandos(['reboot '], comando_direto=True)

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()

def main():
    servicos = Sistema()
    print(f"""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.222
===========================================================================
===========================================================================
ip server:
{servicos.exibe_ip()}
===========================================================================
===========================================================================
""")
    """Função principal que controla o menu."""
    opcoes_menu = [
        ("Reiniciar", servicos.Reiniciar),
        ("Desligar", servicos.Desligar),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("verificando status do sistema", servicos.verificando_status_sistema),
        ("Menu de outras opções", servicos.opcoes_sistema),
        ("Menu Docker", servicos.menu_docker),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()
