import os
import json
import platform
import shlex
import shutil
import subprocess
import textwrap
import time

from install_master.core.docker_base import DockerBase


class MixinTerminal(DockerBase):
    def _instala_ttyd_backend(self):
        print("\n Instalando backend do terminal (ttyd)...")
        print("-" * 60)

        ttyd_dir = f"{self.install_principal}/ttyd"
        os.makedirs(ttyd_dir, exist_ok=True)

        detect_machine = platform.machine().lower()
        arch_map = {
            "x86_64": "x86_64",
            "amd64": "x86_64",
            "aarch64": "arm64",
            "arm64": "arm64",
            "armv7l": "arm",
        }
        ttyd_arch = arch_map.get(detect_machine, "x86_64")
        print(f"  Arquitetura detectada: {detect_machine} → {ttyd_arch}")

        ttyd_bin = "/usr/local/bin/ttyd"
        if os.path.exists(ttyd_bin):
            print(f"  Binário ttyd já existe: {ttyd_bin}")
            try:
                result = subprocess.run([ttyd_bin, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  Versão instalada: {result.stdout.strip()}")
            except:
                pass
            reinstalar = input("  Deseja reinstalar/atualizar? (s/n): ").strip().lower()
            if reinstalar != "s":
                print("  Usando instalação existente.")
            else:
                print("  Baixando nova versão...")
                os.remove(ttyd_bin)
        else:
            print(f"  Baixando ttyd para {ttyd_arch}...")

        if not os.path.exists(ttyd_bin):
            try:
                api_url = "https://api.github.com/repos/tsl0922/ttyd/releases/latest"
                resp = subprocess.run(
                    ["curl", "-sL", api_url],
                    capture_output=True, text=True, timeout=30
                )
                if resp.returncode == 0:
                    release_data = json.loads(resp.stdout)
                    version = release_data.get("tag_name", "1.7.7").lstrip("v")
                else:
                    version = "1.7.7"
            except Exception:
                version = "1.7.7"

            asset_name = f"ttyd.{ttyd_arch}"
            download_url = f"https://github.com/tsl0922/ttyd/releases/download/{version}/{asset_name}"

            print(f"  Versão: {version}")
            print(f"  Asset: {asset_name}")

            try:
                subprocess.run(
                    ["curl", "-fSL", "-o", "/tmp/ttyd", download_url],
                    check=True, timeout=120
                )
                print(f"  Download concluído.")

                subprocess.run(["sudo", "mv", "/tmp/ttyd", ttyd_bin], check=True)
                subprocess.run(["sudo", "chmod", "+x", ttyd_bin], check=True)
                print(f"  Binário instalado: {ttyd_bin}")
            except Exception as e:
                print(f"  Erro ao baixar ttyd: {e}")
                print("  Você pode baixar manualmente em: https://github.com/tsl0922/ttyd/releases")
                return None

        porta_web = 40000

        config_file = os.path.join(ttyd_dir, "config.json")
        usar_config_existente = False

        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    cfg = json.load(f)
                porta_web = cfg.get("porta", porta_web)
                ttyd_user = cfg.get("user", "root")
                ttyd_password = cfg.get("password", "")
                usar_config_existente = True
                print(f"  Configuração existente carregada (porta: {porta_web}).")
            except:
                ttyd_user = "root"
                ttyd_password = ""

        if not usar_config_existente:
            ttyd_user = input("\n  Usuário para acesso (padrão: root): ").strip() or "root"
            ttyd_password_input = input("  Senha (Enter para gerar automaticamente): ").strip()
            if not ttyd_password_input:
                ttyd_password = self.generate_password(16)
                print(f"  Senha gerada automaticamente: {ttyd_password}")
            else:
                ttyd_password = ttyd_password_input

            cfg = {
                "porta": porta_web,
                "user": ttyd_user,
                "password": ttyd_password,
                "versao": version if 'version' in dir() else "1.7.7",
            }
            with open(config_file, "w") as f:
                json.dump(cfg, f, indent=2)
            os.chmod(config_file, 0o600)
            print(f"  Configuração salva: {config_file}")

        print("\n  Criando serviço systemd (ttyd)...")
        service_content = textwrap.dedent(f"""\
            [Unit]
            Description=Terminal Web (ttyd) - Backend Termote
            After=network.target

            [Service]
            Type=simple
            User=root
            ExecStart={ttyd_bin} -i lo --credential {shlex.quote(ttyd_user)}:{shlex.quote(ttyd_password)} --port {porta_web} --writable tmux new-session -A -s main "bash"
            Restart=on-failure
            RestartSec=5

            [Install]
            WantedBy=multi-user.target
        """)

        temp_svc = "/tmp/ttyd.service"
        with open(temp_svc, "w") as f:
            f.write(service_content)

        subprocess.run(["sudo", "mv", temp_svc, "/etc/systemd/system/ttyd.service"], check=False)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False)
        subprocess.run(["sudo", "systemctl", "enable", "ttyd.service"], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "ttyd.service"], check=False)

        time.sleep(2)
        print("  Backend ttyd instalado e iniciado.")

        return (porta_web, ttyd_user, ttyd_password)

    def instala_termote_mobile(self):
        print("Iniciando instalação do Termote Mobile (PWA).")
        print("=" * 60)
        print("PWA mobile para terminal com toolbar virtual e gestos!")
        print("-" * 60)

        ttyd_result = self._instala_ttyd_backend()
        if ttyd_result is None:
            print(" Erro ao instalar o backend (ttyd). Abortando.")
            return
        ttyd_port, ttyd_user, ttyd_password = ttyd_result

        termote_dir = f"{self.install_principal}/termote"
        pwa_dir = os.path.join(termote_dir, "pwa")
        os.makedirs(termote_dir, exist_ok=True)
        os.makedirs(pwa_dir, exist_ok=True)
        print(f" Diretório criado: {termote_dir}")

        detect_machine = platform.machine().lower()
        arch_map = {
            "x86_64": "linux-amd64",
            "amd64": "linux-amd64",
            "aarch64": "linux-arm64",
            "arm64": "linux-arm64",
        }
        termote_arch = arch_map.get(detect_machine, "linux-amd64")
        print(f" Arquitetura detectada: {detect_machine} → {termote_arch}")

        tmux_api_bin = "/usr/local/bin/tmux-api"
        version = "0.0.15"
        try:
            api_url = "https://api.github.com/repos/lamngockhuong/termote/releases/latest"
            print(f" Consultando versão mais recente...")
            resp = subprocess.run(
                ["curl", "-sL", api_url],
                capture_output=True, text=True, timeout=30
            )
            if resp.returncode == 0 and resp.stdout.strip():
                release_data = json.loads(resp.stdout)
                version = release_data.get("tag_name", "v0.0.15").lstrip("v")
                print(f" Versão mais recente: {version}")
            else:
                print(f" Não foi possível consultar a API, usando versão {version}")
        except Exception as e:
            print(f" Erro ao consultar API: {e}, usando versão {version}")

        download_url_api = f"https://github.com/lamngockhuong/termote/releases/download/v{version}/tmux-api-{termote_arch}"
        download_url_pwa = f"https://github.com/lamngockhuong/termote/releases/download/v{version}/pwa-dist-v{version}.zip"

        if os.path.exists(tmux_api_bin):
            print(f" Binário tmux-api já existe: {tmux_api_bin}")
            reinstalar = input(" Deseja reinstalar/atualizar? (s/n): ").strip().lower()
            if reinstalar != "s":
                print(" Usando instalação existente.")
            else:
                print(" Baixando nova versão...")
                os.remove(tmux_api_bin)
        else:
            print(f" Baixando tmux-api para {termote_arch}...")

        if not os.path.exists(tmux_api_bin):
            try:
                print(f" URL: {download_url_api}")
                result = subprocess.run(
                    ["curl", "-fSL", "-o", "/tmp/tmux-api", download_url_api],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    print(f" Erro no curl: {result.stderr}")
                    return
                if not os.path.exists("/tmp/tmux-api") or os.path.getsize("/tmp/tmux-api") == 0:
                    print(" Erro: arquivo baixado está vazio ou não existe.")
                    return
                print(" Download do tmux-api concluído.")
                subprocess.run(["sudo", "mv", "/tmp/tmux-api", tmux_api_bin], check=True)
                subprocess.run(["sudo", "chmod", "+x", tmux_api_bin], check=True)
                print(f" Binário instalado: {tmux_api_bin}")
            except Exception as e:
                print(f" Erro ao baixar tmux-api: {e}")
                return

        print("\n Instalando dependências...")
        if not shutil.which("tmux"):
            print(" Instalando tmux...")
            subprocess.run(["sudo", "apt", "install", "-y", "tmux"], check=False)

        if not shutil.which("unzip"):
            print(" Instalando unzip...")
            subprocess.run(["sudo", "apt", "install", "-y", "unzip"], check=False)

        tmux_conf_content = textwrap.dedent("""\
            set-option -g destroy-unattached off
            set-option -g detach-on-destroy off
            set-option -g mouse on
            set-option -g history-limit 50000
        """)
        temp_tmux_conf = "/tmp/tmux.conf"
        with open(temp_tmux_conf, "w") as f:
            f.write(tmux_conf_content)
        subprocess.run(["sudo", "mv", temp_tmux_conf, "/etc/tmux.conf"], check=False)
        subprocess.run(["sudo", "chmod", "644", "/etc/tmux.conf"], check=False)
        print(" Configuração do tmux criada: /etc/tmux.conf")

        if not os.path.exists(os.path.join(pwa_dir, "index.html")):
            print(f" Baixando PWA dist...")
            print(f" URL: {download_url_pwa}")
            try:
                result = subprocess.run(
                    ["curl", "-fSL", "-o", "/tmp/pwa-dist.zip", download_url_pwa],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode != 0:
                    print(f" Erro no curl: {result.stderr}")
                    return
                if not os.path.exists("/tmp/pwa-dist.zip") or os.path.getsize("/tmp/pwa-dist.zip") == 0:
                    print(" Erro: arquivo PWA baixado está vazio ou não existe.")
                    return
                print(" Download da PWA concluído.")
                subprocess.run(["sudo", "rm", "-rf", pwa_dir], check=False)
                os.makedirs(pwa_dir, exist_ok=True)
                result_unzip = subprocess.run(
                    ["sudo", "unzip", "-o", "/tmp/pwa-dist.zip", "-d", pwa_dir],
                    capture_output=True, text=True, timeout=30
                )
                if result_unzip.returncode != 0:
                    print(f" Erro no unzip: {result_unzip.stderr}")
                    return
                subprocess.run(["sudo", "rm", "-f", "/tmp/pwa-dist.zip"], check=False)
                print(f" PWA extraída em: {pwa_dir}")
            except Exception as e:
                print(f" Erro ao baixar PWA: {e}")
                return
        else:
            print(" PWA já está instalada.")

        porta_termote = 7680

        config_file = os.path.join(termote_dir, "config.json")
        usar_config_existente = False

        if os.path.exists(config_file):
            print("\n⚠️  Arquivo de configuração já existe!")
            resposta = input(" Deseja usar as configurações existentes? (s/n) [padrão: s]: ").strip().lower()
            if resposta != "n":
                usar_config_existente = True
                print("✅ Usando configurações existentes.")
                try:
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                    porta_termote = cfg.get("porta", 7680)
                    termote_user = cfg.get("user", ttyd_user)
                    termote_password = cfg.get("password", ttyd_password)
                except:
                    termote_user = ttyd_user
                    termote_password = ttyd_password
            else:
                print(" Novas configurações serão solicitadas.")

        if not usar_config_existente:
            print(f"\n Usando as credenciais do backend: {ttyd_user}")
            termote_user = ttyd_user
            termote_password = ttyd_password
            alterar_cred = input(" Deseja usar credenciais diferentes para o Termote? (s/n) [padrão: n]: ").strip().lower()
            if alterar_cred == "s":
                termote_user = input("  Usuário para acesso (padrão: root): ").strip() or "root"
                termote_pass_input = input("  Senha (Enter para gerar automaticamente): ").strip()
                if not termote_pass_input:
                    termote_password = self.generate_password(16)
                    print(f"  Senha gerada automaticamente: {termote_password}")
                else:
                    termote_password = termote_pass_input

            expor_lan = input("\n Expor na rede local (LAN)? (s/n) [padrão: s]: ").strip().lower()
            if expor_lan == "n":
                listen_addr = "127.0.0.1"
                print(" Acessível apenas localmente (localhost).")
            else:
                listen_addr = "0.0.0.0"
                print(" Acessível pela rede local.")

            cfg = {
                "porta": porta_termote,
                "user": termote_user,
                "password": termote_password,
                "versao": version,
                "listen": listen_addr,
                "ttyd_port": ttyd_port,
            }
            with open(config_file, "w") as f:
                json.dump(cfg, f, indent=2)
            os.chmod(config_file, 0o600)
            print(f" Configuração salva: {config_file}")
        else:
            try:
                with open(config_file, "r") as f:
                    cfg = json.load(f)
                listen_addr = cfg.get("listen", "0.0.0.0")
            except:
                listen_addr = "0.0.0.0"

        print("\n Criando script wrapper e configurando tmux...")
        
        # Prepara credenciais para URL (com encoding se necessário)
        ttyd_url_auth = ""
        if ttyd_password:
            from urllib.parse import quote
            ttyd_url_auth = f"{quote(ttyd_user, safe='')}:{quote(ttyd_password, safe='')}@"

        wrapper_script = "/usr/local/bin/termote-start.sh"

        wrapper_content = textwrap.dedent(f"""\
            #!/bin/bash
            # Wrapper para iniciar o Termote com ambiente correto
            # Nota: variáveis de ambiente já são injetadas pelo systemd

            export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

            # Garante sessão tmux 'main' (-dA = detached + attach se existe, cria se não)
            tmux new-session -d -A -s main "bash" 2>/dev/null || true

            # Inicia o tmux-api
            exec {tmux_api_bin}
        """)
        
        with open("/tmp/termote-start.sh", "w") as f:
            f.write(wrapper_content)
        subprocess.run(["sudo", "mv", "/tmp/termote-start.sh", wrapper_script], check=True)
        subprocess.run(["sudo", "chmod", "+x", wrapper_script], check=True)
        print(f" Script wrapper criado: {wrapper_script}")
        
        # Cria sessão tmux 'main' inicial
        try:
            subprocess.run(["tmux", "new-session", "-A", "-s", "main", "bash"], check=False)
            print(" Sessão tmux 'main' criada ou reutilizada.")
        except:
            pass

        print("\n Criando serviço systemd...")
        service_content = textwrap.dedent(f"""\
            [Unit]
            Description=Termote Mobile PWA (tmux-api)
            After=network.target ttyd.service
            Wants=ttyd.service

            [Service]
            Type=simple
            User=root
            Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
            Environment=TERMOTE_PORT={porta_termote}
            Environment=TERMOTE_PWA_DIR={pwa_dir}
            Environment=TERMOTE_TTYD_URL=http://{ttyd_url_auth}127.0.0.1:{ttyd_port}
            Environment=TERMOTE_USER={shlex.quote(termote_user)}
            Environment=TERMOTE_PASS={shlex.quote(termote_password)}
            Environment=TERMOTE_BIND={listen_addr}
            ExecStart=/usr/local/bin/termote-start.sh
            Restart=on-failure
            RestartSec=5
            KillMode=process

            [Install]
            WantedBy=multi-user.target
        """)

        temp_svc = "/tmp/termote.service"
        with open(temp_svc, "w") as f:
            f.write(service_content)

        subprocess.run(["sudo", "mv", temp_svc, "/etc/systemd/system/termote.service"], check=False)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False)
        subprocess.run(["sudo", "systemctl", "enable", "termote.service"], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "termote.service"], check=False)

        print("\n Configurando firewall...")
        try:
            ufw_check = subprocess.run(
                ["sudo", "ufw", "status"],
                capture_output=True, text=True, timeout=10
            )
            if "active" in ufw_check.stdout.lower():
                subprocess.run(
                    ["sudo", "ufw", "allow", str(porta_termote), "tcp"],
                    capture_output=True, text=True, timeout=10
                )
                print(f"✔ Porta {porta_termote} liberada no UFW")
        except Exception:
            pass

        try:
            check_iptables = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta_termote), "-j", "ACCEPT"],
                capture_output=True, timeout=10
            )
            if check_iptables.returncode == 0:
                print(f"  Porta {porta_termote} já liberada no iptables")
            else:
                subprocess.run(
                    ["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(porta_termote), "-j", "ACCEPT"],
                    capture_output=True, timeout=10
                )
                print(f"✔ Porta {porta_termote} liberada no iptables (inserida no topo da cadeia)")

                if shutil.which("netfilter-persistent"):
                    subprocess.run(
                        ["sudo", "netfilter-persistent", "save"],
                        capture_output=True, timeout=10
                    )
                elif shutil.which("iptables-save"):
                    subprocess.run(
                        ["sudo", "sh", "-c", "iptables-save > /etc/iptables.rules"],
                        capture_output=True, timeout=10
                    )
                print("  Regras salvas em /etc/iptables.rules")
        except Exception as e:
            print(f"  ⚠️  Não foi possível configurar iptables: {e}")

        time.sleep(2)

        print("\n" + "=" * 60)
        print(" Instalação do Termote Mobile (PWA) concluída!")
        print("=" * 60)
        print("\n IPs possíveis para acesso:")
        self.executar_comandos(["hostname -I | tr ' ' '\\n'"], exibir_executando=False)
        print(f"\n Endereço PWA: http://<seu_ip>:{porta_termote}")
        print(f" Usuário: {termote_user}")
        print(f" Senha: {termote_password}")
        print(f"\n Porta: {porta_termote}")
        print("\n📱 Recursos Mobile:")
        print("   ✅ Toolbar virtual: Tab, Esc, Ctrl, Shift, Setas")
        print("   ✅ Gestos: Swipe ← = Ctrl+C, Swipe → = Tab")
        print("   ✅ Pinch-to-zoom funcional (recalcula colunas)")
        print("   ✅ PWA instalável na homescreen")
        print("   ✅ Múltiplas sessões tmux persistentes")
        print("\n💡 Sessões persistentes: suas sessões tmux continuam rodando")
        print("   mesmo quando você fecha o navegador. Ao reabrir, volta onde parou!")
        print("   Use o botão '+' para criar novas sessões.")
        print("\n💡 No celular, adicione à tela inicial para experiência full-screen!")
        print("\n🔧 Comandos úteis:")
        print("   status:  sudo systemctl status termote")
        print("   stop:    sudo systemctl stop termote")
        print("   start:   sudo systemctl start termote")
        print("   restart: sudo systemctl restart termote")
        print("   logs:    sudo journalctl -u termote -f")
        print("\n Guarde a senha! Ela não será exibida novamente.")
        print("=" * 60)
