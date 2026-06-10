import os
import random
import shlex
import socket
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from .shell import ExecutaComandos


class DockerBase(ExecutaComandos):
    def __init__(self):
        super().__init__()
        self.install_principal = '/install_principal'
        self.bds = self.install_principal + '/bds'
        self.redes_docker = ['_traefik', 'interno']
        self.atmoz_sftp_arquivo_conf = os.path.join(
            f"{self.install_principal}/atmoz_sftp/", "users.conf"
        )
        self.mysql_root_password = None
        self.postgres_password = None

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
            subprocess.run(["docker", "run", *run_cmd, tag], check=True)
        else:
            subprocess.run(["docker", "run", *run_cmd], check=True)

    def escolher_porta_disponivel(self, inicio=40000, fim=40500, quantidade=1):
        portas_disponiveis = []
        print(f"Escolhendo {quantidade} portas disponíveis entre {inicio} e {fim}...")
        for porta in range(inicio, fim + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', porta)) != 0:
                    portas_disponiveis.append(porta)
                    if len(portas_disponiveis) == quantidade:
                        print(f"Portas {portas_disponiveis} estão disponíveis e serão usadas.")
                        return portas_disponiveis

        if len(portas_disponiveis) < quantidade:
            print(f"Nenhuma porta disponível entre {inicio} e {fim}.")
            return None

    def cria_rede_docker(self, associar_todos=False, associar_container_nome=False,
                         numero_rede=None, nome_rede=None):
        try:
            result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)

            if nome_rede is not None:
                self.redes_docker = [nome_rede]
                numero_rede = -1

            for rede in self.redes_docker:
                if rede not in result.stdout:
                    print(f"Rede '{rede}' não encontrada. Criando rede...")
                    subprocess.run(["docker", "network", "create", rede])
                    print(f"Rede '{rede}' criada com sucesso.")

            if associar_container_nome:
                if numero_rede is not None:
                    redes = [self.redes_docker[numero_rede]]
                else:
                    redes = self.redes_docker
                for rede in redes:
                    connect_result = subprocess.run(
                        ["docker", "network", "disconnect", "bridge", associar_container_nome],
                        capture_output=True, text=True
                    )

                    if connect_result.returncode == 0:
                        print(f"Container {associar_container_nome} desconectado da rede bridge com sucesso.")

                    connect_result = subprocess.run(
                        ["docker", "network", "connect", rede, associar_container_nome],
                        capture_output=True, text=True
                    )

                    if connect_result.returncode == 0:
                        print(f"Container {associar_container_nome} associado à rede '{rede}' com sucesso.")

            if associar_todos:
                result = subprocess.run(["docker", "ps", "-q"], capture_output=True, text=True)
                container_ids = result.stdout.strip().splitlines()
                for container_id in container_ids:
                    for rede in self.redes_docker:
                        connect_result = subprocess.run(
                            ["docker", "network", "connect", rede, container_id],
                            capture_output=True, text=True
                        )

                        if connect_result.returncode == 0:
                            print(f"Container {container_id} associado à rede '{rede}' com sucesso.")

        except Exception:
            pass

    def comandos_in_container(self, nome_container, comandos, tipo='bash'):
        comandos_containers = []
        for comando in comandos:
            comandos_containers += [f'docker exec -i -u root {nome_container} {tipo} -c \'{comando}\'']
        self.executar_comandos(comandos_containers)

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
        caracteres_especiais = "!@#$%_"

        characters = ascii_uppercase + ascii_lowercase + digits + caracteres_especiais

        password = (
            random.choice(ascii_uppercase) +
            random.choice(ascii_lowercase) +
            random.choice(digits) +
            random.choice(caracteres_especiais)
        )

        password += ''.join(random.choice(characters) for _ in range(length - 4))
        password = ''.join(random.sample(password, len(password)))
        return password

    def gerenciar_permissoes_pasta(self, pasta: str = None, permissao: str = None):
        if pasta is None:
            pasta = input("Digite o caminho (arquivo ou pasta): ").strip()
        else:
            if not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)

        if not os.path.exists(pasta):
            print(f"Erro: '{pasta}' não existe.")
            return

        if permissao is None:
            permissao = input("Digite as permissões (ex: 777, 755, 644): ").strip()

        try:
            permissao_octal = int(permissao, 8)

            if os.path.isfile(pasta):
                os.chmod(pasta, permissao_octal)
                print(f"Permissões do arquivo alteradas para: {oct(permissao_octal)}")

            elif os.path.isdir(pasta):
                os.chmod(pasta, permissao_octal)

                for root, dirs, files in os.walk(pasta):
                    for nome in dirs:
                        try:
                            os.chmod(os.path.join(root, nome), permissao_octal)
                        except Exception:
                            print(f"Erro ao alterar: {os.path.join(root, nome)}")

                    for nome in files:
                        try:
                            os.chmod(os.path.join(root, nome), permissao_octal)
                        except Exception:
                            print(f"Erro ao alterar: {os.path.join(root, nome)}")

                print(f"Permissões da pasta e itens alteradas para: {oct(permissao_octal)}")

        except ValueError:
            print("Erro: Permissões inválidas. Use formato octal (ex: 777, 755, 644).")
        except PermissionError:
            print("Erro: Permissão negada. Execute como root.")
        except Exception as e:
            print(f"Erro: {e}")

    def verifica_container_existe(self, container_name, install_function):
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
            install_function()
            print('Aguarde terminando de instalar...')
            import time
            time.sleep(30)
            print(f"Container {container_name} instalado com sucesso.")
