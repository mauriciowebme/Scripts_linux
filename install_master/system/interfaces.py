import os
import shutil
import subprocess
import textwrap
import time

from install_master.core.docker_base import DockerBase


class MixinInterfaces(DockerBase):

    def instalar_interface_gnome(self,):
        escolha = input("Deseja uma instalação completa ou mais simples? (Digite '1' para completa ou '2' para simples): ").strip()
        self.atualizar_sistema_completa()
        if escolha == "1":
            self.executar_comandos([
                "sudo apt install ubuntu-gnome-desktop -y",
                "sudo apt install gnome-software -y",
                "sudo reboot",
                ], comando_direto=True)
        elif escolha == "2":
            self.executar_comandos([
            "sudo apt install gnome-shell gdm3 gnome-session -y",
            "sudo systemctl enable gdm",
            "sudo systemctl start gdm",
            "sudo reboot",
            ], comando_direto=True)
        else:
            print("Opção inválida. Nenhuma ação foi realizada.")

    def menu_swap(self):
        """Menu de gerenciamento de Swap"""
        while True:
            print("\n" + "="*50)
            print("💾 GERENCIAMENTO DE SWAP")
            print("="*50)

            print("\n📊 Status Atual:")
            subprocess.run("sudo swapon --show", shell=True)
            subprocess.run("free -h | grep -E 'Mem|Swap'", shell=True)

            try:
                result = subprocess.run("cat /proc/sys/vm/swappiness", shell=True, capture_output=True, text=True)
                print(f"\n⚙️  Swappiness atual: {result.stdout.strip()}")
            except:
                pass

            print("\n" + "-"*50)
            print(" MENU SWAP")
            print("-" * 50)
            print("[1] ➕  Criar/Redimensionar Swap")
            print("[2] 🗑️  Remover Swap")
            print("[3] ⚙️  Ajustar Swappiness")
            print("[4] 🔄  Recarregar Swap (desliga e liga)")
            print("[0] ↩️  Voltar")
            print("="*50)

            escolha = input("\nEscolha: ").strip()

            if escolha == '1':
                novo_tamanho = input('\n📐 Digite o tamanho em GB (ex: 4): ').strip()
                if not novo_tamanho.isdigit():
                    print("❌ Digite apenas números.")
                    continue

                print(f"\n🔧 Criando swap de {novo_tamanho}GB...")
                comandos = [
                    "sudo swapoff /swap.img 2>/dev/null || true",
                    "sudo rm -f /swap.img",
                    f"sudo fallocate -l {novo_tamanho}G /swap.img",
                    "sudo chmod 600 /swap.img",
                    "sudo mkswap /swap.img",
                    "sudo swapon /swap.img"
                ]
                for cmd in comandos:
                    subprocess.run(cmd, shell=True)

                result = subprocess.run("grep -q '/swap.img' /etc/fstab", shell=True)
                if result.returncode != 0:
                    print("📝 Adicionando swap ao /etc/fstab...")
                    subprocess.run('echo "/swap.img none swap sw 0 0" | sudo tee -a /etc/fstab', shell=True)

                print("⚙️  Configurando swappiness para 20...")
                subprocess.run("sudo sysctl vm.swappiness=20", shell=True)

                result = subprocess.run("grep -q 'vm.swappiness' /etc/sysctl.conf", shell=True)
                if result.returncode == 0:
                    subprocess.run("sudo sed -i 's/vm.swappiness=.*/vm.swappiness=20/' /etc/sysctl.conf", shell=True)
                else:
                    subprocess.run('echo "vm.swappiness=20" | sudo tee -a /etc/sysctl.conf', shell=True)

                print(f"\n✅ Swap de {novo_tamanho}GB criado com sucesso! Swappiness configurado para 20.")
                input("\nEnter para continuar...")

            elif escolha == '2':
                confirma = input("\n⚠️  Tem certeza que deseja remover o swap? (s/n): ").strip().lower()
                if confirma == 's':
                    print("\n🗑️  Removendo swap...")
                    subprocess.run("sudo swapoff /swap.img 2>/dev/null || true", shell=True)
                    subprocess.run("sudo rm -f /swap.img", shell=True)
                    subprocess.run("sudo sed -i '/\\/swap.img/d' /etc/fstab", shell=True)
                    print("✅ Swap removido!")
                input("\nEnter para continuar...")

            elif escolha == '3':
                print("\n📖 Swappiness define quando o sistema usa swap:")
                print("   0  = Usa swap apenas em emergência")
                print("   20 = Recomendado para servidores com SSD")
                print("   60 = Padrão do Linux")
                print("   100 = Usa swap agressivamente")

                valor = input("\nDigite o valor (0-100): ").strip()
                if not valor.isdigit() or int(valor) > 100:
                    print("❌ Valor inválido.")
                    continue

                print(f"\n⚙️  Configurando swappiness para {valor}...")
                subprocess.run(f"sudo sysctl vm.swappiness={valor}", shell=True)

                result = subprocess.run("grep -q 'vm.swappiness' /etc/sysctl.conf", shell=True)
                if result.returncode == 0:
                    subprocess.run(f"sudo sed -i 's/vm.swappiness=.*/vm.swappiness={valor}/' /etc/sysctl.conf", shell=True)
                else:
                    subprocess.run(f'echo "vm.swappiness={valor}" | sudo tee -a /etc/sysctl.conf', shell=True)

                print(f"✅ Swappiness configurado para {valor} (permanente)!")
                input("\nEnter para continuar...")

            elif escolha == '4':
                print("\n🔄 Recarregando swap...")
                subprocess.run("sudo swapoff -a && sudo swapon -a", shell=True)
                print("✅ Swap recarregado!")
                input("\nEnter para continuar...")

            elif escolha == '0':
                break

    def instalar_deb(self,):
        caminho = input('Insira o caminho absoluto do .deb para instalar: ')
        self.atualizar_sistema_completa()

        comandos = [
                f"sudo dpkg -i {caminho}",
                f"sudo apt install -f -y",
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
                        "sudo reboot",
                    ]
                    self.executar_comandos(comandos, comando_direto=True)
                    print("xfce4 reinstalado com sucesso.")
                else:
                    print("Iniciando xfce4...")
                    self.executar_comandos(["startxfce4 "], comando_direto=True)
            else:
                print("xfce4 não encontrado. Instalando xfce4...")
                self.atualizar_sistema_completa()
                comandos = [
                    "sudo apt install xfce4 xfce4-goodies lightdm dbus-x11 xinit",
                    "sudo dpkg-reconfigure lightdm",
                    "sudo systemctl enable lightdm --now",
                    "rm -f ~/.Xauthority ~/.cache/sessions/*",
                    "sudo reboot",
                ]
                self.executar_comandos(comandos, comando_direto=True)
                print("xfce4 instalado com sucesso.")

                print("Iniciando xfce4...")
                self.executar_comandos(["startxfce4 "], comando_direto=True)

        except subprocess.CalledProcessError as e:
            print(f"Erro durante a execução do comando: {e}")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")

    def instala_vnc_server(self,):
        """Instala TigerVNC Server com XFCE - funciona com ou sem interface gráfica no host"""
        print("\n" + "="*55)
        print(" INSTALAÇÃO DO VNC SERVER (ACESSO REMOTO)")
        print("="*55)
        print("Instala TigerVNC Server com terminal xterm")
        print("Um terminal xterm abre automaticamente ao conectar")
        print("O serviço iniciará automaticamente no boot.")
        print("-"*55)

        print("\n Configure a senha de acesso VNC:")
        print("(4-8 caracteres, será usada pelo cliente VNC)")
        while True:
            senha_vnc = input("Senha VNC: ").strip()
            if 4 <= len(senha_vnc) <= 8:
                break
            print(" A senha deve ter entre 4 e 8 caracteres.")

        home_dir = os.path.expanduser("~")
        try:
            import pwd
            stat_info = os.stat(home_dir)
            user = pwd.getpwuid(stat_info.st_uid).pw_name
        except Exception:
            user = os.getenv('SUDO_USER') or os.getenv('USER') or 'root'
            if user == 'root':
                home_dir = '/root'
            else:
                home_dir = f'/home/{user}'

        print("\n Instalando TigerVNC Server...")
        comandos = [
            "sudo apt update",
            "sudo apt install -y tigervnc-standalone-server tigervnc-common",
        ]
        self.executar_comandos(comandos, comando_direto=True)

        if not self.verificar_instalacao('xterm'):
            print("\n xterm não encontrado. Instalando...")
            comandos = [
                "sudo apt install -y xterm x11-xserver-utils dbus-x11",
            ]
            self.executar_comandos(comandos, comando_direto=True)
            print(" xterm instalado.")
        else:
            print(" xterm já está instalado.")

        print("\n Configurando ambiente VNC...")
        vnc_dir_user = os.path.join(home_dir, ".vnc")
        os.makedirs(vnc_dir_user, exist_ok=True)

        xstartup_path = os.path.join(vnc_dir_user, "xstartup")
        xstartup_content = (
            "#!/bin/bash\n"
            "unset SESSION_MANAGER\n"
            "unset DBUS_SESSION_BUS_ADDRESS\n"
            "\n"
            "# Adiciona opencode ao PATH para funcionar no VNC\n"
            "export PATH=\"/home/ubuntu/.opencode/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$PATH\"\n"
            "\n"
            "[ -f $HOME/.bashrc ] && . $HOME/.bashrc\n"
            "[ -f $HOME/.profile ] && . $HOME/.profile\n"
            "\n"
            "# Configura tema escuro estilo VS Code Dark+\n"
            "cat > $HOME/.Xresources << 'XRES'\n"
            "xterm*background: #1e1e1e\n"
            "xterm*foreground: #d4d4d4\n"
            "xterm*cursorColor: #00ff00\n"
            "xterm*color0: #1e1e1e\n"
            "xterm*color8: #555555\n"
            "xterm*color1: #f44747\n"
            "xterm*color9: #f44747\n"
            "xterm*color2: #6a9955\n"
            "xterm*color10: #6a9955\n"
            "xterm*color3: #dcdcaa\n"
            "xterm*color11: #dcdcaa\n"
            "xterm*color4: #569cd6\n"
            "xterm*color12: #569cd6\n"
            "xterm*color5: #c586c0\n"
            "xterm*color13: #c586c0\n"
            "xterm*color6: #4ec9b0\n"
            "xterm*color14: #4ec9b0\n"
            "xterm*color7: #d4d4d4\n"
            "xterm*color15: #ffffff\n"
            "xterm*faceName: Monospace\n"
            "xterm*faceSize: 12\n"
            "xterm*scrollBar: false\n"
            "xterm*internalBorder: 0\n"
            "xterm*borderWidth: 0\n"
            "XRES\n"
            "\n"
            "xrdb $HOME/.Xresources\n"
            "\n"
            "# xterm maximizado - ajusta automaticamente ao tamanho da janela VNC\n"
            "exec /usr/bin/xterm -maximized -ls -title \"Terminal VNC\" +sb -b 0\n"
        )
        with open(xstartup_path, 'w') as f:
            f.write(xstartup_content)
        os.chmod(xstartup_path, 0o755)
        print(f" xstartup configurado em: {xstartup_path}")

        passwd_file = os.path.join(vnc_dir_user, "passwd")

        if os.path.exists(passwd_file):
            os.remove(passwd_file)

        temp_pass_file = "/tmp/vnc_pass.txt"
        with open(temp_pass_file, 'w') as f:
            f.write(senha_vnc + senha_vnc)

        try:
            with open(temp_pass_file, 'r') as f:
                subprocess.run(
                    ["sudo", "vncpasswd", "-f"],
                    stdin=f,
                    stdout=open(passwd_file, 'wb'),
                    check=True
                )
        except Exception:
            with open(temp_pass_file, 'r') as f:
                subprocess.run(
                    ["vncpasswd", "-f"],
                    stdin=f,
                    stdout=open(passwd_file, 'wb'),
                    check=True
                )

        if os.path.exists(temp_pass_file):
            os.remove(temp_pass_file)

        os.chmod(passwd_file, 0o600)

        if user != 'root':
            subprocess.run(f"sudo chown -R {user}:{user} {vnc_dir_user}", shell=True)

        print(f" Senha VNC configurada.")

        print("\n Criando serviço systemd para iniciar no boot...")
        display = ":1"
        resolution = "1350x720"

        service_content = textwrap.dedent(f"""\
            [Unit]
            Description=TigerVNC Server - Display {display}
            After=syslog.target network.target

            [Service]
            Type=simple
            User={user}
            Group={user}
            Environment=HOME={home_dir}
            Environment=DISPLAY={display}
            WorkingDirectory={home_dir}
            ExecStartPre=/bin/sh -c '/usr/bin/vncserver -kill {display} > /dev/null 2>&1 || :'
            ExecStart=/usr/bin/vncserver {display} -fg -geometry {resolution} -depth 24 -localhost no -SecurityTypes VncAuth -PasswordFile {home_dir}/.vnc/passwd
            ExecStop=/bin/sh -c '/usr/bin/vncserver -kill {display} 2>/dev/null || :'
            Restart=on-failure
            RestartSec=5

            [Install]
            WantedBy=multi-user.target
        """)

        service_path = "/etc/systemd/system/vncserver@.service"

        temp_service = "/tmp/vncserver.service"
        with open(temp_service, 'w') as f:
            f.write(service_content)

        subprocess.run(["sudo", "mv", temp_service, service_path], check=True)

        print("\n Habilitando e iniciando serviço VNC...")

        subprocess.run(["sudo", "systemctl", "stop", "vncserver@1.service"], check=False)
        time.sleep(2)

        subprocess.run(["sudo", "pkill", "-9", "Xtigervnc"], check=False)
        subprocess.run(["sudo", "pkill", "-9", "xterm"], check=False)
        time.sleep(1)

        comandos = [
            "sudo systemctl daemon-reload",
            "sudo systemctl enable vncserver@1.service",
            "sudo systemctl start vncserver@1.service",
        ]
        self.executar_comandos(comandos, comando_direto=True)

        time.sleep(3)

        print("\n Verificando status do serviço...")
        subprocess.run("sudo systemctl status vncserver@1.service --no-pager", shell=True)

        print("\n Liberando porta 5901 no firewall...")

        try:
            ufw_check = subprocess.run(
                ["sudo", "ufw", "status"],
                capture_output=True, text=True
            )
            if "active" in ufw_check.stdout.lower():
                subprocess.run(
                    ["sudo", "ufw", "allow", "5901/tcp"],
                    check=True
                )
                print(" Porta 5901 liberada no UFW")
            else:
                print("  UFW inativo, pulando...")
        except Exception as e:
            print(f"  UFW não encontrado: {e}")

        try:
            check_result = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", "5901", "-j", "ACCEPT"],
                capture_output=True
            )
            if check_result.returncode == 0:
                print("  Porta 5901 já liberada no iptables")
            else:
                subprocess.run(
                    ["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", "5901", "-j", "ACCEPT"],
                    check=True
                )
                print(" Porta 5901 liberada no iptables")

                if shutil.which("netfilter-persistent"):
                    subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)
                    print("  Regras salvas via netfilter-persistent")
                elif shutil.which("iptables-save"):
                    subprocess.run(
                        ["sudo", "sh", "-c", "iptables-save > /etc/iptables.rules"],
                        check=False
                    )
                    print("  Regras salvas em /etc/iptables.rules")
        except Exception as e:
            print(f"  Não foi possível configurar iptables: {e}")

        ip = self.exibe_ip()
        print("\n" + "="*55)
        print(" VNC SERVER INSTALADO COM SUCESSO!")
        print("="*55)
        print(f"Endereço de acesso: {ip}:5901")
        print(f"Display: {display}")
        print(f"Resolução: {resolution}")
        print(f"Ambiente: Terminal xterm (bash)")
        print("-"*55)
        print(" Clientes VNC recomendados:")
        print("  - Windows: RealVNC Viewer, TightVNC")
        print("  - Linux: Remmina, TigerVNC Viewer")
        print("  - macOS: Screen Sharing (nativo), RealVNC")
        print("  - Android/iOS: VNC Viewer")
        print("-"*55)
        print(" Comandos úteis:")
        print("  status:  sudo systemctl status vncserver@1.service")
        print("  stop:    sudo systemctl stop vncserver@1.service")
        print("  start:   sudo systemctl start vncserver@1.service")
        print("  restart: sudo systemctl restart vncserver@1.service")
        print("="*55)

    def menu_interfaces_graficas(self):
        """Submenu para instalação de interfaces gráficas"""
        opcoes = [
            ("📦  Instalar/Iniciar XFCE (Leve)", self.instalar_interface_xfce),
            ("📦  Instalar GNOME (Padrão Ubuntu)", self.instalar_interface_gnome),
            ("📦  Instalar Desktop Ubuntu Webtop (Docker)", self.desktop_ubuntu_webtop),
            ("🖥️  Instalar VNC Server (Acesso Remoto)", self.instala_vnc_server),
            ("↩️  Voltar", None)
        ]
        self.mostrar_menu_paginado(opcoes, titulo="🖥️  INTERFACES GRÁFICAS", itens_por_pagina=10)
