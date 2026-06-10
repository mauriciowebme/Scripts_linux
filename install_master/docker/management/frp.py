import os
import subprocess
import json
import time
import platform
import textwrap

from install_master.core.docker_base import DockerBase


class MixinFRP(DockerBase):

    def instala_frp_server(self):
        print("Iniciando instalação do frp server (reverse proxy).")
        print("=" * 60)

        frp_dir = f"{self.install_principal}/frp/server"
        os.makedirs(frp_dir, exist_ok=True)

        frps_conf = os.path.join(frp_dir, "frps.toml")
        dashboard_password = self.generate_password(32)

        if not os.path.exists(frps_conf):
            with open(frps_conf, "w") as f:
                f.write(textwrap.dedent(f"""\
                    bindPort = 7000

                    vhostHTTPPort = 80
                    vhostHTTPSPort = 443

                    webServer.addr = "0.0.0.0"
                    webServer.port = 7500
                    webServer.user = "admin"
                    webServer.password = "{dashboard_password}"

                    log.to = "{frp_dir}/frps.log"
                    log.level = "info"
                    log.maxDays = 7
                """))
            print(f" Arquivo de configuração criado: {frps_conf}")
        else:
            print(f" Arquivo de configuração já existe: {frps_conf}")

        self.remove_container("frp_server")

        comandos = [
            f"""docker run -d \\
                --name frp_server \\
                --restart=unless-stopped \\
                --memory=64m \\
                --cpus=0.5 \\
                -p 7000:7000 \\
                -p 7500:7500 \\
                -p 80:80 \\
                -p 443:443 \\
                -v {frps_conf}:/etc/frp/frps.toml \\
                ghcr.io/fatedier/frps:latest
            """
        ]
        self.executar_comandos(comandos)
        time.sleep(5)

        print("\n" + "=" * 60)
        print(" Instalação do frp server concluída!")
        print("=" * 60)
        print("\n IPs possíveis para acesso:")
        self.executar_comandos(["hostname -I | tr ' ' '\\n'"], exibir_executando=False)
        print(f"\n Dashboard: http://<seu_ip>:7500")
        print(f" Usuario: admin")
        print(f" Senha: {dashboard_password}")
        print(f"\n Porta do servidor frp: 7000")
        print(f" Portas HTTP/HTTPS: 80 / 443")
        print("\n Guarde a senha do dashboard! Ela não será exibida novamente.")
        print("=" * 60)

    def instala_frp_client(self):
        print("Iniciando instalação do frp client (tunnel local).")
        print("=" * 60)

        detect_system = platform.system().lower()
        detect_machine = platform.machine().lower()

        arch_map = {
            "x86_64": "amd64",
            "amd64": "amd64",
            "aarch64": "arm64",
            "arm64": "arm64",
            "armv7l": "arm",
            "armv6l": "arm",
        }
        frp_arch = arch_map.get(detect_machine, "amd64")

        if detect_system == "windows":
            os_name = "windows"
            ext = ".zip"
            bin_name = "frpc.exe"
        else:
            os_name = "linux"
            ext = ".tar.gz"
            bin_name = "frpc"

        frp_dir = f"{self.install_principal}/frp/client"
        os.makedirs(frp_dir, exist_ok=True)
        frpc_bin = os.path.join(frp_dir, bin_name)
        frpc_conf = os.path.join(frp_dir, "frpc.toml")

        if os.path.exists(frpc_bin):
            print(f" Binário já existe: {frpc_bin}")
        else:
            print(f" Baixando frp client para {os_name}/{frp_arch}...")
            try:
                api_url = "https://api.github.com/repos/fatedier/frp/releases/latest"
                resp = subprocess.run(
                    ["curl", "-sL", api_url],
                    capture_output=True, text=True, timeout=30
                )
                if resp.returncode == 0:
                    import json as _json
                    release_data = _json.loads(resp.stdout)
                    version = release_data.get("tag_name", "v0.61.1").lstrip("v")
                else:
                    version = "0.61.1"
            except Exception:
                version = "0.61.1"

            asset_name = f"frp_{version}_{os_name}_{frp_arch}{ext}"
            download_url = f"https://github.com/fatedier/frp/releases/download/v{version}/{asset_name}"
            archive_path = os.path.join(frp_dir, asset_name)

            print(f" Versão: {version}")
            print(f" Asset: {asset_name}")

            try:
                subprocess.run(
                    ["curl", "-fSL", "-o", archive_path, download_url],
                    check=True, timeout=120
                )
                print(f" Download concluído.")

                if ext == ".zip":
                    subprocess.run(
                        ["unzip", "-o", archive_path, "-d", frp_dir],
                        check=True, timeout=30
                    )
                else:
                    subprocess.run(
                        ["tar", "-xzf", archive_path, "-C", frp_dir,
                         "--strip-components=1",
                         f"frp_{version}_{os_name}_{frp_arch}/{bin_name}"],
                        check=True, timeout=30
                    )

                if os.path.exists(archive_path):
                    os.remove(archive_path)

                if os_name == "linux":
                    os.chmod(frpc_bin, 0o755)

                print(f" Binário extraído: {frpc_bin}")
            except Exception as e:
                print(f" Erro ao baixar/extrair frp: {e}")
                print(" Você pode baixar manualmente em: https://github.com/fatedier/frp/releases")
                return

        server_addr = input("\n IP ou domínio do servidor frp: ").strip()
        if not server_addr:
            print(" Endereço do servidor é obrigatório.")
            return

        proxies = []
        while True:
            print("\n Tipo de proxy:")
            print(" 1 - TCP  (qualquer serviço TCP: SSH, DB, RDP)")
            print(" 2 - HTTP (site web)")
            print(" 3 - HTTPS (site com TLS)")
            print(" 4 - UDP  (DNS, jogos, etc)")
            tipo_choice = input(" Escolha (1-4): ").strip()

            tipo_map = {"1": "tcp", "2": "http", "3": "https", "4": "udp"}
            proxy_type = tipo_map.get(tipo_choice, "tcp")

            proxy_name = input(" Nome do proxy (ex: meu-site, ssh-tunnel): ").strip()
            if not proxy_name:
                proxy_name = f"{proxy_type}-{len(proxies) + 1}"

            local_port = input(" Porta local (ex: 8080): ").strip()
            if not local_port:
                print(" Porta local é obrigatória.")
                continue

            proxy_conf = {
                "name": proxy_name,
                "type": proxy_type,
                "localIP": "127.0.0.1",
                "localPort": int(local_port),
            }

            if proxy_type in ("tcp", "udp"):
                remote_port = input(" Porta remota no servidor (ex: 8080): ").strip()
                if remote_port:
                    proxy_conf["remotePort"] = int(remote_port)
                else:
                    proxy_conf["remotePort"] = int(local_port)
            elif proxy_type in ("http", "https"):
                domain = input(" Domínio (ex: app.seudominio.com): ").strip()
                if domain:
                    proxy_conf["customDomains"] = [domain]

            proxies.append(proxy_conf)
            print(f" Proxy '{proxy_name}' ({proxy_type}) adicionado.")

            mais = input(" Adicionar outro proxy? (s/n): ").strip().lower()
            if mais != "s":
                break

        if not os.path.exists(frpc_conf):
            frpc_content = f'serverAddr = "{server_addr}"\nserverPort = 7000\n\n'
            for p in proxies:
                frpc_content += "[[proxies]]\n"
                for k, v in p.items():
                    if isinstance(v, list):
                        frpc_content += f'{k} = {json.dumps(v)}\n'
                    elif isinstance(v, str):
                        frpc_content += f'{k} = "{v}"\n'
                    else:
                        frpc_content += f"{k} = {v}\n"
                frpc_content += "\n"

            with open(frpc_conf, "w") as f:
                f.write(frpc_content)
            os.chmod(frpc_conf, 0o600)
            print(f" Configuração salva: {frpc_conf}")
        else:
            print(f" Configuração já existe: {frpc_conf}")
            sobrescrever = input(" Sobrescrever? (s/n): ").strip().lower()
            if sobrescrever == "s":
                frpc_content = f'serverAddr = "{server_addr}"\nserverPort = 7000\n\n'
                for p in proxies:
                    frpc_content += "[[proxies]]\n"
                    for k, v in p.items():
                        if isinstance(v, list):
                            frpc_content += f'{k} = {json.dumps(v)}\n'
                        elif isinstance(v, str):
                            frpc_content += f'{k} = "{v}"\n'
                        else:
                            frpc_content += f"{k} = {v}\n"
                    frpc_content += "\n"
                with open(frpc_conf, "w") as f:
                    f.write(frpc_content)
                os.chmod(frpc_conf, 0o600)
                print(f" Configuração atualizada: {frpc_conf}")

        if detect_system == "linux":
            print("\n Configurando serviço systemd...")
            service_content = textwrap.dedent(f"""\
                [Unit]
                Description=frp client
                After=network.target

                [Service]
                Type=simple
                User=root
                ExecStart={frpc_bin} -c {frpc_conf}
                Restart=on-failure
                RestartSec=5
                StartLimitBurst=5
                StartLimitInterval=60

                [Install]
                WantedBy=multi-user.target
            """)

            temp_svc = "/tmp/frpc.service"
            with open(temp_svc, "w") as f:
                f.write(service_content)

            subprocess.run(["sudo", "mv", temp_svc, "/etc/systemd/system/frpc.service"], check=False)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False)
            subprocess.run(["sudo", "systemctl", "enable", "frpc.service"], check=False)
            subprocess.run(["sudo", "systemctl", "restart", "frpc.service"], check=False)

            print(" Serviço frpc habilitado e iniciado.")
        elif detect_system == "windows":
            bat_path = os.path.join(frp_dir, "start_frpc.bat")
            with open(bat_path, "w") as f:
                f.write(f'@echo off\n"{frpc_bin}" -c "{frpc_conf}"\n')
            print(f"\n Script criado: {bat_path}")
            print(" Execute manualmente ou agende no Task Scheduler.")

        print("\n" + "=" * 60)
        print(" Instalação do frp client concluída!")
        print("=" * 60)
        print(f"\n Servidor: {server_addr}")
        print(f" Proxies configurados: {len(proxies)}")
        for p in proxies:
            print(f"  - {p['name']} ({p['type']}) :{p['localPort']}")
        print("\n Para verificar status:")
        if detect_system == "linux":
            print("  systemctl status frpc")
            print("  journalctl -u frpc -f")
        else:
            print(f"  Execute: {bat_path}")
        print("=" * 60)

    def gerenciar_frp(self):
        print("\n=== GERENCIAMENTO FRP (Fast Reverse Proxy) ===\n")

        frp_dir = f"{self.install_principal}/frp"
        frps_conf = os.path.join(frp_dir, "server", "frps.toml")
        frpc_conf = os.path.join(frp_dir, "client", "frpc.toml")

        while True:
            print("\n[1] ➕ Adicionar proxy")
            print("[2] ➖  Remover proxy")
            print("[3] 📋  Listar proxies")
            print("[4] 🖥️  Status do servidor (frps)")
            print("[5]  Status do cliente (frpc)")
            print("[6] 🔑  Ver credenciais do dashboard")
            print("[0] ↩️  Voltar")

            opcao = input("\nEscolha uma opção: ").strip()

            if opcao == "1":
                self._frp_adicionar_proxy(frpc_conf)
            elif opcao == "2":
                self._frp_remover_proxy(frpc_conf)
            elif opcao == "3":
                self._frp_listar_proxies(frpc_conf)
            elif opcao == "4":
                self._frp_status_server()
            elif opcao == "5":
                self._frp_status_client()
            elif opcao == "6":
                self._frp_ver_dashboard(frps_conf)
            elif opcao == "0":
                break
            else:
                print(" Opção inválida.")

    def _frp_adicionar_proxy(self, frpc_conf):
        if not os.path.exists(frpc_conf):
            print(" Arquivo frpc.toml não encontrado. Instale o frp client primeiro.")
            return

        server_addr = ""
        with open(frpc_conf, "r") as f:
            for line in f:
                if line.startswith("serverAddr"):
                    server_addr = line.split("=")[1].strip().strip('"')
                    break

        print("\n Tipo de proxy:")
        print(" 1 - TCP  (qualquer serviço TCP: SSH, DB, RDP)")
        print(" 2 - HTTP (site web)")
        print(" 3 - HTTPS (site com TLS)")
        print(" 4 - UDP  (DNS, jogos, etc)")
        tipo_choice = input(" Escolha (1-4): ").strip()

        tipo_map = {"1": "tcp", "2": "http", "3": "https", "4": "udp"}
        proxy_type = tipo_map.get(tipo_choice, "tcp")

        proxy_name = input(" Nome do proxy: ").strip()
        if not proxy_name:
            proxy_name = f"{proxy_type}-novo"

        local_port = input(" Porta local: ").strip()
        if not local_port:
            print(" Porta local é obrigatória.")
            return

        proxy_conf = {
            "name": proxy_name,
            "type": proxy_type,
            "localIP": "127.0.0.1",
            "localPort": int(local_port),
        }

        if proxy_type in ("tcp", "udp"):
            remote_port = input(" Porta remota no servidor: ").strip()
            if remote_port:
                proxy_conf["remotePort"] = int(remote_port)
            else:
                proxy_conf["remotePort"] = int(local_port)
        elif proxy_type in ("http", "https"):
            domain = input(" Domínio: ").strip()
            if domain:
                proxy_conf["customDomains"] = [domain]

        with open(frpc_conf, "a") as f:
            f.write("\n[[proxies]]\n")
            for k, v in proxy_conf.items():
                if isinstance(v, list):
                    f.write(f'{k} = {json.dumps(v)}\n')
                elif isinstance(v, str):
                    f.write(f'{k} = "{v}"\n')
                else:
                    f.write(f"{k} = {v}\n")

        print(f" Proxy '{proxy_name}' adicionado.")

        detect_system = platform.system().lower()
        if detect_system == "linux":
            restart = input(" Reiniciar frpc agora? (s/n): ").strip().lower()
            if restart == "s":
                subprocess.run(["sudo", "systemctl", "restart", "frpc.service"], check=False)
                print(" frpc reiniciado.")
        else:
            print(" Reinicie o frpc manualmente para aplicar as mudanças.")

    def _frp_remover_proxy(self, frpc_conf):
        if not os.path.exists(frpc_conf):
            print(" Arquivo frpc.toml não encontrado.")
            return

        with open(frpc_conf, "r") as f:
            content = f.read()

        proxies = []
        current = None
        for line in content.splitlines():
            if line.strip() == "[[proxies]]":
                if current:
                    proxies.append(current)
                current = {"_raw": ""}
            if current is not None:
                current["_raw"] += line + "\n"
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if v.startswith("["):
                        import ast as _ast
                        try:
                            current[k] = _ast.literal_eval(v)
                        except Exception:
                            current[k] = v
                    elif v.startswith('"'):
                        current[k] = v.strip('"')
                    else:
                        try:
                            current[k] = int(v)
                        except ValueError:
                            current[k] = v
        if current:
            proxies.append(current)

        if not proxies:
            print(" Nenhum proxy configurado.")
            return

        print("\n Proxies existentes:")
        for i, p in enumerate(proxies, 1):
            nome = p.get("name", f"proxy-{i}")
            tipo = p.get("type", "tcp")
            porta = p.get("localPort", "?")
            print(f"  [{i}] {nome} ({tipo}) :{porta}")

        escolha = input("\n Número do proxy para REMOVER (0 para cancelar): ").strip()
        if escolha == "0" or not escolha:
            return

        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(proxies):
                removido = proxies.pop(idx)

                server_lines = []
                with open(frpc_conf, "r") as f:
                    for line in f:
                        if line.startswith("serverAddr") or line.startswith("serverPort"):
                            server_lines.append(line.rstrip())

                with open(frpc_conf, "w") as f:
                    for line in server_lines:
                        f.write(line + "\n")
                    for p in proxies:
                        f.write("\n[[proxies]]\n")
                        for k, v in p.items():
                            if k == "_raw":
                                continue
                            if isinstance(v, list):
                                f.write(f'{k} = {json.dumps(v)}\n')
                            elif isinstance(v, str):
                                f.write(f'{k} = "{v}"\n')
                            else:
                                f.write(f"{k} = {v}\n")

                print(f" Proxy '{removido.get('name', 'desconhecido')}' removido.")

                detect_system = platform.system().lower()
                if detect_system == "linux":
                    restart = input(" Reiniciar frpc agora? (s/n): ").strip().lower()
                    if restart == "s":
                        subprocess.run(["sudo", "systemctl", "restart", "frpc.service"], check=False)
                        print(" frpc reiniciado.")
            else:
                print(" Número inválido.")
        except ValueError:
            print(" Entrada inválida.")

    def _frp_listar_proxies(self, frpc_conf):
        if not os.path.exists(frpc_conf):
            print(" Arquivo frpc.toml não encontrado.")
            return

        with open(frpc_conf, "r") as f:
            content = f.read()

        print("\n=== PROXIES CONFIGURADOS ===\n")
        current = None
        count = 0
        for line in content.splitlines():
            if line.strip() == "[[proxies]]":
                if current:
                    count += 1
                    print(f"  {count}. {current.get('name', '?')} ({current.get('type', '?')})")
                    if "localPort" in current:
                        print(f"     Porta local: {current['localPort']}")
                    if "remotePort" in current:
                        print(f"     Porta remota: {current['remotePort']}")
                    if "customDomains" in current:
                        print(f"     Domínio: {', '.join(current['customDomains'])}")
                    print()
                current = {}
            elif current is not None and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if v.startswith("["):
                    import ast as _ast
                    try:
                        current[k] = _ast.literal_eval(v)
                    except Exception:
                        current[k] = v
                elif v.startswith('"'):
                    current[k] = v.strip('"')
                else:
                    try:
                        current[k] = int(v)
                    except ValueError:
                        current[k] = v
        if current:
            count += 1
            print(f"  {count}. {current.get('name', '?')} ({current.get('type', '?')})")
            if "localPort" in current:
                print(f"     Porta local: {current['localPort']}")
            if "remotePort" in current:
                print(f"     Porta remota: {current['remotePort']}")
            if "customDomains" in current:
                print(f"     Domínio: {', '.join(current['customDomains'])}")
            print()

        if count == 0:
            print("  Nenhum proxy configurado.")

    def _frp_status_server(self):
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=frp_server", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True, text=True
            )
            output = result.stdout.strip()
            if output:
                print(f"\n frp_server: {output}")
            else:
                print("\n frp_server: NÃO ESTÁ RODANDO")
                print(" Execute: instala_frp_server")
        except Exception as e:
            print(f" Erro ao verificar status: {e}")

    def _frp_status_client(self):
        detect_system = platform.system().lower()
        if detect_system == "linux":
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", "frpc.service"],
                capture_output=True, text=True
            )
            status = result.stdout.strip()
            if status == "active":
                print("\n frpc: ATIVO")
            else:
                print(f"\n frpc: {status or 'NÃO ESTÁ RODANDO'}")
        else:
            print("\n No Windows, verifique manualmente:")
            print("  tasklist | findstr frpc")

    def _frp_ver_dashboard(self, frps_conf):
        if not os.path.exists(frps_conf):
            print(" Arquivo frps.toml não encontrado. Instale o frp server primeiro.")
            return

        password = ""
        with open(frps_conf, "r") as f:
            for line in f:
                if line.startswith("webServer.password"):
                    password = line.split("=")[1].strip().strip('"')
                    break

        print("\n=== DASHBOARD FRP ===\n")
        print(" IPs possíveis:")
        self.executar_comandos(["hostname -I | tr ' ' '\\n'"], exibir_executando=False)
        print(f"\n URL: http://<seu_ip>:7500")
        print(f" Usuario: admin")
        print(f" Senha: {password}")
