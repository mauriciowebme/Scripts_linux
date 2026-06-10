import os
import subprocess
import time
from pathlib import Path


def check_for_update(sistema_instance=None):
    path_principal = Path("/install_principal")

    if not path_principal.exists():
        try:
            path_principal.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            print(f"Criando {path_principal} com sudo...")
            subprocess.run(["sudo", "mkdir", "-p", str(path_principal)], check=True)

    if not os.access(path_principal, os.W_OK):
        print(f"Ajustando permissões de {path_principal}...")
        user = os.getenv('USER') or os.environ.get('USERNAME') or 'root'
        subprocess.run(["sudo", "chown", "-R", f"{user}:{user}", str(path_principal)], check=True)

    update_file = path_principal / "update_check.txt"
    execute_file = path_principal / "install_master.txt"

    try:
        content = (
            "#!/bin/bash\n"
            "# Limpeza segura: usa sudo apenas se a pasta for protegida (ex: criada pelo root)\n"
            "if [ -d \"/tmp/Scripts_linux\" ]; then\n"
            "    if [ ! -w \"/tmp/Scripts_linux\" ]; then\n"
            "        sudo rm -rf /tmp/Scripts_linux\n"
            "    else\n"
            "        rm -rf /tmp/Scripts_linux\n"
            "    fi\n"
            "fi\n"
            "git clone --depth=1 https://github.com/mauriciowebme/Scripts_linux.git /tmp/Scripts_linux && "
            "python3 /tmp/Scripts_linux/install_master.py \"$@\""
        )
        execute_file.write_text(content)

        subprocess.run(["sudo", "chmod", "+x", str(execute_file)], check=False)

        link_path = "/usr/local/bin/install_master"
        if not os.path.exists(link_path):
            subprocess.run(["sudo", "ln", "-sf", str(execute_file), link_path], check=False)
            print(f"Bônus: Comando '{link_path.split('/')[-1]}' criado! Nas próximas vezes basta digitar: install_master")

    except Exception as e:
        print(f"Aviso: Não foi possível escrever em {execute_file}: {e}")

    if update_file.exists():
        return

    print("Primeira execução detectada. Atualizando o sistema...")

    if sistema_instance:
        sistema_instance.atualizar_sistema_completa()
    else:
        subprocess.run("sudo apt update".split(), check=False)
        subprocess.run("sudo apt upgrade -y".split(), check=False)
        subprocess.run("sudo apt full-upgrade -y".split(), check=False)
        subprocess.run("sudo apt autoremove -y".split(), check=False)
        subprocess.run("sudo apt autoclean".split(), check=False)

    subprocess.run("sudo systemctl disable NetworkManager-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl disable systemd-networkd-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl mask systemd-networkd-wait-online.service".split(), check=False)
    subprocess.run("sudo systemctl mask NetworkManager-wait-online.service".split(), check=False)

    try:
        subprocess.run(["sudo", "timedatectl", "set-timezone", "America/Sao_Paulo"], check=True)
        subprocess.run(["sudo", "timedatectl", "set-ntp", "true"], check=True)
    except Exception as ex:
        try:
            subprocess.run(["sudo", "ln", "-sf", "/usr/share/zoneinfo/America/Sao_Paulo", "/etc/localtime"], check=True)
        except Exception as ex:
            print(f"⚠️  Erro ao configurar timezone: {ex}\n")

    try:
        update_file.write_text("Atualização realizada em: " + time.strftime("%Y-%m-%d %H:%M:%S"))
        print("Atualização concluída.\n")
    except Exception as e:
        print(f"Não foi possível salvar log de atualização: {e}")
