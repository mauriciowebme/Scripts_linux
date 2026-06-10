import json
import os
import shlex
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Union

from install_master.core.docker_base import DockerBase


class MixinLinuxCommands(DockerBase):

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
        subprocess.CalledProcessError – se rsync retornar erro "fatal".
        """
        if not shutil.which("rsync"):
            print("rsync não encontrado. Instalando…")
            self.executar_comandos(
                ["sudo apt update", "sudo apt install -y rsync"], comando_direto=True
            )
            if not shutil.which("rsync"):
                raise RuntimeError("Falha ao instalar rsync.")

        origem = origem or input("Digite o caminho da pasta de origem: ").strip()
        destino = destino or input("Digite o caminho da pasta de destino: ").strip()

        if not os.path.exists(origem):
            raise FileNotFoundError(f"Caminho de origem não existe: {origem}")

        os.makedirs(destino, exist_ok=True)

        cmd = [
            "rsync",
            "-rltD",
            "--no-owner",
            "--no-group",
            "--partial",
            "--inplace",
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

        for tentativa in range(1, max_retries + 1):
            self.gerenciar_permissoes_pasta(destino, "777")
            result = subprocess.run(cmd)
            rc = result.returncode

            if rc == 0:
                print("✅  Sincronização concluída sem pendências.")
                return

            if rc in (23, 24):
                print(f"[{tentativa}/{max_retries}] Ainda há arquivos pendentes "
                    f"(exit-code {rc}). Nova tentativa em 5 s…")
                time.sleep(5)
                continue

            if rc == 11 and tentativa < max_retries:
                print(f"[{tentativa}/{max_retries}] Erro de I/O.")
                time.sleep(5)
                continue

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

        def run(cmd: str, *, shell=False):
            print(f"$ {cmd}")
            subprocess.run(
                cmd if shell else shlex.split(cmd),
                shell=shell,
                check=True,
                executable="/bin/bash" if shell else None,
            )

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

        if "1" in escolhas:
            try:
                porta = int(input("Nova porta SSH: "))
                run(f"sudo sed -i 's/^#\\?Port .*/Port {porta}/' /etc/ssh/sshd_config")
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print(f"✅ Porta alterada para {porta}\n")
            except ValueError:
                print("❌ Porta inválida. Pulando.\n")

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

        if "3" in escolhas:
            key_dir = Path("/install_principal/ssh")
            key_dir.mkdir(parents=True, exist_ok=True)
            key_dir.chmod(0o700)

            default_key = key_dir / "id_ed25519"
            key_path = default_key
            escolha  = "s"

            if default_key.exists():
                escolha = input(
                    "Chave existente encontrada.\n"
                    "[S] Substituir | [A] Adicionar nova | [C] Cancelar: "
                ).strip().lower()

                if escolha == "c":
                    print("Operação cancelada.\n")
                    key_path = None
                elif escolha == "a":
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    key_path = key_dir / f"id_ed25519_{ts}"
                else:
                    key_path = default_key
                    run(f"rm -f {key_path} {key_path}.pub")

            if key_path:
                proteger = input("Proteger com passphrase? [s/n] ").lower().startswith("s")
                passphrase = input("Passphrase: ") if proteger else ""

                passphrase_esc = shlex.quote(passphrase)
                run(
                    f"ssh-keygen -t ed25519 -a 100 -f {key_path} "
                    f"-N {passphrase_esc}"
                )

                run("mkdir -p /root/.ssh")
                run("chmod 700 /root/.ssh")
                run(f"cat {key_path}.pub >> /root/.ssh/authorized_keys", shell=True)
                run("chmod 600 /root/.ssh/authorized_keys")

                run(
                    "(grep -q '^PubkeyAuthentication' /etc/ssh/sshd_config) || "
                    "echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config",
                    shell=True,
                )
                run(
                    "(grep -q '^PermitRootLogin' /etc/ssh/sshd_config && "
                    " sed -i 's/^PermitRootLogin.*/PermitRootLogin prohibit-password/' "
                    "/etc/ssh/sshd_config) || "
                    "echo 'PermitRootLogin prohibit-password' >> /etc/ssh/sshd_config",
                    shell=True,
                )

                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)

                print(f"✅ Chave criada/atualizada e root liberado somente por chave: {key_path}\n")

        if "4" in escolhas:
            print(
                "\n⚠️  AVISO IMPORTANTE:\n"
                "Desativar PasswordAuthentication bloqueará qualquer usuário sem chave SSH configurada.\n"
                "Abra outro terminal e confirme que consegue se conectar via chave ANTES de prosseguir."
            )
            if input("Já testou e quer continuar? [digite CONFIRMAR]: ") == "CONFIRMAR":
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
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print("✅ Login por senha desabilitado.\n")
            else:
                print("Operação abortada.\n")

        if "5" in escolhas:
            print(
                "\n⚠️  AVISO IMPORTANTE:\n"
                "Habilitar PasswordAuthentication permitirá login por senha novamente.\n"
            )
            if input("Podemo continuar? [digite CONFIRMAR]: ") == "CONFIRMAR":
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
                run("sudo systemctl restart ssh || sudo systemctl restart sshd", shell=True)
                print("✅ Login por senha habilitado.\n")
            else:
                print("Operação abortada.\n")

        print("==== Configurações concluídas ====")
