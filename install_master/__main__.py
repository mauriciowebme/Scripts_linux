import os
import subprocess
import textwrap
import time
import json
import shlex

from install_master.core.docker_base import DockerBase
from install_master.core.system_utils import check_for_update
from install_master.core.deps import instalar_dependencias

from install_master.docker.databases.postgres import MixinPostgres
from install_master.docker.databases.mysql import MixinMySQL
from install_master.docker.web.traefik import MixinTraefik
from install_master.docker.web.wordpress import MixinWordPress
from install_master.docker.web.openlitespeed import MixinOpenLiteSpeed
from install_master.docker.web.nodejs import MixinNodeJS
from install_master.docker.tools.n8n import MixinN8N
from install_master.docker.tools.monitoring import MixinMonitoring
from install_master.docker.tools.portainer import MixinPortainer
from install_master.docker.tools.filebrowser import MixinFileBrowser
from install_master.docker.tools.rustdesk import MixinRustdesk
from install_master.docker.tools.redis import MixinRedis
from install_master.docker.tools.sftp import MixinSFTP
from install_master.docker.tools.vpn import MixinVPN
from install_master.docker.tools.guacamole import MixinGuacamole
from install_master.docker.tools.ide import MixinIDE
from install_master.docker.tools.whatsapp import MixinWhatsApp
from install_master.docker.tools.ia import MixinIA
from install_master.docker.tools.selenium import MixinSelenium
from install_master.docker.tools.browserless import MixinBrowserless
from install_master.docker.tools.rclone import MixinRclone
from install_master.docker.tools.opencode import MixinOpenCode
from install_master.docker.tools.sync import MixinSync
from install_master.docker.tools.terminal import MixinTerminal
from install_master.docker.vms.sistema_ciso import MixinSistemaCISO
from install_master.docker.vms.windows_kvm import MixinWindowsKVM
from install_master.docker.vms.ubuntu_container import MixinUbuntuContainer
from install_master.docker.vms.webtop import MixinWebtop
from install_master.docker.vms.nextcloud import MixinNextcloud
from install_master.docker.management.docker_install import MixinDockerInstall
from install_master.docker.management.docker_ops import MixinDockerOps
from install_master.docker.management.frp import MixinFRP
from install_master.system.base import MixinBase
from install_master.system.updates import MixinUpdates
from install_master.system.diagnostic import MixinDiagnostic
from install_master.system.linux_commands import MixinLinuxCommands
from install_master.system.network import MixinNetwork
from install_master.system.partitions import MixinPartitions
from install_master.system.wireguard import MixinWireguard
from install_master.system.tunnels import MixinTunnels
from install_master.system.interfaces import MixinInterfaces
from install_master.system.services import MixinServices
from install_master.system.ollama import MixinOllama


class Sistema(
    MixinTunnels,
    MixinFRP,
    MixinWireguard,
    MixinNetwork,
    MixinPartitions,
    MixinInterfaces,
    MixinServices,
    MixinOllama,
    MixinDiagnostic,
    MixinLinuxCommands,
    MixinUpdates,
    MixinBase,
    MixinDockerOps,
    MixinDockerInstall,
    MixinN8N,
    MixinMonitoring,
    MixinPortainer,
    MixinFileBrowser,
    MixinRustdesk,
    MixinGuacamole,
    MixinRedis,
    MixinSFTP,
    MixinVPN,
    MixinIDE,
    MixinWhatsApp,
    MixinIA,
    MixinSelenium,
    MixinBrowserless,
    MixinRclone,
    MixinOpenCode,
    MixinSync,
    MixinTerminal,
    MixinTraefik,
    MixinWordPress,
    MixinOpenLiteSpeed,
    MixinNodeJS,
    MixinPostgres,
    MixinMySQL,
    MixinSistemaCISO,
    MixinWindowsKVM,
    MixinUbuntuContainer,
    MixinWebtop,
    MixinNextcloud,
    DockerBase,
):
    def __init__(self):
        super().__init__()

    def configura_rede(self):
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

    def ecaminhamentos_portas_tuneis(self):
        print("\n" + "=" * 60)
        print("🔗 Encaminhamentos de Portas / Túneis SSH")
        print("=" * 60)

        print("\n📖 TÚNEL REVERSO (servidor → máquina local):")
        print("   ssh -R 180:localhost:80 usuario@servidor")
        print("   → Porta 180 do servidor → localhost:80 da sua máquina")

        print("\n📖 TÚNEL DIRETO (máquina local → servidor):")
        print("   ssh -L 17080:localhost:7080 usuario@servidor")
        print("   → Porta 17080 local → localhost:7080 do servidor")

        print("\n🔍 Listar túneis ativos:")
        print("   ps aux | grep 'ssh -fN -R'")

        print("\n❌ Matar todos os túneis:")
        print("   pkill -f 'ssh -fN -R'")

        print("\n⚙️  Habilitar túneis no SSH server:")
        print("   1. Backup: sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak")
        print("   2. Editar: sudo nano /etc/ssh/sshd_config")
        print("   3. Alterar:")
        print("      GatewayPorts yes")
        print("      PermitRootLogin yes")
        print("   4. Reiniciar: sudo systemctl restart ssh")

        print("\n" + "=" * 60)
        print("💡 Use o menu '🔗 Gerenciar Túneis SSH' para configuração automática!")
        print("=" * 60)
        input("\nPressione Enter para continuar...")

    def submenu_editores(self):
        opcoes = [
            ("📦  Instalar VSCode Oficial", self.instala_vscode_oficial),
            ("📦  Instalar OpenVSCode (Server)", self.instala_openvscode),
            ("↩️  Voltar", None)
        ]
        self.mostrar_menu_paginado(opcoes, titulo=" EDITORES DE CÓDIGO", itens_por_pagina=10)

    def gerenciar_terminal_web(self):
        print("\n=== GERENCIAMENTO DO TERMINAL WEB (ttyd) ===\n")

        ttyd_bin = "/usr/local/bin/ttyd"
        config_file = f"{self.install_principal}/ttyd/config.json"

        while True:
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", "is-active", "ttyd.service"],
                    capture_output=True, text=True
                )
                status = result.stdout.strip()
                if status == "active":
                    status_icon = "🟢 ATIVO"
                else:
                    status_icon = "🔴 INATIVO"
            except Exception:
                status_icon = "⚪ NÃO INSTALADO"

            print(f"Status: {status_icon}")

            if os.path.exists(config_file):
                try:
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                    print(f"Porta: {cfg.get('porta', 'N/A')}")
                    print(f"Usuário: {cfg.get('user', 'N/A')}")
                except Exception:
                    pass

            print("\n" + "-" * 55)
            print("[1] ▶️  Iniciar ttyd")
            print("[2] ⏹️  Parar ttyd")
            print("[3] 🔄  Reiniciar ttyd")
            print("[4] 📊  Ver status detalhado")
            print("[5] 📄  Ver logs")
            print("[6] 🔑  Alterar senha")
            print("[7] 🔌  Alterar porta")
            print("[0] ↩️  Voltar")
            print("=" * 55)

            opcao = input("\nEscolha: ").strip()

            if opcao == "1":
                print("\n Iniciando ttyd...")
                subprocess.run(["sudo", "systemctl", "start", "ttyd.service"], check=False)
                time.sleep(1)
                subprocess.run(["sudo", "systemctl", "status", "ttyd.service", "--no-pager"], check=False)
                input("\nPressione Enter para continuar...")

            elif opcao == "2":
                print("\n Parando ttyd...")
                subprocess.run(["sudo", "systemctl", "stop", "ttyd.service"], check=False)
                input("\nPressione Enter para continuar...")

            elif opcao == "3":
                print("\n Reiniciando ttyd...")
                subprocess.run(["sudo", "systemctl", "restart", "ttyd.service"], check=False)
                time.sleep(1)
                subprocess.run(["sudo", "systemctl", "status", "ttyd.service", "--no-pager"], check=False)
                input("\nPressione Enter para continuar...")

            elif opcao == "4":
                print("\n Status detalhado:")
                subprocess.run(["sudo", "systemctl", "status", "ttyd.service", "--no-pager"], check=False)
                input("\nPressione Enter para continuar...")

            elif opcao == "5":
                print("\n Logs recentes (Ctrl+C para sair):")
                subprocess.run(["sudo", "journalctl", "-u", "ttyd.service", "-n", "50", "--no-pager"], check=False)
                input("\nPressione Enter para continuar...")

            elif opcao == "6":
                if not os.path.exists(config_file):
                    print(" Arquivo de configuração não encontrado.")
                    input("\nPressione Enter para continuar...")
                    continue

                try:
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                    ttyd_user = cfg.get("user", "root")
                    print(f"\n Usuário atual: {ttyd_user}")
                except Exception:
                    ttyd_user = "root"

                nova_senha = input(" Nova senha (Enter para gerar automaticamente): ").strip()
                if not nova_senha:
                    nova_senha = self.generate_password(16)
                    print(f" Senha gerada: {nova_senha}")

                cfg["password"] = nova_senha
                with open(config_file, "w") as f:
                    json.dump(cfg, f, indent=2)
                os.chmod(config_file, 0o600)

                print("\n Atualizando serviço com nova senha...")
                service_content = textwrap.dedent(f"""\
                    [Unit]
                    Description=Terminal Web (ttyd)
                    After=network.target

                    [Service]
                    Type=simple
                    User=root
                    ExecStart={ttyd_bin} --credential {shlex.quote(ttyd_user)}:{shlex.quote(nova_senha)} --port {cfg.get('porta', 7681)} --writable tmux new-session -A -s main "bash"
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
                subprocess.run(["sudo", "systemctl", "restart", "ttyd.service"], check=False)

                print(" Senha atualizada e serviço reiniciado!")
                input("\nPressione Enter para continuar...")

            elif opcao == "7":
                if not os.path.exists(config_file):
                    print(" Arquivo de configuração não encontrado.")
                    input("\nPressione Enter para continuar...")
                    continue

                try:
                    with open(config_file, "r") as f:
                        cfg = json.load(f)
                    porta_atual = cfg.get("porta", 7681)
                    ttyd_user = cfg.get("user", "root")
                    ttyd_password = cfg.get("password", "")
                except Exception:
                    porta_atual = 7681
                    ttyd_user = "root"
                    ttyd_password = ""

                print(f" Porta atual: {porta_atual}")
                nova_porta = input(" Nova porta (Enter para manter): ").strip()
                if nova_porta:
                    cfg["porta"] = int(nova_porta)
                    with open(config_file, "w") as f:
                        json.dump(cfg, f, indent=2)

                    print("\n Atualizando serviço com nova porta...")
                    service_content = textwrap.dedent(f"""\
                        [Unit]
                        Description=Terminal Web (ttyd)
                        After=network.target

                        [Service]
                        Type=simple
                        User=root
                        ExecStart={ttyd_bin} --credential {shlex.quote(ttyd_user)}:{shlex.quote(ttyd_password)} --port {nova_porta} --writable tmux new-session -A -s main "bash"
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
                    subprocess.run(["sudo", "systemctl", "restart", "ttyd.service"], check=False)

                    print(f" Porta alterada para {nova_porta} e serviço reiniciado!")
                else:
                    print(" Porta mantida.")
                input("\nPressione Enter para continuar...")

            elif opcao == "0":
                break
            else:
                print(" Opção inválida.")

    def menu_interfaces_graficas(self):
        opcoes = [
            ("📦  Instalar/Iniciar XFCE (Leve)", self.instalar_interface_xfce),
            ("📦  Instalar GNOME (Padrão Ubuntu)", self.instalar_interface_gnome),
            ("📦  Instalar Desktop Ubuntu Webtop (Docker)", self.desktop_ubuntu_webtop),
            ("🖥️  Instalar VNC Server (Acesso Remoto)", self.instala_vnc_server),
            ("↩️  Voltar", None)
        ]
        self.mostrar_menu_paginado(opcoes, titulo="🖥️  INTERFACES GRÁFICAS", itens_por_pagina=10)

    def menu_instalacoes(self):
        opcoes = [
            ("🐳  Docker e Aplicações em Containers", self.menu_docker),
            ("🧠  Inteligência Artificial (Ollama Local)", self.gerenciar_ollama),
            ("🦀  Open Claw (Automação/Agentes)", self.gerenciar_open_claw),
            ("🖥️ Interfaces Gráficas (Desktop)", self.menu_interfaces_graficas),
            ("📱  Terminal Mobile (Termote PWA)", self.instala_termote_mobile),
            ("📦  Instalar pacote .deb manualmente", self.instalar_deb),
            ("🤖  Gerenciar OpenCode (AI CLI)", self.gerenciar_opencode),
            ("📊  Monitor de Rede (vnstat)", self.vnstat),
            ("📝  Editores de Código (VSCode/OpenVSCode)", self.submenu_editores),
            ("☁️ Cloudflare WARP (VPN - Contorna bloqueios)", self.gerenciar_cloudflare_warp),
        ]
        self.mostrar_menu_paginado(opcoes, titulo="⬇️  CENTRAL DE INSTALAÇÕES", itens_por_pagina=10)

    def opcoes_sistema(self):
        opcoes_menu = [
            ("🌐  Configurações de Rede (IP, Wifi, SSH)", self.submenu_rede),
            ("💾  Gerenciamento de Disco e Partições", self.menu_particoes),
            ("💾  Gerenciamento de Swap", self.menu_swap),
            ("🔐  Gerenciamento de Permissões", self.gerenciar_permissoes_pasta),
            ("📊  Diagnóstico (Temp, Velocidade, Espaço)", self.submenu_diagnostico),
            ("🛠️ Ferramentas de Backup (Rsync)", self.rsync_sync),
            ("⚙️  Configurar Inicialização (.py service)", self.setup_inicializar_service),
            ("🔒  VPN WireGuard", self.menu_wireguard),
            ("💻  Fechar tampa notebook (NooT)", self.fecha_tela_noot),
            ("🔀  Encaminhamentos de Portas/Túneis", self.ecaminhamentos_portas_tuneis)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="⚙️  CONFIGURAÇÕES DO SISTEMA", itens_por_pagina=15)

    def menu_docker(self):
        print("\nBem-vindo ao Gerenciador Docker\n")
        self.instala_docker()
        if not os.path.exists(self.install_principal):
            os.makedirs(self.install_principal, exist_ok=True)
            os.chmod(self.install_principal, 0o777)
        opcoes_menu = [
            (" Gerenciar Containers Docker", self.menu_gerenciamento_docker),
            ("💪  Força instalação docker", self.instala_docker_force),
            ("📦  Instala portainer", self.instala_portainer),
            (" Instala filebrowser", self.instala_filebrowser),
            ("📦  Instala webserver guacamole", self.instala_webserver_guacamole),
            ("📦  Instala traefik", self.instala_traefik),
            ("||| Conf ||| Adiciona roteamento e serviço ao traefik", self.adiciona_roteador_servico_traefik),
            ("||| Conf ||| Configura rede do container", self.configura_rede),
            ("📦  Instala frp server (reverse proxy)", self.instala_frp_server),
            ("📦  Instala frp client (tunnel local)", self.instala_frp_client),
            ("||| Conf ||| Gerenciar frp proxies", self.gerenciar_frp),
            ("📦  Instala SFTP sftpgo", self.instala_ftp_sftpgo),
            ("||| Conf ||| Gerenciador SFTP sftpgo", self.gerenciar_usuarios_sftp),
            ("📦  Instala openlitespeed", self.instala_openlitespeed),
            ("||| Conf ||| Controle de sites openlitespeed", self.controle_sites_openlitespeed),
            ("** BD ** Instala mysql", self.instala_mysql),
            ("** BD ** Instala postgres", self.instala_postgres),
            ("||| Conf ||| Gerenciar bancos PostgreSQL", self.gerenciar_bancos_postgres),
            ("📦  Instala wordpress", self.instala_wordpress),
            (" Instala wordpress puro", self.instala_wordpress_puro),
            ("📦  Instala app nodejs", self.instala_app_nodejs),
            (" Instala grafana, prometheus, node-exporter", self.iniciar_monitoramento),
            ("📦  Instala n8n (workflow automation)", self.instalar_n8n),
            ("🔄  Start sync pastas com RSYNC", self.start_sync_pastas),
            ("📦  Instala windows KVM docker", self.instala_windows_KVM_docker),
            ("📦  Instala Sistema CISO docker", self.instala_sistema_CISO_docker),
            ("📦  Instala deskto ubuntu webtop", self.desktop_ubuntu_webtop),
            ("📦  Instala Ubuntu", self.ubuntu),
            (" Instala rustdesk", self.instala_rustdesk),
            ("📦  Instala pritunel", self.instala_pritunel),
            ("📦  Instala nextcloud", self.instala_nextcloud),
            (" Instala openvscode", self.instala_openvscode),
            ("📦  Instala vscode_oficial", self.instala_vscode_oficial),
            ("📦  Instala Open WebUI", self.instala_open_webui),
            ("📦  Instala Redis Docker", self.instala_redis_docker),
            ("Instala Evolution API WhatsApp", self.instala_evolution_api_whatsapp),
            ("Instala WAHA WhatsApp (devlikeapro)", self.instala_waha_whatsapp),
            ("Instala browserless (chromium headless)", self.instala_browserless),
            ("Instala selenium-firefox", self.instala_selenium_firefox),
            ("Instala rclone", self.rclone),
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🐳 GERENCIADOR DOCKER", itens_por_pagina=15)

    def gerenciar_microservicos(self):
        opcoes_menu = [
            ("🔗  Gerenciar Túneis SSH", self.gerenciar_tuneis_ssh),
            ("🌐  Gerenciar FRP Proxies", self.gerenciar_frp),
            ("📁  Gerenciar SFTP (sftpgo)", self.gerenciar_usuarios_sftp),
            ("🌍  Gerenciar Traefik (rotas)", self.adiciona_roteador_servico_traefik),
            ("📊  Monitoramento (Grafana)", self.iniciar_monitoramento),
            ("💾  Gerenciar Bancos PostgreSQL", self.gerenciar_bancos_postgres),
            ("📝  Controle Sites (OpenLiteSpeed)", self.controle_sites_openlitespeed),
            ("📱  Gerenciar Terminal (Termote/ttyd)", self.gerenciar_terminal_web)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🔧 GERENCIADOR DE MICROSERVIÇOS", itens_por_pagina=10)


def main():
    servicos = Sistema()

    check_for_update(sistema_instance=servicos)

    banner = f"""Arquivo install_master.py iniciado!
 Versão 1.235
Execute com: install_master
ip server: {servicos.exibe_ip()}"""
    opcoes_menu = [
        ("  Reiniciar", servicos.Reiniciar),
        (" ️ Desligar", servicos.Desligar),
        ("  Atualizar o sistema", servicos.menu_atualizacoes),
        ("  Central de Instalações", servicos.menu_instalacoes),
        ("  Gerenciar Microserviços", servicos.gerenciar_microservicos),
        ("️  Configurações do Sistema", servicos.opcoes_sistema),
        ("  Diagnóstico e Monitoramento", servicos.submenu_diagnostico),
        ("  Comandos essenciais do Linux", servicos.comandos_essenciais_linux)
    ]
    servicos.mostrar_menu_paginado(opcoes_menu, titulo="🖥️  MENU PRINCIPAL - INSTALL MASTER", itens_por_pagina=10, principal=True, mensagem_topo=banner)


if __name__ == "__main__":
    main()
