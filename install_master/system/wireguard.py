import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from install_master.core.docker_base import DockerBase


class MixinWireguard(DockerBase):

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

        for tentativa in range(1, max_tentativas + 1):
            nome = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome para identificar as chaves (ex: servidor, worker1): ").strip()
            if nome:
                break
            print(f"❌ Nome não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Operação cancelada.")
                return

        chaves_dir = Path(f"{self.install_principal}/wireguard/chaves/{nome}")
        chaves_dir.mkdir(parents=True, exist_ok=True)

        private_key_file = chaves_dir / "private.key"
        public_key_file = chaves_dir / "public.key"

        print(f"\n📝 Gerando chaves para '{nome}'...")

        try:
            result_private = subprocess.run(
                ["wg", "genkey"],
                capture_output=True,
                text=True,
                check=True
            )
            private_key = result_private.stdout.strip()

            result_public = subprocess.run(
                ["wg", "pubkey"],
                input=private_key,
                capture_output=True,
                text=True,
                check=True
            )
            public_key = result_public.stdout.strip()

            private_key_file.write_text(private_key)
            public_key_file.write_text(public_key)

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

        print("📝 Configuração do servidor WireGuard\n")

        for tentativa in range(1, max_tentativas + 1):
            ip_servidor = input(f"[{tentativa}/{max_tentativas}] IP do servidor na VPN (ex: 10.8.0.1/24): ").strip()
            if ip_servidor:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            porta = input(f"[{tentativa}/{max_tentativas}] Porta (padrão 51820): ").strip() or "51820"
            try:
                int(porta)
                break
            except ValueError:
                print(f"❌ Porta inválida. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    porta = "51820"

        print(f"\n🔑 Chaves disponíveis em {self.install_principal}/wireguard/chaves/")
        subprocess.run(["ls", "-la", f"{self.install_principal}/wireguard/chaves/"], check=False)

        for tentativa in range(1, max_tentativas + 1):
            chave_privada = input(f"\n[{tentativa}/{max_tentativas}] Cole a chave PRIVADA do servidor: ").strip()
            if chave_privada:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

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

        print("📝 Configuração do cliente WireGuard\n")

        for tentativa in range(1, max_tentativas + 1):
            ip_cliente = input(f"[{tentativa}/{max_tentativas}] IP do cliente na VPN (ex: 10.8.0.2/24): ").strip()
            if ip_cliente:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            chave_privada_cliente = input(f"\n[{tentativa}/{max_tentativas}] Cole a chave PRIVADA do cliente: ").strip()
            if chave_privada_cliente:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            chave_publica_servidor = input(f"[{tentativa}/{max_tentativas}] Cole a chave PÚBLICA do servidor: ").strip()
            if chave_publica_servidor:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            endpoint = input(f"[{tentativa}/{max_tentativas}] IP público do servidor (ex: 1.2.3.4): ").strip()
            if endpoint:
                break
            print(f"❌ Endpoint não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            porta_servidor = input(f"[{tentativa}/{max_tentativas}] Porta do servidor (padrão 51820): ").strip() or "51820"
            try:
                int(porta_servidor)
                break
            except ValueError:
                print(f"❌ Porta inválida. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    porta_servidor = "51820"

        allowed_ips = input("IPs permitidos (padrão 10.8.0.0/24): ").strip() or "10.8.0.0/24"

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

        for tentativa in range(1, max_tentativas + 1):
            nome_peer = input(f"[{tentativa}/{max_tentativas}] Nome do peer (ex: worker1): ").strip()
            if nome_peer:
                break
            print(f"❌ Nome não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            chave_publica_peer = input(f"[{tentativa}/{max_tentativas}] Cole a chave PÚBLICA do peer: ").strip()
            if chave_publica_peer:
                break
            print(f"❌ Chave não pode ser vazia. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

        for tentativa in range(1, max_tentativas + 1):
            ip_peer = input(f"[{tentativa}/{max_tentativas}] IP do peer na VPN (ex: 10.8.0.2/32): ").strip()
            if ip_peer:
                break
            print(f"❌ IP não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                return

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

        config_path = Path("/etc/wireguard/wg0.conf")
        config_existente = config_path.exists()

        if config_existente:
            print("⚠️  ATENÇÃO: Já existe uma configuração WireGuard!")
            print(f"📁 Localização: {config_path}")

            try:
                config_content = config_path.read_text()
                print("\n" + "="*70)
                print("📄 CONFIGURAÇÃO ATUAL:")
                print("="*70)
                print(config_content)
                print("="*70)
            except Exception as e:
                print(f"⚠️  Não foi possível ler a configuração: {e}")

            print("\n📊 Status do serviço:")
            subprocess.run(["sudo", "systemctl", "status", "wg-quick@wg0", "--no-pager"], check=False)

            print("\n" + "="*70)
            print("OPÇÕES:")
            print("[1] ✅  Manter configuração e apenas visualizar/gerenciar")
            print("[2] 🔄  RESETAR e criar nova configuração")
            print("[0] ↩️  Voltar ao menu")
            print("="*70)

            opcao = input("\nEscolha: ").strip()

            if opcao == "0":
                return
            elif opcao == "1":
                print("\n✅ Mantendo configuração existente.")

                chaves_dir = Path(f"{self.install_principal}/wireguard/chaves")
                public_key_file = chaves_dir / "public.key"

                if public_key_file.exists():
                    public_key = public_key_file.read_text().strip()
                    print("\n" + "="*70)
                    print("📋 SUAS INFORMAÇÕES PARA COMPARTILHAR:")
                    print("="*70)
                    print(f"🔓 Chave Pública: {public_key}")

                    try:
                        import re
                        match = re.search(r'Address\s*=\s*(\S+)', config_content)
                        if match:
                            print(f"📍 IP na VPN: {match.group(1)}")
                    except:
                        pass
                    print("="*70)

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

                print("\n" + "="*70)
                print("O QUE DESEJA FAZER?")
                print("="*70)
                print("[1] ➕  Adicionar novo peer (para servidores)")
                print("[2] 📊  Ver status detalhado")
                print("[3] 🔍  Testar conexão com peer")
                print("[0] ↩️  Voltar ao menu principal")
                print("="*70)

                acao = input("\nEscolha: ").strip()

                if acao == "1":
                    self._adicionar_peer_dinamico()
                elif acao == "2":
                    print("\n📊 STATUS DETALHADO:")
                    subprocess.run(["sudo", "systemctl", "status", "wg-quick@wg0", "--no-pager"], check=False)
                    print("\n🔗 CONEXÕES:")
                    subprocess.run(["sudo", "wg", "show"], check=False)
                elif acao == "3":
                    ip_teste = input("\nDigite o IP do peer para testar (ex: 10.8.0.2): ").strip()
                    if ip_teste:
                        print(f"\n🔍 Testando conectividade com {ip_teste}...")
                        subprocess.run(["ping", "-c", "4", ip_teste], check=False)

                return

                return
            elif opcao == "2":
                print("🔄 A configuração será resetada...")
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

        chaves_dir = Path(f"{self.install_principal}/wireguard/chaves")
        private_key_file = chaves_dir / "private.key"
        public_key_file = chaves_dir / "public.key"

        renovar_chaves = False

        if private_key_file.exists() and public_key_file.exists():
            print(f"\n✅ Par de chaves encontrado em: {chaves_dir}")

            try:
                pub_key_preview = public_key_file.read_text().strip()
                print(f"🔓 Chave Pública atual: {pub_key_preview}")
            except:
                pass

            renovar = input("\nDeseja RENOVAR as chaves? [s/N]: ").strip().lower()
            if renovar == 's':
                renovar_chaves = True
                try:
                    import shutil
                    backup_dir = chaves_dir / "backup"
                    backup_dir.mkdir(exist_ok=True)
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.copy(private_key_file, backup_dir / f"private.key.{timestamp}")
                    shutil.copy(public_key_file, backup_dir / f"public.key.{timestamp}")
                    print(f" Backup das chaves antigas salvo em: {backup_dir}")
                except:
                    pass
        else:
            renovar_chaves = True

        if renovar_chaves:
            print("\n🔑 Gerando novo par de chaves...")
            chaves_dir.mkdir(parents=True, exist_ok=True)

            try:
                result_private = subprocess.run(
                    ["wg", "genkey"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                private_key = result_private.stdout.strip()

                result_public = subprocess.run(
                    ["wg", "pubkey"],
                    input=private_key,
                    capture_output=True,
                    text=True,
                    check=True
                )
                public_key = result_public.stdout.strip()

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

        print("="*70)
        print("Qual tipo de configuração deseja?")
        print("[1] 🖥️  SERVIDOR (recebe conexões)")
        print("[2] 💻  CLIENTE/WORKER (conecta a um servidor)")
        print("[3] ➕  Adicionar peer ao servidor existente")
        print("[0] ↩️  Voltar")
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

        ip_servidor = input("IP do servidor na VPN [10.8.0.1/24]: ").strip() or "10.8.0.1/24"
        porta = input("Porta [51820]: ").strip() or "51820"

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

            subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
            subprocess.run(["sudo", "sed", "-i", "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/", "/etc/sysctl.conf"], check=False)

            print("\n✅ Servidor configurado com sucesso!")
            print(f"📁 Config: {config_path}")

            print("\n" + "="*70)
            print(" CONFIGURAÇÃO DO SERVIDOR CRIADA:")
            print("="*70)
            print(config_content)
            print("="*70)

            print("\n🚀 Iniciando servidor WireGuard automaticamente...")
            try:
                subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
                print("✅ Servidor WireGuard iniciado e habilitado!\n")
                subprocess.run(["sudo", "wg", "show"], check=False)
            except Exception as e:
                print(f"⚠️  Erro ao iniciar: {e}")

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

            print("\n" + "="*70)
            print(" CONFIGURAÇÃO DO CLIENTE CRIADA:")
            print("="*70)
            print(config_content)
            print("="*70)

            print("\n🚀 Conectando ao servidor automaticamente...")
            try:
                subprocess.run(["sudo", "systemctl", "enable", "wg-quick@wg0"], check=True)
                subprocess.run(["sudo", "systemctl", "start", "wg-quick@wg0"], check=True)
                print("✅ Cliente conectado e habilitado!\n")
                subprocess.run(["sudo", "wg", "show"], check=False)
            except Exception as e:
                print(f"⚠️  Erro ao conectar: {e}")

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

        nome = input("📝 Nome/identificação do peer (ex: worker1, laptop): ").strip() or "peer"

        chave_pub = input("🔓 Chave PÚBLICA do peer: ").strip()
        if not chave_pub:
            print("❌ Chave pública é obrigatória!")
            return

        ip_peer = input("📍 IP do peer na VPN (ex: 10.8.0.2/32) [/32]: ").strip()
        if not ip_peer:
            print("❌ IP é obrigatório!")
            return

        if '/32' not in ip_peer:
            ip_peer = ip_peer.rstrip('/') + '/32'

        peer_config = f"""
[Peer]
# {nome}
PublicKey = {chave_pub}
AllowedIPs = {ip_peer}
"""

        try:
            with open(config_path, 'a') as f:
                f.write(peer_config)

            print("\n✅ Peer adicionado à configuração!")

            print("\n" + "="*70)
            print("📄 CONFIGURAÇÃO ATUALIZADA:")
            print("="*70)
            updated_config = config_path.read_text()
            print(updated_config)
            print("="*70)

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
            ("🚀  Configurar WireGuard (Auto-install)", self.configurar_wireguard_dinamico),
            ("▶️  Iniciar/Habilitar WireGuard", self.iniciar_wireguard),
            ("⏸️  Parar WireGuard", self.parar_wireguard),
            ("📊  Ver status e conexões", self.status_wireguard),
            ("🔍  Testar conexão", self.testar_conexao_wireguard),
            ("📄  Visualizar configuração", self.visualizar_config_wireguard)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🔐 GERENCIADOR WIREGUARD VPN", itens_por_pagina=10)
