#!/bin/bash

# Execute com:
# wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py
# rm -rf /tmp/Scripts_linux && git clone --depth=1 https://github.com/mauriciowebme/Scripts_linux.git /tmp/Scripts_linux && python3 /tmp/Scripts_linux/install_master.py

# Ou crie um arquivo de texto com o nome install_master.txt na raiz do pendrive USB e execute:
# lsblk
# sudo mkdir -p /mnt/usb
# sudo mount /dev/sdb1 /mnt/usb
# bash /mnt/usb/install_master.txt
# depois da primeira execução, o arquivo pode ser executado com:
# bash /install_principal/install_master.txt

import configparser
from urllib.parse import quote_plus
import shlex
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
import secrets
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
    execute_file = Path("/install_principal/install_master.txt")
    execute_file.parent.mkdir(parents=True, exist_ok=True)

    # if not execute_file.exists():
    execute_file.write_text("rm -rf /tmp/Scripts_linux && git clone --depth=1 https://github.com/mauriciowebme/Scripts_linux.git /tmp/Scripts_linux && python3 /tmp/Scripts_linux/install_master.py")
    
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
                subprocess.run(["docker", "build", "--no-cache", "-t", tag, "."], cwd=ctx, check=True)
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
    
    def aplicar_compose(self, compose_yml: str, compose_filename: str = "docker-compose.yml"):
        tmp_dir = Path(".tmp/compose-run").resolve()
        tmp_dir.mkdir(parents=True, exist_ok=True)
        compose_path = tmp_dir / compose_filename
        compose_path.write_text(compose_yml, encoding="utf-8")
        print(f"docker-compose.yml salvo em: {compose_path}")

        comandos = [
            ["docker", "compose", "-f", str(compose_path), "pull"],
            ["docker", "compose", "-f", str(compose_path), "up", "-d"],
        ]

        for cmd in comandos:
            print("\n" + "*" * 40)
            print(" " * 5 + "---> Executando comando: <---")
            print(" " * 5 + " ".join(cmd))
            print("*" * 40 + "\n")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao executar {' '.join(cmd)}: {e}")
                raise

        try:
            compose_path.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass

        return str(compose_path)
    
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
        Altera as permissões de um arquivo ou pasta.
        Se for pasta, altera recursivamente.
        """
        # Solicitar o caminho
        if pasta == None:
            pasta = input("Digite o caminho (arquivo ou pasta): ").strip()
        else:
            if not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)
        
        if not os.path.exists(pasta):
            print(f"Erro: '{pasta}' não existe.")
            return
        
        # Solicitar permissões
        if permissao == None:
            permissao = input("Digite as permissões (ex: 777, 755, 644): ").strip()
        
        try:
            permissao_octal = int(permissao, 8)
            
            # Verifica se é arquivo ou pasta
            if os.path.isfile(pasta):
                # É arquivo
                os.chmod(pasta, permissao_octal)
                print(f"Permissões do arquivo alteradas para: {oct(permissao_octal)}")
            
            elif os.path.isdir(pasta):
                # É pasta - aplica recursivamente
                os.chmod(pasta, permissao_octal)
                
                for root, dirs, files in os.walk(pasta):
                    for nome in dirs:
                        try:
                            os.chmod(os.path.join(root, nome), permissao_octal)
                        except:
                            print(f"Erro ao alterar: {os.path.join(root, nome)}")
                    
                    for nome in files:
                        try:
                            os.chmod(os.path.join(root, nome), permissao_octal)
                        except:
                            print(f"Erro ao alterar: {os.path.join(root, nome)}")
                
                print(f"Permissões da pasta e itens alteradas para: {oct(permissao_octal)}")
            
        except ValueError:
            print("Erro: Permissões inválidas. Use formato octal (ex: 777, 755, 644).")
        except PermissionError:
            print("Erro: Permissão negada. Execute como root.")
        except Exception as e:
            print(f"Erro: {e}")
        
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
    
    def instalar_n8n(self):
        print("Iniciando instalação do n8n (workflow automation).")
        print("\n" + "="*60)
        
        # PASSO 1: Pergunta tipo de instalação
        print("Tipo de instalação:")
        print("1 - Simples (SQLite local, sem banco externo)")
        print("2 - Main (servidor principal com PostgreSQL e Redis)")
        print("3 - Worker (processador de tarefas)")
        tentativas = 0
        is_simples = False
        is_main = False
        is_worker = False
        while tentativas < 3:
            tipo_instalacao = input("Digite sua escolha (1, 2 ou 3): ").strip()
            is_simples = tipo_instalacao == "1"
            is_main = tipo_instalacao == "2"
            is_worker = tipo_instalacao == "3"
            if is_simples or is_main or is_worker:
                break
            tentativas += 1
            print(f"❌ Opção inválida! ({tentativas}/3 tentativas)")
        if not (is_simples or is_main or is_worker):
            print("❌ Nenhuma opção válida após 3 tentativas. Retornando ao menu principal...")
            return
        
        # Define o sufixo e caminhos baseado no tipo escolhido
        if is_simples:
            tipo_suffix = "simples"
        elif is_main:
            tipo_suffix = "main"
        else:
            tipo_suffix = "worker"
            
        caminho_n8n = f'{self.install_principal}/n8n_{tipo_suffix}'
        env_file_path = os.path.join(caminho_n8n, 'n8n.env')
        container_name = f"n8n_{tipo_suffix}"

        # PASSO 2: Verificação de instalação anterior e decisão manter/limpar
        try:
            dados_existentes = os.path.isdir(caminho_n8n) and any(os.scandir(caminho_n8n))
        except Exception:
            dados_existentes = os.path.isdir(caminho_n8n)
        
        clean_install = False
        pending_delete_dir = None
        if dados_existentes:
            print("\n=== Instalação existente detectada (arquivos) ===")
            try:
                qtd = len(list(os.scandir(caminho_n8n)))
            except Exception:
                qtd = -1
            print(f" - Pasta de dados: {caminho_n8n} (itens: {qtd if qtd>=0 else 'desconhecido'})")
            print("\nO que deseja fazer?")
            if is_main:
                print("Nota: Ao escolher nova instalação, o banco PostgreSQL também será limpo.")
            elif is_worker:
                print("Nota: A nova instalação do worker não alterará o banco PostgreSQL compartilhado.")
            print("1) Manter dados (recomendado)")
            print("2) Nova instalação limpa (apagar pasta de dados)")
            print("3) Cancelar")
            escolha = input("Escolha [1/2/3] (padrão: 1): ").strip() or "1"
            if escolha == "3":
                print("Operação cancelada pelo usuário.")
                return
            if escolha == "2":
                # Remoção da pasta será feita após as ações adicionais abaixo
                pending_delete_dir = caminho_n8n
                if is_main:
                    print(f"Pasta {caminho_n8n} será removida após a limpeza do banco.")
                else:
                    print(f"Pasta {caminho_n8n} será removida para preparar a nova instalação.")
                clean_install = True
            else:
                print("Mantendo a pasta de dados existente.")
                clean_install = False

        # Garante existência e permissões da pasta de dados apenas se NÃO for instalação limpa
        if not clean_install:
            os.makedirs(caminho_n8n, exist_ok=True)
            os.chmod(caminho_n8n, 0o777)
        
        # PASSO 3: Reutilização automática do n8n.env somente se manter dados
        reuse_env = False
        env_data = {}
        if (not clean_install) and os.path.isfile(env_file_path):
            print(f"\nReutilizando arquivo de configuração existente: {env_file_path}")
            reuse_env = True
            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            env_data[k.strip()] = v.strip()
                print("✔ Configurações carregadas do arquivo existente.")
            except Exception as ex:
                print(f"Aviso: erro ao ler {env_file_path}: {ex}")
                reuse_env = False
        
        # PASSO 4: Coletar configurações DB/Redis apenas se não reaproveitar
        postgres_host = ""
        postgres_db = ""
        postgres_user = ""
        postgres_password = ""
        postgres_port = ""
        redis_host = ""
        redis_port = ""
        redis_password = ""
        
        if (is_main or is_worker) and not reuse_env:
            print("\n" + "="*60)
            print("Configurações de banco de dados PostgreSQL:")
            postgres_host = input("Host do PostgreSQL (padrão: postgres): ").strip() or "postgres"
            postgres_port = input("Porta do PostgreSQL (padrão: 5432): ").strip() or "5432"
            postgres_db = input("Nome do banco (padrão: N8N): ").strip() or "N8N"
            postgres_user = input("Usuário do banco (padrão: N8N): ").strip() or "N8N"
            postgres_password = input(f"Senha do usuário '{postgres_user}' do PostgreSQL: ").strip()
            
            if not postgres_password:
                postgres_password = self.generate_password()
                print("⚠️ Senha gerada automaticamente para o PostgreSQL.")
            
            print("\n" + "="*60)
            print("Configurações Redis (fila):")
            redis_host = input("Host do Redis (padrão: redis): ").strip() or "redis"
            redis_port = input("Porta do Redis (padrão: 6379): ").strip() or "6379"
            redis_password = input("Senha do Redis (deixe vazio se não tiver): ").strip()
        elif (is_main or is_worker) and reuse_env:
            # Carrega do env_data
            postgres_host = env_data.get('DB_POSTGRESDB_HOST', 'postgres')
            postgres_port = env_data.get('DB_POSTGRESDB_PORT', '5432')
            postgres_db = env_data.get('DB_POSTGRESDB_DATABASE', 'N8N')
            postgres_user = env_data.get('DB_POSTGRESDB_USER', 'N8N')
            postgres_password = env_data.get('DB_POSTGRESDB_PASSWORD', '')
            redis_host = env_data.get('QUEUE_BULL_REDIS_HOST', 'redis')
            redis_port = env_data.get('QUEUE_BULL_REDIS_PORT', '6379')
            redis_password = env_data.get('QUEUE_BULL_REDIS_PASSWORD', '')

        # PASSO 4.1: Se usuário escolheu nova instalação no Main, limpar o banco automaticamente
        if is_main and clean_install:
            # Garante senha caso reuse_env não tenha trazido
            if not postgres_password:
                postgres_password = self.generate_password()
                print("[!] Senha do owner do banco estava vazia e foi gerada automaticamente.")
            try:
                print("\n=== Limpando banco de dados (DROP e recriação) ===")
                print(f"Banco: '{postgres_db}' em {postgres_host}:{postgres_port} (owner: {postgres_user})")
                self.limpar_banco_postgres(postgres_host, postgres_port, postgres_db, postgres_user, postgres_password)
                print("✔ Banco de dados limpo e recriado com sucesso.")
            except Exception as ex:
                print(f"Aviso: falha ao limpar o banco de dados: {ex}")
        
        # Após limpeza do banco (se aplicável), remover a pasta de dados se estiver pendente
        if clean_install and pending_delete_dir:
            try:
                if os.path.exists(pending_delete_dir):
                    shutil.rmtree(pending_delete_dir, ignore_errors=True)
                    print(f"Pasta {pending_delete_dir} removida para nova instalação.")
            except Exception as ex:
                print(f"Aviso: não foi possível remover {pending_delete_dir}: {ex}")

        # Garantia final: a pasta de dados do n8n precisa existir e ser gravável
        # para que o usuário 'node' dentro do container consiga criar /home/node/.n8n/config
        try:
            os.makedirs(caminho_n8n, exist_ok=True)
            os.chmod(caminho_n8n, 0o777)
            nodes_dir = os.path.join(caminho_n8n, 'nodes')
            os.makedirs(nodes_dir, exist_ok=True)
            try:
                os.chmod(nodes_dir, 0o777)
            except Exception:
                pass
        except Exception:
            pass
        # PASSO 5: Configurações específicas do Main ou Simples (domínio, chave, porta)
        n8n_host = ""
        webhook_url = ""
        encryption_key = ""
        porta_publicar = ""
        
        if is_main or is_simples:
            print("\n" + "="*60)
            tipo_texto = "servidor" if is_main else "instalação simples"
            print(f"Configurações do {tipo_texto}:")
            
            if reuse_env:
                n8n_host = env_data.get('N8N_HOST', '')
                encryption_key = env_data.get('N8N_ENCRYPTION_KEY', '')
                # Se estiver reutilizando env, mas a chave estiver ausente em modo Main, gere uma nova
                if is_main and not encryption_key:
                    try:
                        encryption_key = self.generate_password(32)
                        print(f"?? Chave de encriptação ausente no n8n.env. Gerada: {encryption_key}")
                        print("?? GUARDE ESTA CHAVE! Necessária para descriptografar credenciais.")
                        # Garante que o env_data contenha a chave para persistência adiante
                        env_data['N8N_ENCRYPTION_KEY'] = encryption_key
                    except Exception as ex:
                        print(f"Aviso: falha ao gerar chave de encriptação: {ex}")
                porta_publicar = "5678"  # Porta padrão quando reutilizando
            else:
                n8n_host = input("Domínio público (ex: n8n.seudominio.com, deixe vazio para pular): ").strip()
                
                if not is_simples:  # Encryption key só é necessário para Main com banco
                    encryption_key = input("Chave de encriptação (deixe vazio para gerar): ").strip()
                    if not encryption_key:
                        encryption_key = self.generate_password(32)
                        print(f"⚠️ Chave gerada: {encryption_key}")
                        print("⚠️ GUARDE ESTA CHAVE! Necessária para descriptografar credenciais.")
                
                porta_publicar = input("Porta para expor (padrão: 5678): ").strip() or "5678"
            
            if n8n_host:
                webhook_url = f"https://{n8n_host}/"
                print(f"✔ Webhook URL: {webhook_url}")

        # PASSO 5.1: Concorrência de workers (apenas Simples e Worker)
        # Worker: solicitar a N8N_ENCRYPTION_KEY usada no Main
        if is_worker and not reuse_env:
            encryption_key = input("Informe a mesma N8N_ENCRYPTION_KEY usada no servidor Main: ").strip()
            if not encryption_key:
                print("Aviso: N8N_ENCRYPTION_KEY nao informada no Worker; workflows com credenciais podem falhar.")
        elif is_worker and reuse_env:
            encryption_key = env_data.get('N8N_ENCRYPTION_KEY', encryption_key)
        worker_concurrency = "10"
        if is_simples or is_worker:
            # Segue o mesmo padrão de entrada com fallback: input(...).strip() or "10"
            worker_concurrency = (
                env_data.get('N8N_WORKER_CONCURRENCY', '') if reuse_env else input("Quantidade de processos em paralelo (padrão: 10): ").strip()
            ) or "10"
            # Sanitiza valor inválido
            if not str(worker_concurrency).isdigit() or int(worker_concurrency) < 1:
                worker_concurrency = "10"
        
        # PASSO 6: Constrói comando base do container
        comando_base = f"""docker run -d \
            --name {container_name} \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -v {caminho_n8n}:/home/node/.n8n"""
        
        # Variáveis de ambiente - diferentes para cada tipo
        if is_simples:
            # Instalação simples: sem banco externo, sem Redis, sem workers
            # Adiciona variáveis recomendadas para evitar warnings
            env_vars = f""" \
            -e DB_SQLITE_POOL_SIZE=3 \
            -e N8N_RUNNERS_ENABLED=true \
            -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
            -e N8N_GIT_NODE_DISABLE_BARE_REPOS=true \
            -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true"""
        else:
            # Main ou Worker: com PostgreSQL e Redis
            env_vars = f""" \
            -e DB_TYPE=postgresdb \
            -e DB_POSTGRESDB_HOST={shlex.quote(str(postgres_host))} \
            -e DB_POSTGRESDB_PORT={shlex.quote(str(postgres_port))} \
            -e DB_POSTGRESDB_DATABASE={shlex.quote(str(postgres_db))} \
            -e DB_POSTGRESDB_USER={shlex.quote(str(postgres_user))} \
            -e DB_POSTGRESDB_PASSWORD={shlex.quote(str(postgres_password))} \
            -e QUEUE_BULL_REDIS_HOST={shlex.quote(str(redis_host))} \
            -e QUEUE_BULL_REDIS_PORT={shlex.quote(str(redis_port))} \
            -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
            -e N8N_RUNNERS_ENABLED=true \
            -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
            -e N8N_GIT_NODE_DISABLE_BARE_REPOS=true"""
        
        # Adiciona senha do Redis se informada (só para Main/Worker)
        if redis_password and not is_simples:
            env_vars += f""" \
            -e QUEUE_BULL_REDIS_PASSWORD={shlex.quote(str(redis_password))}"""

        # Configurações específicas por tipo
        if is_simples:
            # Instalação simples: apenas configurações básicas
            if n8n_host:
                env_vars += f""" \
            -e N8N_HOST={shlex.quote(str(n8n_host))} \
            -e N8N_PROTOCOL=https \
            -e WEBHOOK_URL={shlex.quote(str(webhook_url))} \
            -e N8N_PROXY_HOPS=1 \
            -e N8N_SECURE_COOKIE=true"""
            
            # Porta exposta
            env_vars += f""" \
            -p {porta_publicar}:5678"""
            # Limita processos em paralelo (aplicado também no simples; sem efeito no main)
            env_vars += f""" \
            -e N8N_WORKER_CONCURRENCY={shlex.quote(str(worker_concurrency))}"""
            
        elif is_main:
            # Variáveis específicas do Main
            env_vars += f""" \
            -e EXECUTIONS_MODE=queue \
            -e OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true"""
            # Exporta N8N_ENCRYPTION_KEY somente se não estiver vazia
            if encryption_key:
                env_vars += f""" \
            -e N8N_ENCRYPTION_KEY={shlex.quote(str(encryption_key))}"""
            
            if n8n_host:
                env_vars += f""" \
            -e N8N_HOST={shlex.quote(str(n8n_host))} \
            -e N8N_PROTOCOL=https \
            -e WEBHOOK_URL={shlex.quote(str(webhook_url))} \
            -e N8N_PROXY_HOPS=1 \
            -e N8N_SECURE_COOKIE=true"""
            
            # Porta exposta apenas no Main
            env_vars += f""" \
            -p {porta_publicar}:5678"""
        
        else:  # Worker
            # Worker apenas processa, não precisa de porta exposta
            env_vars += f""" \
            -e EXECUTIONS_MODE=queue \
            -e QUEUE_WORKER_ID={shlex.quote(str(container_name))} \
            -e N8N_WORKER_CONCURRENCY={shlex.quote(str(worker_concurrency))}"""
        
        # Injeta N8N_ENCRYPTION_KEY para Worker, se informada
        try:
            if is_worker and encryption_key:
                env_vars += f""" \
            -e N8N_ENCRYPTION_KEY={shlex.quote(str(encryption_key))}"""
        except Exception:
            pass

        # Comando completo
        # Persiste .env com as variáveis utilizadas para reutilização futura
        try:
            env_map = {}
            if is_simples:
                env_map.update({
                    'DB_SQLITE_POOL_SIZE': '3',
                    'N8N_RUNNERS_ENABLED': 'true',
                    'N8N_BLOCK_ENV_ACCESS_IN_NODE': 'false',
                    'N8N_GIT_NODE_DISABLE_BARE_REPOS': 'true',
                    'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS': 'true',
                    'N8N_WORKER_CONCURRENCY': str(worker_concurrency),
                })
            else:
                env_map.update({
                    'DB_TYPE': 'postgresdb',
                    'DB_POSTGRESDB_HOST': str(postgres_host),
                    'DB_POSTGRESDB_PORT': str(postgres_port),
                    'DB_POSTGRESDB_DATABASE': str(postgres_db),
                    'DB_POSTGRESDB_USER': str(postgres_user),
                    'DB_POSTGRESDB_PASSWORD': str(postgres_password),
                    'QUEUE_BULL_REDIS_HOST': str(redis_host),
                    'QUEUE_BULL_REDIS_PORT': str(redis_port),
                    'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS': 'true',
                    'N8N_RUNNERS_ENABLED': 'true',
                    'N8N_BLOCK_ENV_ACCESS_IN_NODE': 'false',
                    'N8N_GIT_NODE_DISABLE_BARE_REPOS': 'true',
                })
                if redis_password:
                    env_map['QUEUE_BULL_REDIS_PASSWORD'] = str(redis_password)
                # Para workers, define concorrência
                if is_worker:
                    env_map['N8N_WORKER_CONCURRENCY'] = str(worker_concurrency)
                    if encryption_key:
                        env_map['N8N_ENCRYPTION_KEY'] = str(encryption_key)
            if is_main:
                env_map['EXECUTIONS_MODE'] = 'queue'
                env_map['OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS'] = 'true'
                if encryption_key:
                    env_map['N8N_ENCRYPTION_KEY'] = str(encryption_key)
            if n8n_host:
                env_map.update({
                    'N8N_HOST': str(n8n_host),
                    'N8N_PROTOCOL': 'https',
                    'WEBHOOK_URL': str(webhook_url),
                    'N8N_PROXY_HOPS': '1',
                    'N8N_SECURE_COOKIE': 'true',
                })
            # Salva arquivo env
            os.makedirs(caminho_n8n, exist_ok=True)
            with open(env_file_path, 'w', encoding='utf-8') as fenv:
                fenv.write('# n8n environment variables\n')
                for k, v in env_map.items():
                    if v is None:
                        continue
                    # Evita quebras de linha e espaços à direita
                    fenv.write(f"{k}={str(v).strip()}\n")
            try:
                os.chmod(env_file_path, 0o600)
            except Exception:
                pass
            print(f"\n✔ Arquivo de configuração salvo: {env_file_path}")
        except Exception as ex:
            print(f"Aviso: não foi possível salvar o env em {env_file_path}: {ex}")

        # Seleciona a imagem e entrypoint correto (web padrão ou worker)
        image_cmd = "docker.n8n.io/n8nio/n8n:latest"
        if is_worker:
            image_cmd += " worker"

        comando_completo = comando_base + env_vars + f" \\\n+            {image_cmd}\n            "
        
        # Saneia string do comando para evitar '+' deixado por engano e quebras formatadas
        comando_completo = comando_completo.replace("+            ", "")
        comandos = [comando_completo]
        
        # Remove container se existir
        self.remove_container(container_name)
        
        # Executa instalação
        self.executar_comandos(comandos)
        
        time.sleep(30)
        os.chmod(caminho_n8n, 0o777)
        
        # Mensagens finais
        print("\n" + "="*60)
        print(f"✔ Instalação do n8n ({tipo_suffix.upper()}) concluída!")
        print("="*60)
        
        if is_simples:
            print(f'\n✔ Instalação simples configurada!')
            print(f'\nAcesse o n8n em http://<seu_ip>:{porta_publicar}')
            if n8n_host:
                print(f'Ou via domínio: https://{n8n_host}')
            print('\nNa primeira execução você precisará criar um usuário e senha.')
            print('\n📝 Características desta instalação:')
            print('   - Banco de dados: SQLite (arquivo local)')
            print('   - Execuções: Modo local (sem fila/workers)')
            print('   - Dados salvos em: ' + caminho_n8n)
            print('\n⚠️ NOTA: Para produção com múltiplos workers, use a opção "Main"')
            
        elif is_main:
            print(f'\nAcesse o n8n em http://<seu_ip>:{porta_publicar}')
            if n8n_host:
                print(f'Ou via domínio: https://{n8n_host}')
            print('\nNa primeira execução você precisará criar um usuário e senha.')
            print(f'\n⚠️ IMPORTANTE - Guarde estas informações:')
            print(f'   - Chave de encriptação: {encryption_key}')
            print(f'   - Senha PostgreSQL: [oculta]')
        else:
            print('\n✔ Worker configurado e em execução.')
            print('Este worker processará tarefas da fila automaticamente.')
        
        # Note about secure cookies when behind HTTPS
        try:
            if n8n_host:
                print("\nAviso: N8N_SECURE_COOKIE=true habilitado (requer HTTPS).")
                print("Para testar via HTTP, pare o container e defina N8N_SECURE_COOKIE=false, depois reinicie.")
        except Exception:
            pass

        print("\n" + "="*60)
    
    def cria_dynamic_conf_traefik(self, email=None):
        base_dir = f"{self.install_principal}/traefik"
        dyn_dir  = f"{base_dir}/dynamic"
        le_dir   = f"{base_dir}/lets-encrypt"
        dynamic_conf = f"{dyn_dir}/dynamic_conf.yml"

        # pastas
        os.makedirs(dyn_dir, exist_ok=True)
        os.makedirs(le_dir,  exist_ok=True)

        # acme.json (perms 600)
        acme_path = f"{le_dir}/acme.json"
        if not os.path.exists(acme_path):
            with open(acme_path, "w") as _f:
                _f.write("")
            os.chmod(acme_path, 0o600)

        # cria arquivo dinâmico somente com http:{routers,services}
        if not os.path.exists(dynamic_conf):
            data = {"http": {"routers": {}, "services": {}}}
            with open(dynamic_conf, "w") as f:
                yaml.safe_dump(data, f, sort_keys=False)

        return dynamic_conf
        
    def adiciona_roteador_servico_traefik(self, dominio=None, endereco=None, porta=None):
        self.verifica_container_existe('traefik', self.instala_traefik)

        if dominio is None:
            dominio = input('Digite o dominio (sem o www): ').strip()
        if endereco is None:
            endereco = input('Coloque o endereço do container ou IP da rede que deseja apontar: ').strip()
        if porta is None:
            porta = input('Digite a porta (se for container, use a porta INTERNA): ').strip()

        # valida domínio (sem underscore)
        if "_" in dominio or not re.match(r"^[A-Za-z0-9.-]+$", dominio):
            raise ValueError(f"Domínio inválido: {dominio}. Use apenas letras, números, hífens e pontos (sem _ ).")

        # garante rede entre traefik e o container de destino (sua função existente)
        self.cria_rede_docker(associar_container_nome=endereco, numero_rede=0)

        dynamic_conf = self.cria_dynamic_conf_traefik()

        # carrega, edita e salva
        with open(dynamic_conf, 'r') as file:
            config = yaml.safe_load(file) or {}

        config.setdefault('http', {})
        config['http'].setdefault('routers', {})
        config['http'].setdefault('services', {})

        router_name  = dominio.replace('.', '_')
        service_name = f"{router_name}_service"

        # router HTTPS (websecure) — TLS via certResolver "le"
        config['http']['routers'][router_name] = {
            'rule': f"Host(`{dominio}`)",
            'entryPoints': ['websecure'],
            'service': service_name,
            'tls': {'certResolver': 'le'}
        }

        # service para o backend alvo
        config['http']['services'][service_name] = {
            'loadBalancer': {'servers': [{'url': f"http://{endereco}:{porta}"}]}
        }

        with open(dynamic_conf, 'w') as file:
            yaml.safe_dump(config, file, sort_keys=False)

        print(f"✔ Router/Service adicionados: {dominio} -> http://{endereco}:{porta}")
        print(f"Arquivo: {dynamic_conf}")
        print("Obs: cert (LE) depende do DNS A (e AAAA correto/ausente) apontando para este servidor.")

    def instala_traefik(self):
        print("Iniciando instalação do Traefik.")
        email = input('Digite um e-mail para gerar o certificado: ').strip()

        # garante estrutura dinâmica e acme.json 600
        self.cria_dynamic_conf_traefik(email=email)

        base_dir = f"{self.install_principal}/traefik"
        dyn_dir  = f"{base_dir}/dynamic"
        le_dir   = f"{base_dir}/lets-encrypt"

        self.remove_container('traefik')

        comando = f"""docker run -d \
        --name traefik \
        --restart=unless-stopped \
        --memory=256m \
        --cpus=1 \
        -p 80:80 \
        -p 443:443 \
        -p 8080:8080 \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v {le_dir}:/letsencrypt \
        -v {dyn_dir}:/etc/traefik/dynamic \
        traefik:latest \
        --log.level=INFO \
        --api.insecure=true \
        --providers.docker=true \
        --providers.docker.exposedbydefault=false \
        --providers.file.directory=/etc/traefik/dynamic \
        --providers.file.watch=true \
        --entrypoints.web.address=:80 \
        --entrypoints.web.http.redirections.entrypoint.to=websecure \
        --entrypoints.web.http.redirections.entrypoint.scheme=https \
        --entrypoints.websecure.address=:443 \
        --certificatesresolvers.le.acme.email={email} \
        --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json \
        --certificatesresolvers.le.acme.httpchallenge=true \
        --certificatesresolvers.le.acme.httpchallenge.entrypoint=web
        """
        self.executar_comandos([comando])

        # conecta rede padrão do seu ambiente (como você já fazia)
        self.cria_rede_docker(associar_container_nome='traefik', numero_rede=0)

        print('\nIPs possíveis para acesso:')
        self.executar_comandos(["hostname -I | tr ' ' '\\n'"])
        print('Porta de acesso (dashboard temporária): 8080')
        
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
                    --user 0:0 \
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
        
        # Aguarda e captura a senha gerada automaticamente
        print("Aguardando senha ser gerada...")
        time.sleep(15)
        
        senha_padrao = None
        try:
            result = subprocess.run(
                "docker logs filebrowser".split(),
                capture_output=True,
                text=True
            )
            
            # Busca pela senha nos logs
            for linha in result.stderr.splitlines():
                if "randomly generated password:" in linha:
                    senha_padrao = linha.split("randomly generated password:")[1].strip()
                    break
                
        except Exception as e:
            print(f"Erro: {e}")
        
        print(f"Possiveis ip's para acesso:")
        comandos = [
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f'Porta para uso local: {portas[0]}')
        print(f'Usuario padrão: admin')
        
        if senha_padrao:
            print(f'Senha gerada automaticamente: {senha_padrao}')
        else:
            print(f'📌 IMPORTANTE: Verifique os logs para obter a senha inicial!')
            print(f'Execute: docker logs filebrowser')
            print(f'Procure pela linha com "randomly generated password:"')
        
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
        
        # Instalar extensões PHP
        print("\n" + "="*60)
        print("Instalando PHP 8.4 e extensões...")
        print("="*60)
        
        script_bash = """set +e
export DEBIAN_FRONTEND=noninteractive

echo "Instalando PHP 8.4..."
apt-get update

# Instala o PHP 8.4 e extensões
echo "Instalando lsphp84 e extensões disponíveis..."
for ext in "" pgsql mysql curl common imap opcache gd; do
    pkg="lsphp84${ext:+-}${ext}"
    echo -n "  - ${pkg}: "
    if apt-get install -y ${pkg} >/dev/null 2>&1; then
        echo "OK"
    else
        echo "Não disponível"
    fi
done

# Define o PHP 8.4 como padrão
echo ""
echo "Configurando PHP 8.4 como padrão..."
ln -sf /usr/local/lsws/lsphp84/bin/lsphp /usr/local/lsws/fcgi-bin/lsphp

# Reinicia o servidor
/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1

echo ""
echo "Versão PHP instalada:"
/usr/local/lsws/lsphp84/bin/php -v
echo ""
echo "Extensões PHP instaladas:"
/usr/local/lsws/lsphp84/bin/php -m | sort
"""
        subprocess.run(
            ["docker", "exec", "-u", "root", "-it", "openlitespeed", "bash", "-lc", script_bash],
            check=True,
            text=True
        )
        
        # Cria arquivo de configuração personalizado do PHP
        print("\n" + "="*60)
        print("Criando arquivo de configuração personalizado do PHP...")
        print("="*60)
        
        php_custom_ini_path = f"{conf_completa}/lsphp84/etc/php/8.4/mods-available/99-custom.ini"
        os.makedirs(os.path.dirname(php_custom_ini_path), exist_ok=True)
        
        php_custom_config = """;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Configurações Personalizadas PHP 8.4 - OpenLiteSpeed
; Arquivo: 99-custom.ini
; 
; Este arquivo contém APENAS configurações customizadas que sobrescrevem o php.ini padrão
; Edite conforme suas necessidades específicas
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

[PHP]
; ============================================================================
; TIMEOUTS E LIMITES DE RECURSOS
; ============================================================================
max_execution_time = 300
max_input_time = 300
default_socket_timeout = 300
memory_limit = 1024M
max_input_vars = 5000

; ============================================================================
; UPLOAD DE ARQUIVOS
; ============================================================================
upload_max_filesize = 1024M
post_max_size = 1024M
max_file_uploads = 20

; ============================================================================
; TIMEZONE
; ============================================================================
date.timezone = America/Sao_Paulo

; ============================================================================
; ERROS E LOGS (PRODUÇÃO)
; ============================================================================
display_errors = Off
display_startup_errors = Off
log_errors = On
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT

; ============================================================================
; SEGURANÇA - Funções desabilitadas
; Remova funções desta lista se precisar usá-las
; ============================================================================
disable_functions = exec,passthru,shell_exec,system,proc_open,popen

; ============================================================================
; OPCACHE - OTIMIZAÇÕES DE PERFORMANCE
; ============================================================================
[opcache]
opcache.enable = 1
opcache.enable_cli = 0
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 20000
opcache.validate_timestamps = 1
opcache.revalidate_freq = 2
opcache.save_comments = 1
opcache.enable_file_override = 1
opcache.fast_shutdown = 1

; ============================================================================
; SESSION - SEGURANÇA
; ============================================================================
[Session]
session.cookie_httponly = 1
session.cookie_samesite = Lax
session.use_strict_mode = 1
session.gc_maxlifetime = 3600

; ============================================================================
; MYSQLI - Configurações padrão
; ============================================================================
[MySQLi]
mysqli.default_socket = /var/run/mysqld/mysqld.sock

; ============================================================================
; POSTGRESQL
; ============================================================================
[PostgreSQL]
pgsql.allow_persistent = On

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; INSTRUÇÕES DE USO:
;
; 📝 Para editar: nano /install_principal/openlitespeed/conf_completa/lsphp84/etc/php/8.4/mods-available/99-custom.ini
; 🔄 Após editar: docker exec openlitespeed /usr/local/lsws/bin/lswsctrl restart
; 📊 Ver configurações: docker exec openlitespeed /usr/local/lsws/lsphp84/bin/php -i | grep -i "nome_da_config"
;
; EXEMPLOS DE CUSTOMIZAÇÃO:
; - Para debug: display_errors = On
; - Mais memória: memory_limit = 2048M
; - Uploads maiores: upload_max_filesize = 2048M
; - Timeout maior: max_execution_time = 600
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
"""
        with open(php_custom_ini_path, 'w') as f:
            f.write(php_custom_config)
        
        os.chmod(php_custom_ini_path, 0o644)
        
        print(f"✔ Arquivo de configuração criado: {php_custom_ini_path}")
        
        # Reinicia o container para aplicar as mudanças
        print("Reiniciando o container OpenLiteSpeed...")
        subprocess.run(
            ["docker", "restart", "openlitespeed"],
            check=True
        )
        time.sleep(10)  # Aguarda o container reiniciar completamente
        
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
        
        self.gerenciar_permissoes_pasta(site_dir, permissao='777')
        
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
        
        # Ajusta permissões para o usuário nobody (usuário do OpenLiteSpeed)
        print(f"Ajustando permissões do site '{nome_dominio_}'...")
        comandos_permissoes = [
            f"docker exec openlitespeed chown -R nobody:nogroup /var/www/vhosts/{nome_dominio_}",
            f"docker exec openlitespeed chmod -R 755 /var/www/vhosts/{nome_dominio_}",
            f"docker exec openlitespeed chmod -R 775 /var/www/vhosts/{nome_dominio_}/public_html",
        ]
        self.executar_comandos(comandos_permissoes)
        
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
        elif selecao == "2" or selecao == "16":
            versao = '16'
            porta = '5434'
        elif selecao == "3" or selecao == "17":
            versao = '17'
            porta = '5435'
        else:
            print("Seleção incorreta.")
            return

        if not hasattr(self, 'postgres_password') or not self.postgres_password:
            self.postgres_password = input("Digite a senha do usuário postgres: ")

        versao_ = versao.replace('.', '_')

        print('Instalando o Postgres.\n')

        container_db = f"""docker run -d \
            --name postgres_{versao_} \
            --restart=unless-stopped \
            --memory=256m \
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

        print(f'Instalação do Postgres completa.\n')
        print(f'Acesso:')
        print(f' - ssh -L {porta}:localhost:{porta} usuario@servidor_remoto')
        print(f' - Local instalação: {self.bds}/postgres/{versao_}')
        print(f' - Usuario: postgres')
        # Senha do Postgres ocultada por segurança
        print(f' - Porta interna: 5432')
        print(f' - Porta externa: {porta}')
    
    def gerenciar_bancos_postgres(self):
        """Menu para gerenciar bancos de dados PostgreSQL"""
        print("\n=== GERENCIAMENTO DE BANCOS DE DADOS POSTGRESQL ===\n")
        
        # Verificar containers PostgreSQL disponíveis
        print("Verificando containers PostgreSQL disponíveis...")
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=postgres_", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container PostgreSQL em execução encontrado.")
            print("Instale o PostgreSQL primeiro usando a opção '** BD ** Instala postgres'")
            return
        
        print("\nContainers PostgreSQL disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container (número): ").strip()
        try:
            container_idx = int(escolha) - 1
            if container_idx < 0 or container_idx >= len(containers):
                print("❌ Opção inválida.")
                return
            container = containers[container_idx]
        except ValueError:
            print("❌ Entrada inválida.")
            return
        
        # Menu de operações
        print(f"\n=== OPERAÇÕES NO CONTAINER: {container} ===")
        print("[1] Criar banco de dados")
        print("[2] Listar bancos de dados")
        print("[3] Apagar banco de dados")
        print("[0] Voltar")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            self.criar_banco_postgres(container)
        elif opcao == "2":
            self.listar_bancos_postgres(container)
        elif opcao == "3":
            self.apagar_banco_postgres(container)
        elif opcao == "0":
            return
        else:
            print("❌ Opção inválida.")
    
    def criar_banco_postgres(self, container):
        """Cria um novo banco de dados PostgreSQL com usuário e senha"""
        print("\n=== CRIAR BANCO DE DADOS POSTGRESQL ===\n")
        
        max_tentativas = 3
        
        # ==================== COLETA NOME DO BANCO ====================
        for tentativa in range(1, max_tentativas + 1):
            nome_banco = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome do banco de dados: ").strip()
            if nome_banco:
                break
            print(f"❌ Nome do banco não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return
        
        # ==================== COLETA NOME DO USUÁRIO ====================
        for tentativa in range(1, max_tentativas + 1):
            usuario = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome do usuário (deixe vazio para usar '{nome_banco}'): ").strip()
            if not usuario:
                usuario = nome_banco
                print(f"ℹ️  Usando '{usuario}' como nome de usuário.")
                break
            elif len(usuario) >= 3:
                break
            print(f"❌ Usuário deve ter pelo menos 3 caracteres. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return
        
        # ==================== COLETA SENHA ====================
        for tentativa in range(1, max_tentativas + 1):
            senha = input(f"[Tentativa {tentativa}/{max_tentativas}] Senha para o usuário '{usuario}' (mínimo 4 caracteres): ").strip()
            if len(senha) >= 4:
                break
            print(f"❌ Senha deve ter pelo menos 4 caracteres. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return
        
        # ==================== CONFIRMAÇÃO FINAL ====================
        print("\n" + "="*60)
        print("📋 RESUMO DA OPERAÇÃO:")
        print(f"   Banco de dados: {nome_banco}")
        print(f"   Usuário: {usuario}")
        print(f"   Senha: {'*' * len(senha)}")
        print(f"   Container: {container}")
        print("="*60)
        
        confirmar = input("\n✅ Confirma a criação com esses dados? (s/n): ").strip().lower()
        if confirmar != 's':
            print("❌ Operação cancelada pelo usuário.")
            return
        
        print(f"\n📝 Criando banco de dados '{nome_banco}' com usuário '{usuario}'...")
        
        try:
            # Criar usuário (com aspas duplas para preservar case)
            cmd_usuario = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"CREATE USER \"{usuario}\" WITH PASSWORD '{senha}';"
            ]
            resultado = subprocess.run(cmd_usuario, capture_output=True, text=True)
            
            if resultado.returncode != 0 and "already exists" not in resultado.stderr:
                print(f"❌ Erro ao criar usuário: {resultado.stderr}")
                return
            elif "already exists" in resultado.stderr:
                print(f"⚠️  Usuário '{usuario}' já existe, usando existente.")
            else:
                print(f"✅ Usuário '{usuario}' criado com sucesso.")
            
            # Criar banco de dados (com aspas duplas para preservar case)
            cmd_banco = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"CREATE DATABASE \"{nome_banco}\" OWNER \"{usuario}\";"
            ]
            resultado = subprocess.run(cmd_banco, capture_output=True, text=True)
            
            if resultado.returncode != 0:
                if "already exists" in resultado.stderr:
                    print(f"⚠️  Banco '{nome_banco}' já existe.")
                else:
                    print(f"❌ Erro ao criar banco: {resultado.stderr}")
                    return
            else:
                print(f"✅ Banco de dados '{nome_banco}' criado com sucesso.")
            
            # Conceder privilégios (com aspas duplas para preservar case)
            cmd_grant = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"GRANT ALL PRIVILEGES ON DATABASE \"{nome_banco}\" TO \"{usuario}\";"
            ]
            subprocess.run(cmd_grant, capture_output=True, text=True)
            print(f"✅ Privilégios concedidos ao usuário '{usuario}'.")
            
            print("\n" + "="*60)
            print("📌 INFORMAÇÕES DE CONEXÃO:")
            print(f"   Host: localhost (ou IP do servidor)")
            print(f"   Banco: {nome_banco}")
            print(f"   Usuário: {usuario}")
            print(f"   Senha: {senha}")
            print(f"   Container: {container}")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Erro ao criar banco de dados: {e}")
    
    def listar_bancos_postgres(self, container):
        """Lista todos os bancos de dados do PostgreSQL"""
        print(f"\n=== BANCOS DE DADOS NO CONTAINER: {container} ===\n")
        try:
            cmd = [
                "docker", "exec", container, "psql", "-U", "postgres", "-A", "-F|", "-c",
                "SELECT datname, pg_catalog.pg_get_userbyid(datdba) as owner FROM pg_database ORDER BY datname;"
            ]
            resultado = subprocess.run(cmd, capture_output=True, text=True)
            if resultado.returncode != 0:
                print(f"❌ Erro ao listar bancos: {resultado.stderr}")
                return
            linhas = resultado.stdout.strip().split('\n')
            bancos_padrao = ['postgres', 'template0', 'template1']
            bancos_usuario = []
            bancos_sistema = []
            
            # Processa todas as linhas ignorando cabeçalho e rodapé
            for linha in linhas:
                # Ignora linhas vazias, cabeçalho e rodapé
                if not linha or linha.startswith('datname|') or linha.startswith('(') or linha.startswith('-'):
                    continue
                
                partes = linha.split('|')
                if len(partes) < 2:
                    continue
                
                nome = partes[0].strip()
                owner = partes[1].strip()
                
                # Pula se for linha vazia após split
                if not nome:
                    continue
                
                if nome in bancos_padrao:
                    bancos_sistema.append((nome, owner))
                else:
                    bancos_usuario.append((nome, owner))
            print(f"\n=== BANCOS DE DADOS NO CONTAINER: {container} ===\n")
            print("--- Bancos do sistema (padrão) ---")
            for nome, owner in bancos_sistema:
                print(f"  {nome:<15} (owner: {owner})")
            print("\n--- Bancos criados pelo usuário ---")
            if bancos_usuario:
                for nome, owner in bancos_usuario:
                    print(f"  {nome:<15} (owner: {owner})")
            else:
                print("  Nenhum banco de usuário encontrado.")
        except Exception as e:
            print(f"❌ Erro ao listar bancos de dados: {e}")
            print(f"❌ Erro ao listar bancos de dados: {e}")
    
    def apagar_banco_postgres(self, container):
        """Apaga um banco de dados PostgreSQL"""
        print(f"\n=== APAGAR BANCO DE DADOS NO CONTAINER: {container} ===\n")
        
        # Primeiro listar os bancos
        self.listar_bancos_postgres(container)
        
        max_tentativas = 3
        
        # ==================== COLETA NOME DO BANCO ====================
        for tentativa in range(1, max_tentativas + 1):
            nome_banco = input(f"\n[Tentativa {tentativa}/{max_tentativas}] Nome do banco de dados a ser APAGADO: ").strip()
            
            if not nome_banco:
                print(f"❌ Nome do banco não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                    return
                continue
            
            # Bancos do sistema que não podem ser apagados
            bancos_sistema = ['postgres', 'template0', 'template1']
            if nome_banco in bancos_sistema:
                print(f"❌ Não é permitido apagar bancos do sistema: {', '.join(bancos_sistema)}")
                print(f"   Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                    return
                continue
            
            # Nome válido, sair do loop
            break
        
        # ==================== CONFIRMAÇÃO DE EXCLUSÃO ====================
        for tentativa in range(1, max_tentativas + 1):
            print(f"\n⚠️  ATENÇÃO: Você está prestes a APAGAR o banco '{nome_banco}'!")
            print("⚠️  Esta ação é IRREVERSÍVEL e todos os dados serão perdidos!")
            confirmacao = input(f"[Tentativa {tentativa}/{max_tentativas}] Digite 'CONFIRMAR' para prosseguir: ").strip()
            
            if confirmacao == "CONFIRMAR":
                break
            
            print(f"❌ Confirmação incorreta. Digite exatamente 'CONFIRMAR'.")
            print(f"   Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada por segurança.")
                return
        
        # ==================== PERGUNTA SOBRE USUÁRIO ====================
        for tentativa in range(1, max_tentativas + 1):
            apagar_usuario = input(f"[Tentativa {tentativa}/{max_tentativas}] Apagar também o usuário de mesmo nome? (s/n): ").strip().lower()
            
            if apagar_usuario in ['s', 'n']:
                break
            
            print(f"❌ Responda apenas 's' ou 'n'. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("⚠️  Assumindo 'n' (não apagar usuário).")
                apagar_usuario = 'n'
        
        try:
            # Forçar desconexão de todas as sessões ativas (aspas simples para string)
            print(f"\n📝 Desconectando sessões ativas do banco '{nome_banco}'...")
            cmd_disconnect = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{nome_banco}';"
            ]
            subprocess.run(cmd_disconnect, capture_output=True, text=True)
            
            # Apagar banco (com aspas duplas para preservar case)
            print(f"📝 Apagando banco de dados '{nome_banco}'...")
            cmd_drop = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"DROP DATABASE \"{nome_banco}\";"
            ]
            resultado = subprocess.run(cmd_drop, capture_output=True, text=True)
            
            if resultado.returncode == 0:
                print(f"✅ Banco de dados '{nome_banco}' apagado com sucesso.")
            else:
                print(f"❌ Erro ao apagar banco: {resultado.stderr}")
                return
            
            # Apagar usuário se solicitado (com aspas duplas para preservar case)
            if apagar_usuario == 's':
                print(f"📝 Apagando usuário '{nome_banco}'...")
                cmd_drop_user = [
                    "docker", "exec", container, "psql", "-U", "postgres", "-c",
                    f"DROP USER IF EXISTS \"{nome_banco}\";"
                ]
                resultado = subprocess.run(cmd_drop_user, capture_output=True, text=True)
                
                if resultado.returncode == 0:
                    print(f"✅ Usuário '{nome_banco}' apagado com sucesso.")
                else:
                    print(f"⚠️  Aviso ao apagar usuário: {resultado.stderr}")
            
        except Exception as e:
            print(f"❌ Erro ao apagar banco de dados: {e}")

    def limpar_banco_postgres(self, host, port, db_name, db_owner, db_password):
        """
        Limpeza simples do banco: remove e recria o schema 'public' usando um cliente psql
        executado via container temporário do Postgres. Mantém o banco e o owner; apenas zera o conteúdo.
        """
        print("Iniciando container temporário do Postgres para limpar via schema (psql)...")
        base_cmd = ["docker", "run", "--rm"]
        # Acesso a localhost do host
        if str(host) in ("localhost", "127.0.0.1"):
            base_cmd += ["--network=host"]
        base_cmd += [
            "-e", f"PGPASSWORD={db_password}",
            "postgres:17",
            "psql",
            "-h", str(host),
            "-p", str(port),
            "-U", str(db_owner),
            "-d", str(db_name),
            "-v", "ON_ERROR_STOP=1",
        ]

        schema_cmds = [
            "DROP SCHEMA IF EXISTS public CASCADE;",
            f"CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION \"{db_owner}\";",
            f"GRANT ALL ON SCHEMA public TO \"{db_owner}\";",
            "GRANT ALL ON SCHEMA public TO public;",
        ]
        for sql in schema_cmds:
            cmd = base_cmd + ["-c", sql]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"Falha ao executar psql via container temporário: {r.stderr}")
        print("Schema public limpo e recriado (via container temporário).")
        return

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
        elif selecao == "2" or selecao == "8.0":
            versao = '8.0'
            porta = '3317'
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
                        -e MYSQL_ROOT_PASSWORD='{self.mysql_root_password}' \
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
        
        if not novo_db:
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
        resposta = input("A instalação do Docker requer uma reinicialização do sistema. Deseja continuar? (s/n) ").strip().lower()
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
        caminho_ollama = f"{self.install_principal}/IA/ollama"
        caminho_open_webui = f"{self.install_principal}/IA/open_webui"
        
        comandos = [
            "docker network create ollama-network",
            f"""docker run -d \
            --name ollama \
            --network ollama-network \
            -p 11434:11434 \
            -e OLLAMA_MAX_LOADED_MODELS=1 \
            -e OLLAMA_NUM_PARALLEL=2 \
            -e OLLAMA_KEEP_ALIVE=1 \
            -v {caminho_ollama}:/root \
            ollama/ollama""",
        ]
        
        comandos += [
            """docker exec -it ollama bash -c "ollama list" """,
            f"""docker run -d \
            --name open-webui \
            --network ollama-network \
            -p 3001:8080 \
            -v {caminho_open_webui}:/app/backend/data \
            -e OLLAMA_BASE_URL=http://ollama:11434 \
            ghcr.io/open-webui/open-webui:main"""
        ]
        
        # Adiciona permissão 777 no caminho persistente do container ollama
        self.gerenciar_permissoes_pasta(caminho_ollama, '777')
        
        self.remove_container(f'open-webui')
        self.remove_container(f'ollama')
        self.executar_comandos(comandos, ignorar_erros=True)
        
        # Instruções de uso no final
        print("\n" + "="*50)
        print("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*50)
        print("\n📋 INSTRUÇÕES DE USO:")
        print("1. Acesse a interface web em: http://seu-ip:3001")
        print("2. Na primeira execução, você precisará criar uma conta de administrador")
        print("3. Conecte ao Ollama no menu 'Connections' usando a URL: http://ollama:11434")
        
        print("\n💡 MODELOS ADICIONAIS:")
        print("Você pode instalar mais modelos diretamente pela interface do Open WebUI ou usando o comando docker abaixo:")
        
        print("\n💡 COMANDOS ÚTEIS:")
        print("- Ver modelos instalados: docker exec ollama bash -c \"ollama list\"")
        print("- Instalar novo modelo:   docker exec ollama bash -c \"ollama pull gemma3:4b\"")
        print("- Reiniciar serviço:      docker restart ollama open-webui")
        
        print("\n⚠️ ATENÇÃO:")
        print("- Para modelos maiores (como llama3), verifique se seu hardware tem recursos suficientes")
    
    def instala_evolution_api_whatsapp(self):
        print("Iniciando instalação Evolution API WhatsApp:")
        
        # Preparar diretórios
        caminho_evolution = f'{self.install_principal}/evolution_api_whatsapp'
        caminho_store = f'{caminho_evolution}/store'
        caminho_instances = f'{caminho_evolution}/instances'
        caminho_env = f'{caminho_evolution}/config'
        
        os.makedirs(caminho_store, exist_ok=True)
        os.makedirs(caminho_instances, exist_ok=True)
        os.makedirs(caminho_env, exist_ok=True)
        os.chmod(caminho_evolution, 0o777)
        
        # Verificar se o arquivo .env já existe ANTES de pedir configurações
        env_file_path = f'{caminho_env}/.env'
        usar_config_existente = False
        
        if os.path.exists(env_file_path):
            print("\n⚠️  ATENÇÃO: Arquivo .env já existe!")
            print(f"Localização: {env_file_path}")
            resposta = input("Deseja usar as configurações existentes? (s/n) [padrão: s]: ").strip().lower()
            if resposta != 'n':
                usar_config_existente = True
                print("✅ Usando arquivo .env existente.")
                print("💡 A instalação continuará com as configurações já salvas.")
            else:
                print("⚠️  As configurações serão solicitadas para sobrescrever o arquivo existente...")
        
        # Só solicita configurações se NÃO estiver usando arquivo existente
        if not usar_config_existente:
            # Gerar chave de autenticação forte automaticamente
            api_key = secrets.token_urlsafe(32)
            print("\n=== CHAVE DE AUTENTICAÇÃO GERADA ===")
            print(f"AUTHENTICATION_API_KEY: {api_key}")
            print("⚠️  Guarde esta chave em local seguro!")
            print("Ela será salva automaticamente no arquivo .env")
            
            # Configurar versão do Telefone
            print("\n=== CONFIGURAÇÃO DA VERSÃO DO TELEFONE ===")
            print("A versão do Telefone determina qual cliente será usado pela API.")
            print("Versões mais recentes podem ter mais recursos, mas versões estáveis são mais confiáveis.")
            yarn_version = input("Digite a versão do Telefone (padrão: 1.22.22): ").strip() or "1.22.22"

            # Configurar versão do WhatsAppWeb (para evitar banimento)
            print("\n=== CONFIGURAÇÃO DA VERSÃO DO WhatsAppWeb ===")
            print("Esta configuração simula uma versão específica do WhatsApp no WhatsAppWeb.")
            print("Ajuda a evitar detecção e possível banimento pela API oficial do WhatsApp.")
            phone_version = input("Digite a versão do WhatsAppWeb (padrão: 2.3000.1028956288): ").strip() or "2.3000.1028956288"

            # Configurar URL do servidor
            print("\n=== CONFIGURAÇÃO DA URL DO SERVIDOR ===")
            print("Esta URL é usada para webhooks e integrações externas.")
            print("Exemplo: http://seu-ip:porta ou https://seu-dominio.com")
            server_url = input("Digite a URL do servidor (opcional, pressione Enter para pular): ").strip()
            
            # Configuração do banco de dados PostgreSQL
            print("\n=== CONFIGURAÇÃO DO BANCO DE DADOS POSTGRESQL ===")
            print("Informe os dados de conexão com o PostgreSQL:")
            
            host_db = input("Host do PostgreSQL (ex: postgres_17, localhost, IP): ").strip()
            porta_db = input("Porta do PostgreSQL (padrão: 5435): ").strip() or "5435"
            nome_banco = input("Nome do banco de dados (padrão: evolution): ").strip() or "evolution"
            usuario_db = input("Nome do usuário do banco (padrão: evolution): ").strip() or "evolution"
            senha_db = input("Senha do usuário: ").strip()
            
            # Validação dos campos obrigatórios
            if not host_db or not nome_banco or not usuario_db or not senha_db:
                print("ERRO: Todos os campos são obrigatórios!")
                return
            
            # Validação de caracteres especiais que podem causar problemas na URI
            
            # Caracteres que precisam ser escapados na URI
            caracteres_problematicos = r'[@:/\?#\[\]!$&\'()*+,;=]'
            
            if re.search(caracteres_problematicos, usuario_db):
                print("⚠️  AVISO: O nome de usuário contém caracteres especiais que serão codificados na URI.")
                usuario_db = quote_plus(usuario_db)
            
            if re.search(caracteres_problematicos, senha_db):
                print("⚠️  AVISO: A senha contém caracteres especiais que serão codificados na URI.")
                senha_db = quote_plus(senha_db)
            
            if re.search(caracteres_problematicos, nome_banco):
                print("⚠️  AVISO: O nome do banco contém caracteres especiais que serão codificados na URI.")
                nome_banco = quote_plus(nome_banco)
            
            # Construir URI de conexão com os dados fornecidos (já codificados se necessário)
            database_uri = f"postgresql://{usuario_db}:{senha_db}@{host_db}:{porta_db}/{nome_banco}?schema=public"
            
            # Criar/sobrescrever o arquivo .env
            with open(env_file_path, 'w') as f:
                f.write(f"AUTHENTICATION_API_KEY={api_key}\n")
                f.write(f"DATABASE_CONNECTION_URI={database_uri}\n")
                f.write(f"YARN_VERSION={yarn_version}\n")
                f.write(f"CONFIG_SESSION_PHONE_VERSION={phone_version}\n")
                if server_url:
                    f.write(f"SERVER_URL={server_url}\n")
            
            # Definir permissões restritas no arquivo .env (apenas owner pode ler)
            os.chmod(env_file_path, 0o600)
            print("✅ Arquivo .env criado com sucesso!")
        
        portas = self.escolher_porta_disponivel()
        
        # Construir o comando docker usando --env-file (credenciais não aparecem em docker inspect)
        container = f"""docker run -d \
                        --name evolution_api_whatsapp \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -p {portas[0]}:8080 \
                        --env-file {env_file_path} \
                        -e TZ="America/Sao_Paulo" \
                        -e DATABASE_ENABLED="true" \
                        -e DATABASE_PROVIDER="postgresql" \
                        -e CACHE_REDIS_ENABLED="false" \
                        -e CACHE_LOCAL_ENABLED="true" \
                        -v {caminho_store}:/evolution/store \
                        -v {caminho_instances}:/evolution/instances \
                        atendai/evolution-api
                    """
        
        self.remove_container('evolution_api_whatsapp')
        resultados = self.executar_comandos([container])
        
        self.cria_rede_docker(associar_container_nome='evolution_api_whatsapp', numero_rede=1)
        
        print("\n" + "="*60)
        print("Instalação do Evolution API WhatsApp concluída.")
        print("="*60)
        print(f"Porta de acesso: {portas[0]}")
        
        # Só exibe detalhes se foram coletados (novo .env criado)
        if not usar_config_existente:
            print(f"API Key: {api_key}")
            print(f"Versão WhatsApp Web: {yarn_version}")
            print(f"Versão do Telefone: {phone_version}")
            if server_url:
                print(f"URL do Servidor: {server_url}")
            print(f"Banco de dados: {host_db}:{porta_db}/{nome_banco}")
        else:
            print("📋 Configurações: Usando arquivo .env existente")
            print(f"   (Verifique o arquivo para detalhes: {env_file_path})")
        
        print(f"Cache: Local (Redis desabilitado)")
        print(f"Diretório store: {caminho_store}")
        print(f"Diretório instances: {caminho_instances}")
        print(f"\nARQUIVO DE CONFIGURAÇÃO (.env):")
        print(f"  Localização: {env_file_path}")
        print(f"  Permissões: 600 (apenas owner pode ler)")
        print(f"  Contém: API_KEY, DATABASE_URI, YARN_VERSION, PHONE_VERSION, SERVER_URL (opcional)")
        print("\nIPs possíveis para acesso:")
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f"\nAcesse: http://<seu_ip>:{portas[0]}")
        print("="*60)
            
    def instala_waha_whatsapp(self):
        print("Iniciando instalação WAHA WhatsApp HTTP API (devlikeapro/waha):")

        caminho_waha = f'{self.install_principal}/waha_whatsapp'
        caminho_sessions = f'{caminho_waha}/sessions'
        caminho_media = f'{caminho_waha}/media'
        caminho_env = f'{caminho_waha}/config'

        portas = self.escolher_porta_disponivel()

        os.makedirs(caminho_waha, exist_ok=True)
        os.makedirs(caminho_sessions, exist_ok=True)
        os.makedirs(caminho_media, exist_ok=True)
        os.makedirs(caminho_env, exist_ok=True)
        os.chmod(caminho_waha, 0o777)

        env_file_path = f'{caminho_env}/.env'
        usar_config_existente = False

        if os.path.exists(env_file_path):
            print("\n⚠  ATENÇÃO: Arquivo .env já existe para o WAHA!")
            print(f"Localização: {env_file_path}")
            resposta = input("Deseja usar as configurações existentes? (s/n) [padrão: s]: ").strip().lower()
            if resposta != 'n':
                usar_config_existente = True
                print("✅ Usando arquivo .env existente.")
            else:
                print("As novas configurações serão solicitadas e sobrescreverão o arquivo.")

        api_key = dashboard_user = dashboard_password = None
        swagger_user = swagger_password = None
        base_url = engine_padrao = None
        dashboard_enabled = swagger_enabled = None

        if not usar_config_existente:
            api_key = secrets.token_hex(16)
            print("\n=== CHAVE DE AUTENTICAÇÃO GERADA ===")
            print(f"WAHA_API_KEY: {api_key}")
            print("Anote esta chave, ela será necessária para proteger as chamadas API.")

            dashboard_user = input("\nUsuário do dashboard (padrão: admin): ").strip() or "admin"
            dashboard_password = input("Senha do dashboard (Enter para gerar automaticamente): ").strip()
            if not dashboard_password:
                dashboard_password = secrets.token_urlsafe(16)
                print(f"Senha do dashboard gerada: {dashboard_password}")

            swagger_user = input("\nUsuário do Swagger (padrão: admin): ").strip() or "admin"
            swagger_password = input("Senha do Swagger (Enter para gerar automaticamente): ").strip()
            if not swagger_password:
                swagger_password = secrets.token_urlsafe(16)
                print(f"Senha do Swagger gerada: {swagger_password}")

            base_url_padrao = f"http://localhost:{portas[0]}"
            base_url = input(f"\nBase URL pública da API (padrão: {base_url_padrao}): ").strip() or base_url_padrao

            engine_padrao = input("\nEngine padrão do WhatsApp (WEBJS/GOWS/NOWEB) [WEBJS]: ").strip().upper() or "WEBJS"

            dash_enabled_input = input("Deseja habilitar o dashboard web? (s/n) [s]: ").strip().lower()
            dashboard_enabled = "False" if dash_enabled_input == 'n' else "True"

            swagger_enabled_input = input("Deseja habilitar o Swagger? (s/n) [s]: ").strip().lower()
            swagger_enabled = "False" if swagger_enabled_input == 'n' else "True"

            with open(env_file_path, 'w') as f:
                f.write(f"WAHA_API_KEY={api_key}\n")
                f.write(f"WAHA_DASHBOARD_USERNAME={dashboard_user}\n")
                f.write(f"WAHA_DASHBOARD_PASSWORD={dashboard_password}\n")
                f.write(f"WHATSAPP_SWAGGER_USERNAME={swagger_user}\n")
                f.write(f"WHATSAPP_SWAGGER_PASSWORD={swagger_password}\n")
                f.write(f"WAHA_DASHBOARD_ENABLED={dashboard_enabled}\n")
                f.write(f"WHATSAPP_SWAGGER_ENABLED={swagger_enabled}\n")
                f.write(f"WAHA_BASE_URL={base_url}\n")
                f.write(f"WHATSAPP_DEFAULT_ENGINE={engine_padrao}\n")
                f.write("WAHA_MEDIA_STORAGE=LOCAL\n")
                f.write("WHATSAPP_FILES_FOLDER=/app/.media\n")
                f.write("WHATSAPP_FILES_LIFETIME=0\n")
                f.write("WAHA_LOG_FORMAT=JSON\n")
                f.write("WAHA_LOG_LEVEL=info\n")
                f.write("WAHA_PRINT_QR=False\n")

            os.chmod(env_file_path, 0o600)
            print("✅ Arquivo .env criado com sucesso!")

        container = f"""docker run -d \
                        --name waha_whatsapp \
                        --restart=unless-stopped \
                        --memory=512m \
                        --cpus=1 \
                        -p {portas[0]}:3000 \
                        --env-file {env_file_path} \
                        -e TZ="America/Sao_Paulo" \
                        -v {caminho_sessions}:/app/.sessions \
                        -v {caminho_media}:/app/.media \
                        devlikeapro/waha
                    """

        self.remove_container('waha_whatsapp')
        resultados = self.executar_comandos([container])

        self.cria_rede_docker(associar_container_nome='waha_whatsapp', numero_rede=1)

        print("\n" + "="*60)
        print("Instalação do WAHA WhatsApp concluída.")
        print("="*60)
        print(f"Porta de acesso: {portas[0]}")

        if not usar_config_existente:
            print(f"API Key: {api_key}")
            print(f"Usuário Dashboard: {dashboard_user}")
            print(f"Senha Dashboard: {dashboard_password}")
            print(f"Usuário Swagger: {swagger_user}")
            print(f"Senha Swagger: {swagger_password}")
            print(f"Base URL configurada: {base_url}")
            print(f"Engine padrão: {engine_padrao}")
            print(f"Dashboard habilitado: {dashboard_enabled}")
            print(f"Swagger habilitado: {swagger_enabled}")
        else:
            print("Usando configurações existentes do arquivo .env.")
            print(f"Consulte: {env_file_path}")

        print(f"Diretório Sessions: {caminho_sessions}")
        print(f"Diretório Media: {caminho_media}")
        print("\nArquivo .env")
        print(f"  Localização: {env_file_path}")
        print(f"  Permissões: 600 (somente proprietário)")

        print("\nIPs disponíveis para acesso:")
        comandos = [
            "hostname -I | tr ' ' '\\n'",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f"\nDashboard: http://<seu_ip>:{portas[0]}/dashboard")
        print(f"Swagger:   http://<seu_ip>:{portas[0]}/swagger")
        print("="*60)
            
    def instala_redis_docker(self):
        print("Iniciando instalação redis:")
        senha = input("Configure uma senha para acessar: ")
        container = f"""docker run -d \
                        --name redis \
                        --restart=unless-stopped \
                        --memory=256m \
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
        print("info memory")
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
    
    def instala_browserless(self):
        print("Iniciando instalacao do Browserless (Chromium headless).")

        base_dir = f"{self.install_principal}/browserless"

        porta = self.escolher_porta_disponivel()[0]
        max_sessions = "2"
        timeout_ms = "15000"
        token_input = input("TOKEN de acesso (Enter gera automaticamente): ").strip()
        token = token_input or self.generate_password(24)
        if not token_input:
            print(f"TOKEN gerado automaticamente: {token}")

        self.remove_container("browserless_central")

        compose_yml = textwrap.dedent(f"""
        version: '3'
        services:
          browserless:
            image: ghcr.io/browserless/chromium:latest
            container_name: browserless_central
            restart: always
            ports:
              - "{porta}:3000"
            environment:
              - MAX_CONCURRENT_SESSIONS={max_sessions}
              - TOKEN={token}
              - CONNECTION_TIMEOUT={timeout_ms}
            deploy:
              resources:
                limits:
                  cpus: "1"
                  memory: "512m"
            shm_size: "512m"
        """).strip() + "\n"

        self.aplicar_compose(compose_yml=compose_yml)

        print("\nBrowserless disponivel.")
        print(f"- URL: http://<ip-servidor>:{porta}")
        print("- Use o TOKEN configurado para autenticar as requisicoes.")

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
    
    def mostrar_menu_paginado(self, opcoes_menu, titulo="Menu de Opções", itens_por_pagina=15, principal=False):
        """Mostra menu com paginação, busca e navegação melhorada."""
        opcoes_menu.insert(0, ("Sair", self.sair))
        
        pagina_atual = 0
        filtro = ""
        
        while True:
            # Limpa a tela usando ANSI escape codes
            # \033[2J = limpa tela | \033[H = move cursor para topo
            # Mantém histórico no buffer (pode scrollar para cima)
            print("\033[2J\033[H", end='')
            
            # Aplica filtro se houver
            if filtro:
                opcoes_filtradas = [
                    (idx, opcao) for idx, opcao in enumerate(opcoes_menu)
                    if filtro.lower() in opcao[0].lower()
                ]
            else:
                opcoes_filtradas = list(enumerate(opcoes_menu))
            
            total_opcoes = len(opcoes_filtradas)
            total_paginas = (total_opcoes + itens_por_pagina - 1) // itens_por_pagina
            
            # Ajusta página se exceder o limite
            if pagina_atual >= total_paginas:
                pagina_atual = max(0, total_paginas - 1)
            
            inicio = pagina_atual * itens_por_pagina
            fim = min(inicio + itens_por_pagina, total_opcoes)
            opcoes_pagina = opcoes_filtradas[inicio:fim]
            
            # Exibe cabeçalho com cores ANSI
            # \033[1m = negrito | \033[36m = ciano | \033[0m = reset
            print("\033[1;36m" + "="*80 + "\033[0m")
            print(f"\033[1;37m  {titulo}\033[0m")
            if filtro:
                print(f"\033[33m  🔍 Filtro: '{filtro}' | {total_opcoes} resultado(s)\033[0m")
            print(f"\033[90m  📄 Página {pagina_atual + 1}/{total_paginas} | Exibindo {inicio + 1}-{fim} de {total_opcoes}\033[0m")
            print("\033[1;36m" + "="*80 + "\033[0m")
            
            # Exibe opções da página
            for idx_original, (texto, funcao) in opcoes_pagina:
                if idx_original == 0:
                    # Opção "Sair" em vermelho
                    print(f"\033[91m  [{idx_original}] {texto}\033[0m")
                else:
                    # Opções normais em branco/verde claro
                    print(f"\033[92m  [{idx_original}]\033[0m {texto}")
            
            # Exibe rodapé com comandos
            print("\n" + "\033[2m" + "-"*80 + "\033[0m")
            print("\033[96m  NAVEGAÇÃO:\033[0m [n]ext | [p]rev | [número] para selecionar")
            print("\033[96m  BUSCA:\033[0m /palavra | [c]limpar filtro | [0] Sair")
            print("\033[2m" + "-"*80 + "\033[0m")
            
            escolha = input("\n\033[1;33m➤ Digite sua escolha:\033[0m ").strip()
            
            # Comandos especiais
            if escolha.lower() == 'n' or escolha.lower() == 'next':
                if pagina_atual < total_paginas - 1:
                    pagina_atual += 1
                else:
                    print("\n\033[93m⚠️  Você já está na última página!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")
                continue
            
            elif escolha.lower() == 'p' or escolha.lower() == 'prev':
                if pagina_atual > 0:
                    pagina_atual -= 1
                else:
                    print("\n\033[93m⚠️  Você já está na primeira página!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")
                continue
            
            elif escolha.startswith('/'):
                # Busca/filtro
                filtro = escolha[1:].strip()
                pagina_atual = 0
                continue
            
            elif escolha.lower() == 'c' or escolha.lower() == 'clear':
                # Limpa filtro
                filtro = ""
                pagina_atual = 0
                continue
            
            # Seleção numérica
            try:
                escolha_num = int(escolha)
                
                # Verifica se é uma opção válida
                opcao_selecionada = None
                for idx_original, (texto, funcao) in opcoes_filtradas:
                    if idx_original == escolha_num:
                        opcao_selecionada = (texto, funcao)
                        break
                
                if opcao_selecionada:
                    print("\033[2J\033[H", end='')
                    print(f"\033[1;32m{'='*80}\033[0m")
                    print(f"\033[1;32m  ✓ Executando: {opcao_selecionada[0]}\033[0m")
                    print(f"\033[1;32m{'='*80}\033[0m\n")
                    opcao_selecionada[1]()
                    
                    if principal:
                        break
                    else:
                        return
                else:
                    print(f"\n\033[91m❌ Opção [{escolha_num}] não encontrada!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")
                    
            except ValueError:
                print("\n\033[91m❌ Entrada inválida! Use um número, 'n', 'p', '/busca' ou 'c'\033[0m")
                input("\033[90mPressione Enter para continuar...\033[0m")
        
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
            
            encontrado = False
            for linha in fstab_lines:
                if '/swap.img' in linha:
                    print("A linha de swap já existe em /etc/fstab.")
                    encontrado = True
                    break
            
            if not encontrado:
                with open('/etc/fstab', 'a') as f:
                    swap_fstab_line = '/swap.img       none    swap    sw      0       0\n' #
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
        """Menu de opções"""
        opcoes_menu = [
            ("Exibe o estado atual da raid", self.estado_raid),
            ("Formata o disco para usar em raid existente", self.formatar_criar_particao_raid),
            ("Controle de tamanho do raid", self.gerenciar_raid),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="💾 GERENCIAMENTO DE RAID", itens_por_pagina=10)
        
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
        """Menu de opções"""
        opcoes_menu = [
            ("Menu RAID", self.menu_raid),
            ("Listar particoes", self.listar_particoes),
            ("Listar particoes detalhadas", self.listar_particoes_detalhadas),
            ("Monta particao", self.monta_particao),
            ("Desmontar particao", self.desmontar_particao),
            ("Formata o disco e cria partição e monta", self.formata_cria_particao),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="💿 GERENCIAMENTO DE PARTIÇÕES", itens_por_pagina=10)
    
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
        
    def configurar_ssh(self):
        """
        Menu interativo de configuração SSH:
        1) Alterar porta do serviço
        2) Alterar senha de todos os usuários com shell
        3) Gerar / atualizar chave ED25519 para root
        4) Desabilitar login por senha (somente chave)
        0) Sair
        Executa as opções escolhidas em sequência.
        """

        # ──────────────────────────────────────────────────────────
        # utilitário interno para rodar comandos
        # ──────────────────────────────────────────────────────────
        def run(cmd: str, *, shell=False):
            print(f"$ {cmd}")
            subprocess.run(
                cmd if shell else shlex.split(cmd),
                shell=shell,
                check=True,
                executable="/bin/bash" if shell else None,
            )

        # ──────────────────────────────────────────────────────────
        # MENU PRINCIPAL
        # ──────────────────────────────────────────────────────────
        opcoes = {
            "1": "Alterar porta SSH",
            "2": "Alterar senha dos usuários",
            "3": "Gerar/atualizar chave para root",
            "4": "Desabilitar login por senha",
            "5": "Habilitar login por senha (reverte opção 4)",
            "0": "Sair",
        }

        print("\n==== CONFIGURADOR DE SSH ====")
        for k, v in opcoes.items():
            print(f"[{k}] {v}")

        escolhas = input(
            "\nDigite os números das opções desejadas (ex.: 1,3 para 1 e 3): "
        ).strip()

        # ──────────────────────────────────────────────────────────
        # 1) Alterar porta SSH
        # ──────────────────────────────────────────────────────────
        if "1" in escolhas:
            try:
                porta = int(input("Nova porta SSH: "))
                run(f"sudo sed -i 's/^#\\?Port .*/Port {porta}/' /etc/ssh/sshd_config")
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print(f"✅ Porta alterada para {porta}\n")
            except ValueError:
                print("❌ Porta inválida. Pulando.\n")

        # ──────────────────────────────────────────────────────────
        # 2) Alterar senha de todos os usuários com shell
        # ──────────────────────────────────────────────────────────
        if "2" in escolhas:
            nova_senha = input("Digite a nova senha para os usuários: ")
            try:
                lista = subprocess.check_output(
                    "awk -F: '($7 ~ /(\\/bin\\/bash|\\/bin\\/sh|\\/bin\\/dash)$/){print $1}' /etc/passwd",
                    shell=True,
                    text=True,
                )
                usuarios = [u for u in lista.splitlines() if u]
            except subprocess.CalledProcessError:
                usuarios = []

            for u in usuarios:
                try:
                    print(f"Alterando senha de {u}...")
                    subprocess.run(
                        ["sudo", "passwd", u],
                        input=f"{nova_senha}\n{nova_senha}",
                        text=True,
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    print(f"⚠️  Falhou ao alterar senha de {u}")
            print("✅ Senhas atualizadas.\n")

        # ──────────────────────────────────────────────────────────
        # 3) Gerar / atualizar chave ED25519 para root (login root só por chave)
        # ──────────────────────────────────────────────────────────
        if "3" in escolhas:
            key_dir = Path("/install_principal/ssh")
            key_dir.mkdir(parents=True, exist_ok=True)
            key_dir.chmod(0o700)

            default_key = key_dir / "id_ed25519"
            key_path = default_key          # valor default se for a 1ª vez
            escolha  = "s"                  # assume “substituir” quando não existe

            if default_key.exists():
                escolha = input(
                    "Chave existente encontrada.\n"
                    "[S] Substituir | [A] Adicionar nova | [C] Cancelar: "
                ).strip().lower()

                if escolha == "c":
                    print("Operação cancelada.\n")
                    key_path = None          # nada a fazer
                elif escolha == "a":
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    key_path = key_dir / f"id_ed25519_{ts}"
                else:  # 's'
                    key_path = default_key
                    run(f"rm -f {key_path} {key_path}.pub")     # remove par antigo

            # Se foi escolhido gerar (substituir ou adicionar)
            if key_path:
                proteger = input("Proteger com passphrase? [s/n] ").lower().startswith("s")
                passphrase = input("Passphrase: ") if proteger else ""

                # 1) Gera o par ED25519
                passphrase_esc = shlex.quote(passphrase) # vira '' se vazia
                run(
                    f"ssh-keygen -t ed25519 -a 100 -f {key_path} "
                    f"-N {passphrase_esc}"
                )

                # 2) Autoriza a chave pública para o root
                run("mkdir -p /root/.ssh")
                run("chmod 700 /root/.ssh")
                run(f"cat {key_path}.pub >> /root/.ssh/authorized_keys", shell=True)
                run("chmod 600 /root/.ssh/authorized_keys")

                # 3) Garante que:
                #    • PubkeyAuthentication esteja ativo
                run(
                    "(grep -q '^PubkeyAuthentication' /etc/ssh/sshd_config) || "
                    "echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config",
                    shell=True,
                )
                # 4) Garante que:
                #    • root só possa logar por chave (senha bloqueada)
                run(
                    "(grep -q '^PermitRootLogin' /etc/ssh/sshd_config && "
                    " sed -i 's/^PermitRootLogin.*/PermitRootLogin prohibit-password/' "
                    "/etc/ssh/sshd_config) || "
                    "echo 'PermitRootLogin prohibit-password' >> /etc/ssh/sshd_config",
                    shell=True,
                )

                # 5) Reinicia o serviço para aplicar tudo
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)

                print(f"✅ Chave criada/atualizada e root liberado somente por chave: {key_path}\n")

        # ──────────────────────────────────────────────────────────
        # 4) Desabilitar login por senha
        # ──────────────────────────────────────────────────────────
        if "4" in escolhas:
            print(
                "\n⚠️  AVISO IMPORTANTE:\n"
                "Desativar PasswordAuthentication bloqueará qualquer usuário sem chave SSH configurada.\n"
                "Abra outro terminal e confirme que consegue se conectar via chave ANTES de prosseguir."
            )
            if input("Já testou e quer continuar? [digite CONFIRMAR]: ") == "CONFIRMAR":
                # 1) Isso percorre o arquivo principal e todos os .conf incluídos, eliminando qualquer “yes”.
                run(
                    r"for f in /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf; do "
                    r"  sudo sed -i "
                    r"  -e 's/^[ #]*PasswordAuthentication.*/PasswordAuthentication no/' "
                    r"  -e 's/^[ #]*KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' "
                    r"  -e 's/^[ #]*ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/' "
                    r"  $f ; "
                    r"done",
                    shell=True,
                )
                # 2) Reinicia o serviço SSH para aplicar
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print("✅ Login por senha desabilitado.\n")
            else:
                print("Operação abortada.\n")
        # ──────────────────────────────────────────────────────────
        # 5) Habilitar login por senha (reverte opção 4)
        # ──────────────────────────────────────────────────────────
        if "5" in escolhas:
            print(
                "\n⚠️  AVISO IMPORTANTE:\n"
                "Habilitar PasswordAuthentication permitirá login por senha novamente.\n"
            )
            if input("Podemo continuar? [digite CONFIRMAR]: ") == "CONFIRMAR":
                # 1) Isso percorre o arquivo principal e todos os .conf incluídos, eliminando qualquer “no”.
                run(
                    r"for f in /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf; do "
                    r"  sudo sed -i "
                    r"  -e 's/^[ #]*PasswordAuthentication.*/PasswordAuthentication yes/' "
                    r"  -e 's/^[ #]*KbdInteractiveAuthentication.*/KbdInteractiveAuthentication yes/' "
                    r"  -e 's/^[ #]*ChallengeResponseAuthentication.*/ChallengeResponseAuthentication yes/' "
                    r"  $f ; "
                    r"done",
                    shell=True,
                )
                # 2) Reinicia o serviço SSH para aplicar
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print("✅ Login por senha habilitado.\n")
            else:
                print("Operação abortada.\n")

        print("==== Configurações concluídas ====")
        
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
    
    def instalar_wireguard(self):
        """Instala o WireGuard no sistema"""
        print("\n=== INSTALAÇÃO DO WIREGUARD ===\n")
        
        if self.verificar_instalacao("wireguard"):
            print("✅ WireGuard já está instalado.")
            return
        
        print("📦 Instalando WireGuard...")
        comandos = [
            "sudo apt update",
            "sudo apt install -y wireguard wireguard-tools"
        ]
        self.executar_comandos(comandos, comando_direto=True)
        print("\n✅ WireGuard instalado com sucesso!")
    
    def gerar_chaves_wireguard(self):
        """Gera par de chaves pública/privada para WireGuard"""
        print("\n=== GERAR CHAVES WIREGUARD ===\n")
        
        max_tentativas = 3
        
        # Solicitar nome para identificar as chaves
        for tentativa in range(1, max_tentativas + 1):
            nome = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome para identificar as chaves (ex: servidor, worker1): ").strip()
            if nome:
                break
            print(f"❌ Nome não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Operação cancelada.")
                return
        
        # Diretório para armazenar as chaves
        chaves_dir = Path(f"{self.install_principal}/wireguard/chaves/{nome}")
        chaves_dir.mkdir(parents=True, exist_ok=True)
        
        private_key_file = chaves_dir / "private.key"
        public_key_file = chaves_dir / "public.key"
        
        print(f"\n📝 Gerando chaves para '{nome}'...")
        
        try:
            # Gerar chave privada
            result_private = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True
            )
            private_key = result_private.stdout.strip()
            
            # Gerar chave pública a partir da privada
            result_public = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            )
            public_key = result_public.stdout.strip()
            
            # Salvar chaves
            private_key_file.write_text(private_key)
            public_key_file.write_text(public_key)
            
            # Ajustar permissões
            os.chmod(private_key_file, 0o600)
            os.chmod(public_key_file, 0o644)
            
            print("\n" + "="*60)
            print("✅ CHAVES GERADAS COM SUCESSO!")
            print("="*60)
            print(f"📁 Localização: {chaves_dir}")
            print(f"\n🔐 Chave Privada:")
            print(f"   {private_key}")
            print(f"\n🔓 Chave Pública:")
            print(f"   {public_key}")
            print("="*60)
            print("\n⚠️  IMPORTANTE: Guarde a chave privada com segurança!")
            
        except Exception as e:
            print(f"❌ Erro ao gerar chaves: {e}")
    
    def configurar_servidor_wireguard(self):
        """Configura WireGuard como servidor"""
        print("\n=== CONFIGURAR WIREGUARD COMO SERVIDOR ===\n")
        
        max_tentativas = 3
        
        # Coletar informações
        print("📝 Configuração do servidor WireGuard\n")
        
        # IP do servidor na VPN
        for tentativa in range(1, max_tentativas + 1):
            ip_servidor = input(f"[{tentativa}/{max_tentativas}] IP do servidor na VPN (ex: 10.8.0.1/24): ").strip()
            if ip_servidor:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Porta
        for tentativa in range(1, max_tentativas + 1):
            porta = input(f"[{tentativa}/{max_tentativas}] Porta (padrão 51820): ").strip() or "51820"
            try:
                int(porta)
                break
            except ValueError:
                print(f"❌ Porta inválida. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    porta = "51820"
        
        # Chave privada do servidor
        print(f"\n🔑 Chaves disponíveis em {self.install_principal}/wireguard/chaves/")
        subprocess.run(["ls", "-la", f"{self.install_principal}/wireguard/chaves/"], check=False)
        
        for tentativa in range(1, max_tentativas + 1):
            chave_privada = input(f"\n[{tentativa}/{max_tentativas}] Cole a chave PRIVADA do servidor: ").strip()
            if chave_privada:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Criar arquivo de configuração
        config_path = Path("/etc/wireguard/wg0.conf")
        config_content = f"""[Interface]
Address = {ip_servidor}
PrivateKey = {chave_privada}
ListenPort = {porta}

# Adicione peers abaixo usando a opção 'Adicionar peer'

# Exemplo de peer:
# [Peer]
# PublicKey = <chave_publica_do_peer>
# AllowedIPs = <ip_peer_na_vpn>
# Endpoint = <ip_publico_servidor>:51820
# PersistentKeepalive = 25
"""
        
        try:
            config_path.write_text(config_content)
            os.chmod(config_path, 0o600)
            
            print("\n✅ Configuração do servidor criada com sucesso!")
            print(f"📁 Arquivo: {config_path}")
            print("\n⚠️  Próximos passos:")
            print("   1. Adicione peers usando a opção 'Adicionar peer'")
            print("   2. Inicie o serviço WireGuard")
            
        except Exception as e:
            print(f"❌ Erro ao criar configuração: {e}")
    
    def configurar_cliente_wireguard(self):
        """Configura WireGuard como cliente/worker"""
        print("\n=== CONFIGURAR WIREGUARD COMO CLIENTE/WORKER ===\n")
        
        max_tentativas = 3
        
        # Coletar informações
        print("📝 Configuração do cliente WireGuard\n")
        
        # IP do cliente na VPN
        for tentativa in range(1, max_tentativas + 1):
            ip_cliente = input(f"[{tentativa}/{max_tentativas}] IP do cliente na VPN (ex: 10.8.0.2/24): ").strip()
            if ip_cliente:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Chave privada do cliente
        for tentativa in range(1, max_tentativas + 1):
            chave_privada_cliente = input(f"\n[{tentativa}/{max_tentativas}] Cole a chave PRIVADA do cliente: ").strip()
            if chave_privada_cliente:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Chave pública do servidor
        for tentativa in range(1, max_tentativas + 1):
            chave_publica_servidor = input(f"[{tentativa}/{max_tentativas}] Cole a chave PÚBLICA do servidor: ").strip()
            if chave_publica_servidor:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Endpoint do servidor
        for tentativa in range(1, max_tentativas + 1):
            endpoint = input(f"[{tentativa}/{max_tentativas}] IP público do servidor (ex: 1.2.3.4): ").strip()
            if endpoint:
                break
            print(f"❌ Endpoint não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Porta do servidor
        for tentativa in range(1, max_tentativas + 1):
            porta_servidor = input(f"[{tentativa}/{max_tentativas}] Porta do servidor (padrão 51820): ").strip() or "51820"
            try:
                int(porta_servidor)
                break
            except ValueError:
                print(f"❌ Porta inválida. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    porta_servidor = "51820"
        
        # AllowedIPs
        allowed_ips = input("IPs permitidos (padrão 10.8.0.0/24): ").strip() or "10.8.0.0/24"
        
        # Criar arquivo de configuração
        config_path = Path("/etc/wireguard/wg0.conf")
        config_content = f"""[Interface]
Address = {ip_cliente}
PrivateKey = {chave_privada_cliente}

[Peer]
PublicKey = {chave_publica_servidor}
Endpoint = {endpoint}:{porta_servidor}
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""
        
        try:
            config_path.write_text(config_content)
            os.chmod(config_path, 0o600)
            
            print("\n✅ Configuração do cliente criada com sucesso!")
            print(f"📁 Arquivo: {config_path}")
            print("\n⚠️  Próximo passo:")
            print("   Inicie o serviço WireGuard")
            
        except Exception as e:
            print(f"❌ Erro ao criar configuração: {e}")
    
    def adicionar_peer_wireguard(self):
        """Adiciona um peer ao servidor WireGuard"""
        print("\n=== ADICIONAR PEER AO SERVIDOR WIREGUARD ===\n")
        
        config_path = Path("/etc/wireguard/wg0.conf")
        
        if not config_path.exists():
            print("❌ Arquivo de configuração não encontrado!")
            print("   Configure o servidor primeiro usando a opção 'Configurar como servidor'")
            return
        
        max_tentativas = 3
        
        # Nome do peer
        for tentativa in range(1, max_tentativas + 1):
            nome_peer = input(f"[{tentativa}/{max_tentativas}] Nome do peer (ex: worker1): ").strip()
            if nome_peer:
                break
            print(f"❌ Nome não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Chave pública do peer
        for tentativa in range(1, max_tentativas + 1):
            chave_publica_peer = input(f"[{tentativa}/{max_tentativas}] Cole a chave PÚBLICA do peer: ").strip()
            if chave_publica_peer:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # IP do peer
        for tentativa in range(1, max_tentativas + 1):
            ip_peer = input(f"[{tentativa}/{max_tentativas}] IP do peer na VPN (ex: 10.8.0.2/32): ").strip()
            if ip_peer:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return
        
        # Adicionar peer ao arquivo
        peer_config = f"""
[Peer]
# {nome_peer}
PublicKey = {chave_publica_peer}
AllowedIPs = {ip_peer}
"""
        
        try:
            with open(config_path, 'a') as f:
                f.write(peer_config)
            
            print(f"\n✅ Peer '{nome_peer}' adicionado com sucesso!")
            print("\n⚠️  Reinicie o serviço WireGuard para aplicar:")
            print("   sudo systemctl restart wg-quick@wg0")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar peer: {e}")
    
    def iniciar_wireguard(self):
        """Inicia e habilita o serviço WireGuard"""
        print("\n=== INICIAR WIREGUARD ===\n")
        
        try:
            print("🚀 Habilitando WireGuard para iniciar com o sistema...")
            subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
            
            print("🚀 Iniciando WireGuard...")
            subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
            
            print("\n✅ WireGuard iniciado com sucesso!")
            print("\n📊 Status:")
            subprocess.run(["sudo", "wg", "show"], check=False)
            
        except Exception as e:
            print(f"❌ Erro ao iniciar WireGuard: {e}")
    
    def parar_wireguard(self):
        """Para o serviço WireGuard"""
        print("\n=== PARAR WIREGUARD ===\n")
        
        try:
            print("🛑 Parando WireGuard...")
            subprocess.run(["sudo", "systemctl", "stop", "wg-quick@wg0"], check=True)
            print("✅ WireGuard parado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao parar WireGuard: {e}")
    
    def status_wireguard(self):
        """Mostra o status do WireGuard"""
        print("\n=== STATUS WIREGUARD ===\n")
        
        try:
            print("📊 Status do serviço:")
            subprocess.run(["sudo", "systemctl", "status", "wg-quick@wg0"], check=False)
            
            print("\n" + "="*60)
            print("📊 Conexões ativas:")
            subprocess.run(["sudo", "wg", "show"], check=False)
            
        except Exception as e:
            print(f"❌ Erro ao verificar status: {e}")
    
    def testar_conexao_wireguard(self):
        """Testa a conexão WireGuard"""
        print("\n=== TESTAR CONEXÃO WIREGUARD ===\n")
        
        ip_teste = input("Digite o IP do peer para testar (ex: 10.8.0.1): ").strip()
        
        if not ip_teste:
            print("❌ IP não pode ser vazio.")
            return
        
        print(f"\n🔍 Testando conectividade com {ip_teste}...")
        subprocess.run(["ping", "-c", "4", ip_teste], check=False)
    
    def visualizar_config_wireguard(self):
        """Visualiza a configuração atual do WireGuard"""
        print("\n=== CONFIGURAÇÃO WIREGUARD ===\n")
        
        config_path = Path("/etc/wireguard/wg0.conf")
        
        if not config_path.exists():
            print("❌ Arquivo de configuração não encontrado!")
            return
        
        try:
            config_content = config_path.read_text()
            print(config_content)
        except Exception as e:
            print(f"❌ Erro ao ler configuração: {e}")
    
    def configurar_wireguard_dinamico(self):
        """Configuração dinâmica e inteligente do WireGuard"""
        print("\n" + "="*70)
        print("🔐 ASSISTENTE DE CONFIGURAÇÃO WIREGUARD VPN")
        print("="*70)
        
        # 1. Auto-instalar WireGuard se necessário
        if not self.verificar_instalacao("wireguard"):
            print("\n📦 WireGuard não encontrado. Instalando automaticamente...")
            comandos = [
                "sudo apt update",
                "sudo apt install -y wireguard wireguard-tools"
            ]
            try:
                self.executar_comandos(comandos, comando_direto=True)
                print("✅ WireGuard instalado!\n")
            except Exception as e:
                print(f"❌ Erro ao instalar WireGuard: {e}")
                return
        else:
            print("✅ WireGuard já está instalado\n")
        
        # 2. Verificar se já existe configuração
        config_path = Path("/etc/wireguard/wg0.conf")
        config_existente = config_path.exists()
        
        if config_existente:
            print("⚠️  ATENÇÃO: Já existe uma configuração WireGuard!")
            print(f"📁 Localização: {config_path}")
            
            # Mostra a configuração completa
            try:
                config_content = config_path.read_text()
                print("\n" + "="*70)
                print("📄 CONFIGURAÇÃO ATUAL:")
                print("="*70)
                print(config_content)
                print("="*70)
            except Exception as e:
                print(f"⚠️  Não foi possível ler a configuração: {e}")
            
            # Verifica status do serviço
            print("\n📊 Status do serviço:")
            subprocess.run(["sudo", "systemctl", "status", "wg-quick@wg0", "--no-pager"], check=False)
            
            print("\n" + "="*70)
            print("OPÇÕES:")
            print("[1] Manter configuração e apenas visualizar/gerenciar")
            print("[2] RESETAR e criar nova configuração")
            print("[0] Voltar ao menu")
            print("="*70)
            
            opcao = input("\nEscolha: ").strip()
            
            if opcao == "0":
                return
            elif opcao == "1":
                # Menu de gerenciamento da configuração existente
                print("\n✅ Mantendo configuração existente.")
                
                # Tenta extrair e mostrar a chave pública
                chaves_dir = Path(f"{self.install_principal}/wireguard/chaves")
                public_key_file = chaves_dir / "public.key"
                
                if public_key_file.exists():
                    public_key = public_key_file.read_text().strip()
                    print("\n" + "="*70)
                    print("📋 SUAS INFORMAÇÕES PARA COMPARTILHAR:")
                    print("="*70)
                    print(f"🔓 Chave Pública: {public_key}")
                    
                    # Tenta extrair IP da config
                    try:
                        import re
                        match = re.search(r'Address\s*=\s*(\S+)', config_content)
                        if match:
                            print(f"📍 IP na VPN: {match.group(1)}")
                    except:
                        pass
                    print("="*70)
                
                # Verifica se está rodando, se não, oferece iniciar
                result = subprocess.run(
                    ["sudo", "systemctl", "is-active", "wg-quick@wg0"],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout.strip() != "active":
                    if input("\n⚠️  WireGuard não está ativo. Deseja iniciar? [S/n]: ").strip().lower() != 'n':
                        subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
                        subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
                        print("✅ WireGuard iniciado!")
                        subprocess.run(["sudo", "wg", "show"], check=False)
                else:
                    print("\n✅ WireGuard está ativo!")
                    subprocess.run(["sudo", "wg", "show"], check=False)
                
                # Menu de ações adicionais
                print("\n" + "="*70)
                print("O QUE DESEJA FAZER?")
                print("="*70)
                print("[1] ➕ Adicionar novo peer (para servidores)")
                print("[2] 📊 Ver status detalhado")
                print("[3] 🔍 Testar conexão com peer")
                print("[0] Voltar ao menu principal")
                print("="*70)
                
                acao = input("\nEscolha: ").strip()
                
                if acao == "1":
                    # Adicionar peer
                    self._adicionar_peer_dinamico()
                elif acao == "2":
                    # Status detalhado
                    print("\n📊 STATUS DETALHADO:")
                    subprocess.run(["sudo", "systemctl", "status", "wg-quick@wg0", "--no-pager"], check=False)
                    print("\n🔗 CONEXÕES:")
                    subprocess.run(["sudo", "wg", "show"], check=False)
                elif acao == "3":
                    # Testar conexão
                    ip_teste = input("\nDigite o IP do peer para testar (ex: 10.8.0.2): ").strip()
                    if ip_teste:
                        print(f"\n🔍 Testando conectividade com {ip_teste}...")
                        subprocess.run(["ping", "-c", "4", ip_teste], check=False)
                
                return
                
                return
            elif opcao == "2":
                print("🔄 A configuração será resetada...")
                # Backup da config antiga
                backup_path = config_path.with_suffix('.conf.backup')
                try:
                    import shutil
                    shutil.copy(config_path, backup_path)
                    print(f"💾 Backup salvo em: {backup_path}")
                except:
                    pass
            else:
                print("Opção inválida. Voltando...")
                return
        
        # 3. Verificar/gerar chaves automaticamente
        chaves_dir = Path(f"{self.install_principal}/wireguard/chaves")
        private_key_file = chaves_dir / "private.key"
        public_key_file = chaves_dir / "public.key"
        
        renovar_chaves = False
        
        if private_key_file.exists() and public_key_file.exists():
            print(f"\n✅ Par de chaves encontrado em: {chaves_dir}")
            
            # Mostra as chaves existentes
            try:
                pub_key_preview = public_key_file.read_text().strip()
                print(f"🔓 Chave Pública atual: {pub_key_preview}")
            except:
                pass
            
            renovar = input("\nDeseja RENOVAR as chaves? [s/N]: ").strip().lower()
            if renovar == 's':
                renovar_chaves = True
                # Backup das chaves antigas
                try:
                    import shutil
                    backup_dir = chaves_dir / "backup"
                    backup_dir.mkdir(exist_ok=True)
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.copy(private_key_file, backup_dir / f"private.key.{timestamp}")
                    shutil.copy(public_key_file, backup_dir / f"public.key.{timestamp}")
                    print(f"� Backup das chaves antigas salvo em: {backup_dir}")
                except:
                    pass
        else:
            renovar_chaves = True
        
        if renovar_chaves:
            print("\n🔑 Gerando novo par de chaves...")
            chaves_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Gerar chave privada
                result_private = subprocess.run(
                    ["wg", "genkey"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                private_key = result_private.stdout.strip()
                
                # Gerar chave pública
                result_public = subprocess.run(
                    ["wg", "pubkey"],
                    input=private_key,
                    capture_output=True,
                    text=True,
                    check=True
                )
                public_key = result_public.stdout.strip()
                
                # Salvar chaves
                private_key_file.write_text(private_key)
                public_key_file.write_text(public_key)
                os.chmod(private_key_file, 0o600)
                os.chmod(public_key_file, 0o644)
                
                print("✅ Novas chaves geradas e salvas!")
            except Exception as e:
                print(f"❌ Erro ao gerar chaves: {e}")
                return
        else:
            print("✅ Usando chaves existentes.")
            private_key = private_key_file.read_text().strip()
            public_key = public_key_file.read_text().strip()
        
        print(f"\n🔐 Chave Privada: {private_key}")
        print(f"🔓 Chave Pública: {public_key}\n")
        
        # 3. Perguntar tipo de configuração
        print("="*70)
        print("Qual tipo de configuração deseja?")
        print("[1] SERVIDOR (recebe conexões)")
        print("[2] CLIENTE/WORKER (conecta a um servidor)")
        print("[3] Adicionar peer ao servidor existente")
        print("[0] Voltar")
        print("="*70)
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            self._configurar_como_servidor(private_key, public_key)
        elif escolha == "2":
            self._configurar_como_cliente(private_key, public_key)
        elif escolha == "3":
            self._adicionar_peer_dinamico()
        else:
            print("Voltando ao menu anterior...")
    
    def _configurar_como_servidor(self, private_key, public_key):
        """Configura como servidor WireGuard - usa chave local automaticamente"""
        print("\n" + "="*70)
        print("📡 CONFIGURAÇÃO COMO SERVIDOR")
        print("="*70)
        
        print(f"\n🔑 Usando chave privada local automaticamente")
        print(f"🔓 Sua chave pública: {public_key}\n")
        
        # Coleta informações
        ip_servidor = input("IP do servidor na VPN [10.8.0.1/24]: ").strip() or "10.8.0.1/24"
        porta = input("Porta [51820]: ").strip() or "51820"
        
        # Cria configuração do servidor
        config_path = Path("/etc/wireguard/wg0.conf")
        config_content = f"""[Interface]
Address = {ip_servidor}
PrivateKey = {private_key}
ListenPort = {porta}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Peers serão adicionados abaixo
# Use a opção 'Adicionar peer' do menu
"""
        
        try:
            config_path.write_text(config_content)
            os.chmod(config_path, 0o600)
            
            # Habilita IP forwarding
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
            subprocess.run(["sudo", "sed", "-i", "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/", "/etc/sysctl.conf"], check=False)
            
            print("\n✅ Servidor configurado com sucesso!")
            print(f"📁 Config: {config_path}")
            
            # Mostra a configuração criada
            print("\n" + "="*70)
            print("� CONFIGURAÇÃO DO SERVIDOR CRIADA:")
            print("="*70)
            print(config_content)
            print("="*70)
            
            # Inicia automaticamente
            print("\n🚀 Iniciando servidor WireGuard automaticamente...")
            try:
                subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
                print("✅ Servidor WireGuard iniciado e habilitado!\n")
                subprocess.run(["sudo", "wg", "show"], check=False)
            except Exception as e:
                print(f"⚠️  Erro ao iniciar: {e}")
            
            # Mostra informações para compartilhar
            print("\n" + "="*70)
            print("📋 COPIE E ENVIE PARA OS CLIENTES:")
            print("="*70)
            print(f"🔓 Chave Pública do Servidor:\n   {public_key}")
            print(f"\n🌐 IP Público do Servidor:\n   [execute: curl ifconfig.me]")
            print(f"\n🔌 Porta:\n   {porta}")
            print(f"\n📍 Rede VPN:\n   {ip_servidor}")
            print("="*70)
            print("\n💡 Os clientes precisarão destas informações para se conectar!")
            print("💡 Não esqueça de adicionar os peers com a opção do menu!")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def _configurar_como_cliente(self, private_key, public_key):
        """Configura como cliente WireGuard - usa chave local automaticamente"""
        print("\n" + "="*70)
        print("💻 CONFIGURAÇÃO COMO CLIENTE")
        print("="*70)
        
        print(f"\n🔑 Usando chave privada local automaticamente")
        print(f"🔓 Sua chave pública: {public_key}\n")
        
        # Coleta informações - APENAS do servidor remoto
        print("Digite as informações do SERVIDOR:")
        print("-" * 70)
        
        chave_pub_servidor = input("🔓 Chave PÚBLICA do servidor: ").strip()
        if not chave_pub_servidor:
            print("❌ Chave do servidor é obrigatória!")
            return
        
        endpoint = input("🌐 IP público do servidor: ").strip()
        if not endpoint:
            print("❌ Endpoint é obrigatório!")
            return
            
        porta_servidor = input("🔌 Porta do servidor [51820]: ").strip() or "51820"
        
        print("\n" + "-" * 70)
        print("Configurações da VPN local:")
        ip_cliente = input("📍 IP deste cliente na VPN [10.8.0.2/24]: ").strip() or "10.8.0.2/24"
        allowed_ips = input("🌍 Tráfego permitido - Só VPN [10.8.0.0/24] ou Com Internet [0.0.0.0/0]: ").strip() or "10.8.0.0/24"
        
        # Cria configuração do cliente
        config_path = Path("/etc/wireguard/wg0.conf")
        config_content = f"""[Interface]
Address = {ip_cliente}
PrivateKey = {private_key}

[Peer]
PublicKey = {chave_pub_servidor}
Endpoint = {endpoint}:{porta_servidor}
AllowedIPs = {allowed_ips}
PersistentKeepalive = 25
"""
        
        try:
            config_path.write_text(config_content)
            os.chmod(config_path, 0o600)
            
            print("\n✅ Cliente configurado com sucesso!")
            print(f"📁 Config: {config_path}")
            
            # Mostra a configuração criada
            print("\n" + "="*70)
            print("� CONFIGURAÇÃO DO CLIENTE CRIADA:")
            print("="*70)
            print(config_content)
            print("="*70)
            
            # Conecta automaticamente
            print("\n🚀 Conectando ao servidor automaticamente...")
            try:
                subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
                print("✅ Cliente conectado e habilitado!\n")
                subprocess.run(["sudo", "wg", "show"], check=False)
            except Exception as e:
                print(f"⚠️  Erro ao conectar: {e}")
            
            # Mostra informações para enviar ao servidor
            print("\n" + "="*70)
            print("📋 COPIE E ENVIE PARA O ADMINISTRADOR DO SERVIDOR:")
            print("="*70)
            print(f"🔓 Sua Chave Pública:\n   {public_key}")
            print(f"\n📍 IP desejado na VPN:\n   {ip_cliente.split('/')[0]}/32")
            print("="*70)
            print("\n💡 O servidor precisa adicionar você como peer!")
            print("💡 Use o comando no servidor: Adicionar peer")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def _adicionar_peer_dinamico(self):
        """Adiciona peer de forma dinâmica ao servidor"""
        config_path = Path("/etc/wireguard/wg0.conf")
        
        if not config_path.exists():
            print("\n❌ Arquivo de configuração não encontrado!")
            print("💡 Configure o WireGuard como SERVIDOR primeiro usando a opção [1] do menu")
            return
        
        # Verifica se é um servidor (tem ListenPort)
        config_content = config_path.read_text()
        if "ListenPort" not in config_content:
            print("\n❌ Esta configuração não parece ser de um servidor!")
            print("💡 Apenas servidores podem adicionar peers")
            return
        
        print("\n" + "="*70)
        print("➕ ADICIONAR NOVO PEER AO SERVIDOR")
        print("="*70)
        
        print("\n📋 O cliente deve ter enviado estas informações:")
        print("   - Chave Pública do cliente")
        print("   - IP desejado na VPN (ex: 10.8.0.2/32)")
        
        print("\n" + "-"*70)
        
        # Coleta informações do peer
        nome = input("📝 Nome/identificação do peer (ex: worker1, laptop): ").strip() or "peer"
        
        chave_pub = input("🔓 Chave PÚBLICA do peer: ").strip()
        if not chave_pub:
            print("❌ Chave pública é obrigatória!")
            return
        
        ip_peer = input("📍 IP do peer na VPN (ex: 10.8.0.2/32) [/32]: ").strip()
        if not ip_peer:
            print("❌ IP é obrigatório!")
            return
        
        # Garante que termina com /32
        if '/32' not in ip_peer:
            ip_peer = ip_peer.rstrip('/') + '/32'
        
        # Configuração do peer
        peer_config = f"""
[Peer]
# {nome}
PublicKey = {chave_pub}
AllowedIPs = {ip_peer}
"""
        
        try:
            # Adiciona ao arquivo
            with open(config_path, 'a') as f:
                f.write(peer_config)
            
            print("\n✅ Peer adicionado à configuração!")
            
            # Mostra a config atualizada
            print("\n" + "="*70)
            print("📄 CONFIGURAÇÃO ATUALIZADA:")
            print("="*70)
            updated_config = config_path.read_text()
            print(updated_config)
            print("="*70)
            
            # Reinicia automaticamente
            print("\n🔄 Reiniciando WireGuard para aplicar mudanças...")
            try:
                subprocess.run(["sudo", "systemctl", "restart", "wg-quick@wg0"], check=True)
                print("✅ WireGuard reiniciado com sucesso!")
                print("\n📊 Conexões ativas:")
                subprocess.run(["sudo", "wg", "show"], check=False)
            except Exception as e:
                print(f"⚠️  Erro ao reiniciar: {e}")
                print("💡 Execute manualmente: sudo systemctl restart wg-quick@wg0")
                
        except Exception as e:
            print(f"❌ Erro ao adicionar peer: {e}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    def menu_wireguard(self):
        """Menu principal do WireGuard - Versão Dinâmica"""
        opcoes_menu = [
            ("🚀 Configurar WireGuard (Auto-install)", self.configurar_wireguard_dinamico),
            ("▶️  Iniciar/Habilitar WireGuard", self.iniciar_wireguard),
            ("⏸️  Parar WireGuard", self.parar_wireguard),
            ("📊 Ver status e conexões", self.status_wireguard),
            ("🔍 Testar conexão", self.testar_conexao_wireguard),
            ("📄 Visualizar configuração", self.visualizar_config_wireguard),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🔐 GERENCIADOR WIREGUARD VPN", itens_por_pagina=10)
        
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
        
    def opcoes_sistema(self):
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
            ("configura ssh", self.configurar_ssh),
            # ("Configurar acesso root por ssh", self.acess_root),
            ("Faz copia inteligente com rsync", self.rsync_sync),
            ("Inatala/Executa monitor de rede vnstat", self.vnstat),
            ("🔐 Gerenciador WireGuard VPN", self.menu_wireguard),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="⚙️  OPÇÕES DO SISTEMA", itens_por_pagina=15)
        
    def listar_containers_docker(self):
        """Lista todos os containers Docker (rodando e parados)"""
        print("\n=== CONTAINERS DOCKER ===\n")
        
        try:
            # Listar containers rodando
            print("CONTAINERS RODANDO:")
            cmd_running = ["docker", "ps", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"]
            subprocess.run(cmd_running, check=False)
            
            # Listar containers parados
            print("\nCONTAINERS PARADOS:")
            cmd_stopped = ["docker", "ps", "-a", "--filter", "status=exited", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}"]
            subprocess.run(cmd_stopped, check=False)
            
        except Exception as e:
            print(f"❌ Erro ao listar containers: {e}")
    
    def parar_container_docker(self):
        """Para um container Docker"""
        print("\n=== PARAR CONTAINER DOCKER ===\n")
        
        # Listar containers rodando
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container rodando encontrado.")
            return
        
        print("Containers rodando:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para PARAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nParando container '{container}'...")
            subprocess.run(["docker", "stop", container], check=True)
            print(f"Container '{container}' parado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao parar container: {e}")
    
    def iniciar_container_docker(self):
        """Inicia um container Docker parado"""
        print("\n=== INICIAR CONTAINER DOCKER ===\n")
        
        # Listar containers parados
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "status=exited", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container parado encontrado.")
            return
        
        print("Containers parados:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para INICIAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nIniciando container '{container}'...")
            subprocess.run(["docker", "start", container], check=True)
            print(f"Container '{container}' iniciado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar container: {e}")
    
    def reiniciar_container_docker(self):
        """Reinicia um container Docker"""
        print("\n=== REINICIAR CONTAINER DOCKER ===\n")
        
        # Listar containers rodando
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container rodando encontrado.")
            return
        
        print("Containers rodando:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para REINICIAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nReiniciando container '{container}'...")
            subprocess.run(["docker", "restart", container], check=True)
            print(f"Container '{container}' reiniciado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao reiniciar container: {e}")
    
    def excluir_container_docker(self):
        """Exclui um container Docker (parado ou rodando)"""
        print("\n=== EXCLUIR CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        linhas = [l.strip() for l in result.stdout.split('\n') if l.strip()]
        
        if not linhas:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        containers = []
        for i, linha in enumerate(linhas, 1):
            parts = linha.split('\t')
            if len(parts) >= 2:
                nome = parts[0]
                status = parts[1]
                containers.append(nome)
                print(f"[{i}] {nome} - {status}")
        
        escolha = input("\nEscolha o container para EXCLUIR (numero ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            confirmacao = input(f"\nATENCAO: Deseja realmente EXCLUIR o container '{container}'? (s/N): ").strip().lower()
            
            if confirmacao != 's':
                print("Operacao cancelada.")
                return
            
            # Parar container se estiver rodando
            subprocess.run(["docker", "stop", container], check=False, capture_output=True)
            
            # Excluir container
            print(f"\nExcluindo container '{container}'...")
            subprocess.run(["docker", "rm", container], check=True)
            print(f"Container '{container}' excluido com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao excluir container: {e}")
    
    def ver_logs_container_docker(self):
        """Visualiza os logs de um container Docker"""
        print("\n=== LOGS DO CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para ver LOGS (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nOpcoes de logs:")
            print("[1] Ultimas 50 linhas")
            print("[2] Ultimas 100 linhas")
            print("[3] Ultimas 500 linhas")
            print("[4] Todos os logs")
            print("[5] Seguir logs (tempo real)")
            
            opcao_log = input("\nEscolha uma opcao: ").strip()
            
            print(f"\nLogs do container '{container}':\n")
            print("=" * 80)
            
            if opcao_log == "1":
                subprocess.run(["docker", "logs", "--tail", "50", container])
            elif opcao_log == "2":
                subprocess.run(["docker", "logs", "--tail", "100", container])
            elif opcao_log == "3":
                subprocess.run(["docker", "logs", "--tail", "500", container])
            elif opcao_log == "4":
                subprocess.run(["docker", "logs", container])
            elif opcao_log == "5":
                print("Pressione Ctrl+C para sair...\n")
                subprocess.run(["docker", "logs", "-f", container])
            else:
                print("❌ Opção inválida.")
                return
            
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("\n\nVisualizacao de logs interrompida.")
        except Exception as e:
            print(f"❌ Erro ao ver logs: {e}")
    
    def inspecionar_container_docker(self):
        """Inspeciona detalhes de um container Docker"""
        print("\n=== INSPECIONAR CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para INSPECIONAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nDetalhes do container '{container}':\n")
            print("=" * 80)
            
            # Informações básicas
            subprocess.run([
                "docker", "inspect", 
                "--format", "ID: {{.Id}}\nNome: {{.Name}}\nImagem: {{.Config.Image}}\nStatus: {{.State.Status}}\nCriado em: {{.Created}}\nIP: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}\nPortas: {{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}} {{end}}",
                container
            ])
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Erro ao inspecionar container: {e}")
    
    def limpar_recursos_docker(self):
        """Limpa recursos não utilizados do Docker (containers parados, imagens órfãs, volumes, etc)"""
        print("\n=== LIMPAR RECURSOS DOCKER ===\n")
        
        print("ATENCAO: Esta operacao ira remover:")
        print("  - Containers parados")
        print("  - Redes nao utilizadas")
        print("  - Imagens orfas (dangling)")
        print("  - Cache de build")
        
        confirmacao = input("\nDeseja continuar? (s/N): ").strip().lower()
        
        if confirmacao != 's':
            print("Operacao cancelada.")
            return
        
        try:
            print("\nLimpando recursos nao utilizados...\n")
            subprocess.run(["docker", "system", "prune", "-f"], check=True)
            print("\nRecursos limpos com sucesso!")
            
            # Mostrar espaço liberado
            print("\nEspaco em disco Docker:")
            subprocess.run(["docker", "system", "df"])
            
        except Exception as e:
            print(f"❌ Erro ao limpar recursos: {e}")
    
    def menu_gerenciamento_docker(self):
        """Menu de gerenciamento de containers Docker"""
        opcoes_gerenciamento = [
            ("Listar Containers", self.listar_containers_docker),
            ("Iniciar Container", self.iniciar_container_docker),
            ("Parar Container", self.parar_container_docker),
            ("Reiniciar Container", self.reiniciar_container_docker),
            ("Excluir Container", self.excluir_container_docker),
            ("Ver Logs de Container", self.ver_logs_container_docker),
            ("Inspecionar Container", self.inspecionar_container_docker),
            ("Limpar Recursos Nao Utilizados", self.limpar_recursos_docker),
            ("Voltar ao Menu Docker", None)
        ]
        
        self.mostrar_menu_paginado(opcoes_gerenciamento, titulo="📦 GERENCIAMENTO DE CONTAINERS", itens_por_pagina=10)
    
    def menu_docker(self):
        print("\nBem-vindo ao Gerenciador Docker\n")
        self.instala_docker()
        if not os.path.exists(self.install_principal):
            os.makedirs(self.install_principal, exist_ok=True)
            os.chmod(self.install_principal, 0o777)
        """Menu de opções"""
        opcoes_menu = [
            ("Gerenciar Containers Docker", self.menu_gerenciamento_docker),
            ("Força instalação docker", self.instala_docker_force),
            ("Instala portainer", self.instala_portainer),
            ("Instala filebrowser", self.instala_filebrowser),
            ("Instala webserver guacamole", self.instala_webserver_guacamole),
            ("Instala traefik", self.instala_traefik),
            ("||| Conf ||| Adiciona roteamento e serviço ao traefik", self.adiciona_roteador_servico_traefik),
            ("||| Conf ||| Configura rede do container", self.configura_rede),
            ("Instala SFTP sftpgo", self.instala_ftp_sftpgo),
            ("||| Conf ||| Gerenciador SFTP sftpgo", self.gerenciar_usuarios_sftp),
            ("Instala openlitespeed", self.instala_openlitespeed),
            ("||| Conf ||| Controle de sites openlitespeed", self.controle_sites_openlitespeed),
            ("** BD ** Instala mysql", self.instala_mysql),
            ("** BD ** Instala postgres", self.instala_postgres),
            ("||| Conf ||| Gerenciar bancos PostgreSQL", self.gerenciar_bancos_postgres),
            ("Instala wordpress", self.instala_wordpress),
            ("Instala wordpress puro", self.instala_wordpress_puro),
            ("Instala app nodejs", self.instala_app_nodejs),
            ("Instala grafana, prometheus, node-exporter", self.iniciar_monitoramento),
            ("Instala n8n (workflow automation)", self.instalar_n8n),
            ("Start sync pastas com RSYNC", self.start_sync_pastas),
            ("Instala windows KVM docker", self.instala_windows_KVM_docker),
            ("Instala Sistema CISO docker", self.instala_sistema_CISO_docker),
            ("Instala deskto ubuntu webtop", self.desktop_ubuntu_webtop),
            ("Instala Ubuntu", self.ubuntu),
            ("Instala rustdesk", self.instala_rustdesk),
            ("Instala pritunel", self.instala_pritunel),
            ("Instala nextcloud", self.instala_nextcloud),
            ("Instala openvscode", self.instala_openvscode),
            ("Instala vscode_oficial", self.instala_vscode_oficial),
            ("Instala Open WebUI", self.instala_open_webui),
            ("Instala Redis Docker", self.instala_redis_docker),
            ("Instala Evolution API WhatsApp", self.instala_evolution_api_whatsapp),
            ("Instala WAHA WhatsApp (devlikeapro)", self.instala_waha_whatsapp),
            ("Instala browserless (chromium headless)", self.instala_browserless),
            ("Instala selenium-firefox", self.instala_selenium_firefox),
            ("Instala rclone", self.rclone),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🐳 GERENCIADOR DOCKER", itens_por_pagina=15)
    
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
        self.mostrar_menu_paginado(opcoes_menu, titulo="🔄 ATUALIZAÇÕES DO SISTEMA", itens_por_pagina=10)
        
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

    def comandos_essenciais_linux(self):
        """Exibe uma lista de comandos essenciais do Linux Ubuntu."""
        print("\n" + "="*80)
        print("                    COMANDOS ESSENCIAIS DO LINUX UBUNTU")
        print("="*80)
        
        comandos = {
            "📁 NAVEGAÇÃO E LISTAGEM": [
                ("pwd", "Mostra o diretório atual"),
                ("ls", "Lista arquivos e pastas"),
                ("ls -la", "Lista detalhada (incluindo ocultos)"),
                ("ls -lh", "Lista com tamanhos legíveis (KB, MB, GB)"),
                ("cd /caminho", "Navega para um diretório"),
                ("cd ..", "Volta um diretório"),
                ("cd ~", "Vai para o diretório home do usuário"),
                ("find /caminho -name 'arquivo'", "Busca arquivos por nome"),
                ("locate arquivo", "Busca arquivos rapidamente (updatedb)"),
                ("which comando", "Mostra onde está o executável"),
            ],
            
            "📄 CRIAÇÃO E EDIÇÃO DE ARQUIVOS": [
                ("touch arquivo.txt", "Cria arquivo vazio"),
                ("mkdir pasta", "Cria diretório"),
                ("mkdir -p pasta/subpasta", "Cria diretórios recursivamente"),
                ("nano arquivo.txt", "Edita arquivo com nano"),
                ("vim arquivo.txt", "Edita arquivo com vim"),
                ("cat arquivo.txt", "Mostra conteúdo do arquivo"),
                ("head -n 10 arquivo.txt", "Mostra primeiras 10 linhas"),
                ("tail -n 10 arquivo.txt", "Mostra últimas 10 linhas"),
                ("tail -f arquivo.log", "Monitora arquivo em tempo real"),
                ("less arquivo.txt", "Visualiza arquivo página por página"),
            ],
            
            "🗑️ REMOÇÃO E MOVIMENTAÇÃO": [
                ("rm arquivo.txt", "Remove arquivo"),
                ("rm -rf pasta/", "Remove pasta e conteúdo recursivamente"),
                ("rmdir pasta", "Remove pasta vazia"),
                ("mv origem destino", "Move/renomeia arquivo ou pasta"),
                ("cp arquivo.txt copia.txt", "Copia arquivo"),
                ("cp -r pasta/ copia_pasta/", "Copia pasta recursivamente"),
                ("ln -s origem link", "Cria link simbólico"),
            ],
            
            "🔐 PERMISSÕES E PROPRIEDADE": [
                ("chmod 755 arquivo", "Define permissões (rwxr-xr-x)"),
                ("chmod +x script.sh", "Torna arquivo executável"),
                ("chown usuario:grupo arquivo", "Muda proprietário"),
                ("sudo comando", "Executa como administrador"),
                ("su - usuario", "Troca de usuário"),
                ("whoami", "Mostra usuário atual"),
                ("id", "Mostra ID do usuário e grupos"),
            ],
            
            "📊 INFORMAÇÕES DO SISTEMA": [
                ("df -h", "Mostra espaço em disco"),
                ("du -h pasta/", "Mostra tamanho da pasta"),
                ("free -h", "Mostra uso de memória"),
                ("top", "Mostra processos em execução"),
                ("htop", "Monitor de processos interativo"),
                ("ps aux", "Lista todos os processos"),
                ("uptime", "Tempo de execução do sistema"),
                ("uname -a", "Informações do sistema"),
                ("lscpu", "Informações da CPU"),
                ("lsblk", "Lista dispositivos de bloco"),
            ],
            
            "🌐 REDE E CONECTIVIDADE": [
                ("ping google.com", "Testa conectividade"),
                ("wget https://site.com/arquivo", "Baixa arquivo da internet"),
                ("curl -O https://site.com/arquivo", "Baixa arquivo com curl"),
                ("ip addr show", "Mostra interfaces de rede"),
                ("netstat -tuln", "Mostra portas abertas"),
                ("ss -tuln", "Mostra conexões de rede (moderno)"),
                ("nslookup dominio.com", "Consulta DNS"),
            ],
            
            "🔄 PROCESSOS E SERVIÇOS": [
                ("systemctl status serviço", "Status de um serviço"),
                ("systemctl start serviço", "Inicia serviço"),
                ("systemctl stop serviço", "Para serviço"),
                ("systemctl restart serviço", "Reinicia serviço"),
                ("systemctl enable serviço", "Habilita na inicialização"),
                ("kill PID", "Mata processo por ID"),
                ("killall nome_processo", "Mata processos por nome"),
                ("jobs", "Lista trabalhos em background"),
                ("nohup comando &", "Executa comando em background"),
            ],
            
            "📦 GERENCIAMENTO DE PACOTES": [
                ("sudo apt update", "Atualiza lista de pacotes"),
                ("sudo apt upgrade", "Atualiza pacotes instalados"),
                ("sudo apt install pacote", "Instala pacote"),
                ("sudo apt remove pacote", "Remove pacote"),
                ("sudo apt search termo", "Busca pacotes"),
                ("apt list --installed", "Lista pacotes instalados"),
                ("sudo apt autoremove", "Remove dependências não usadas"),
                ("sudo apt clean", "Limpa cache de pacotes"),
            ],
            
            "🔧 ARQUIVOS E COMPRESSÃO": [
                ("tar -czf arquivo.tar.gz pasta/", "Compacta pasta"),
                ("tar -xzf arquivo.tar.gz", "Descompacta arquivo"),
                ("zip -r arquivo.zip pasta/", "Cria arquivo ZIP"),
                ("unzip arquivo.zip", "Extrai arquivo ZIP"),
                ("gzip arquivo.txt", "Compacta arquivo"),
                ("gunzip arquivo.txt.gz", "Descompacta arquivo"),
            ],
            
            "🔍 BUSCA E FILTROS": [
                ("grep 'texto' arquivo.txt", "Busca texto em arquivo"),
                ("grep -r 'texto' pasta/", "Busca recursiva em pasta"),
                ("grep -i 'texto' arquivo.txt", "Busca ignorando case"),
                ("awk '{print $1}' arquivo.txt", "Processa colunas"),
                ("sed 's/old/new/g' arquivo.txt", "Substitui texto"),
                ("sort arquivo.txt", "Ordena linhas"),
                ("uniq arquivo.txt", "Remove linhas duplicadas"),
                ("wc -l arquivo.txt", "Conta linhas do arquivo"),
            ],
        }
        
        for categoria, lista_comandos in comandos.items():
            print(f"\n{categoria}")
            print("-" * 60)
            for comando, descricao in lista_comandos:
                print(f"  {comando:<35} # {descricao}")
        
        print("\n" + "="*80)
        print("💡 DICAS IMPORTANTES:")
        print("   • Use 'man comando' para ver manual detalhado")
        print("   • Use 'comando --help' para ver opções disponíveis")
        print("   • Use Tab para autocompletar comandos e caminhos")
        print("   • Use Ctrl+C para cancelar comando em execução")
        print("   • Use Ctrl+Z para pausar processo (retomar com 'fg')")
        print("   • Use history para ver comandos anteriores")
        print("="*80)
        
        input("\nPressione Enter para voltar ao menu...")

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()

def main():
    servicos = Sistema()
    print(f"""
===========================================================================
===========================================================================

Execute com: bash /install_principal/install_master.txt

===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.227
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
        ("Comandos essenciais do Linux", servicos.comandos_essenciais_linux),
        ("Menu de outras opções", servicos.opcoes_sistema),
        ("Menu Docker", servicos.menu_docker),
    ]
    servicos.mostrar_menu_paginado(opcoes_menu, titulo="🖥️  MENU PRINCIPAL - INSTALL MASTER", itens_por_pagina=10, principal=True)
    

if __name__ == "__main__":
    main()
