import os
import re
import subprocess
import time

import yaml

from install_master.core.docker_base import DockerBase


class MixinNetwork(DockerBase):

    def submenu_rede(self):
        opcoes = [
            ("📶  Gerenciar Wifi (nmtui)", self.setup_wifi),
            ("📍  Configurar IP Fixo", self.configura_ip_fixo),
            ("📊  Informações de Rede", self.informacoes_rede),
            ("🔐  Configurar SSH", self.configurar_ssh),
            ("↩️  Voltar", None)
        ]
        self.mostrar_menu_paginado(opcoes, titulo="🌐 CONFIGURAÇÕES DE REDE", itens_por_pagina=10)

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
            with open("/etc/fstab", "r") as fstab:
                linhas = fstab.readlines()

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

                linha_fstab = f"{dispositivo} {ponto_montagem} ext4 defaults 0 0\n"
                with open("/etc/fstab", "a") as fstab:
                    fstab.write(linha_fstab)
                print(f"Partição {dispositivo} adicionada ao /etc/fstab para montagem automática em {ponto_montagem}.")

            elif acao == 'desmontar':
                if linha_existente:
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

    def lista_interfaces_fisicas(self):
        """Lista interfaces de rede físicas, filtrando interfaces virtuais."""
        try:
            saida = subprocess.check_output(
                ["ip", "-o", "link", "show"], text=True
            )
        except subprocess.CalledProcessError:
            return []

        # Padrões de interfaces virtuais a ignorar
        prefixos_virtuais = (
            "lo", "docker", "br-", "veth", "wg",
            "virbr", "lxcbr", "cali", "flannel", "vnet", "kube",
        )

        interfaces = []
        for linha in saida.strip().splitlines():
            match = re.match(r'^\d+:\s+(\S+?)[@:]', linha)
            if not match:
                continue
            nome = match.group(1)
            # Remove sufixo @ifN de veth pairs
            nome = re.sub(r'@\w+$', '', nome)
            # Filtra interfaces virtuais
            if any(nome == p or nome.startswith(p) for p in prefixos_virtuais):
                continue
            if nome not in interfaces:
                interfaces.append(nome)

        return interfaces

    def configura_ip_fixo(self,):
        # Lista interfaces físicas disponíveis para seleção
        interfaces = self.lista_interfaces_fisicas()

        if not interfaces:
            print("❌ Nenhuma interface de rede física encontrada.")
            return

        print("Interfaces de rede disponíveis:")
        for idx, nome in enumerate(interfaces, start=1):
            print(f"  [{idx}] {nome}")

        # Seleção numérica da interface
        while True:
            escolha = input("Selecione o número da interface de rede: ").strip()
            try:
                num = int(escolha)
                if 1 <= num <= len(interfaces):
                    break
                print(f"❌ Digite um número entre 1 e {len(interfaces)}.")
            except ValueError:
                print("❌ Entrada inválida. Digite um número.")

        interface = interfaces[num - 1]
        print(f"✅ Interface selecionada: {interface}")

        ip_address = input("Digite o endereço IP com a máscara (ex: 192.168.0.80/24): ")

        gateway = input("Digite o endereço do gateway (ex: 192.168.0.1): ")

        dns = input("Digite os endereços de DNS separados por vírgula (ex: 8.8.8.8, 8.8.4.4): ")
        dns_list = [dns.strip() for dns in dns.split(",")]

        config_file = "/etc/netplan/00-installer-config.yaml"
        if not os.path.exists(config_file):
            config_file = "/etc/netplan/50-cloud-init.yaml"
            with open("/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg", "w") as file:
                file.write("network: {config: disabled}")

        print("Criando backup do arquivo de configuração existente...")
        backup_file = config_file + "_old"
        subprocess.run(["sudo", "cp", config_file, backup_file], check=True)

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

        print("Gerando novo arquivo de configuração...")
        try:
            with open(config_file, "w") as file:
                yaml.dump(config_data, file, default_flow_style=False)
        except IOError as e:
            print(f"Erro ao escrever no arquivo de configuração: {e}")
            return

        print("Aplicando as configurações...")
        try:
            subprocess.run(["sudo", "netplan", "apply"], check=True)
            print("Configuração concluída com sucesso!")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao aplicar as configurações: {e}")

    def informacoes_rede(self):
        """Exibe informações completas de rede de todas as interfaces físicas."""

        def cidr_to_mask(cidr):
            """Converte prefixo CIDR para máscara decimal. Ex: 23 -> 255.255.254.0"""
            try:
                prefix = int(cidr)
                mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
                return f"{(mask_int >> 24) & 0xFF}.{(mask_int >> 16) & 0xFF}.{(mask_int >> 8) & 0xFF}.{mask_int & 0xFF}"
            except (ValueError, TypeError):
                return "N/A"

        interfaces = self.lista_interfaces_fisicas()

        if not interfaces:
            print("\n⚠️  Nenhuma interface de rede física encontrada.")
            return

        print("\n" + "=" * 60)
        print("📊 INFORMAÇÕES DE REDE")
        print("=" * 60)

        for iface in interfaces:
            print(f"\nInterface: {iface}")
            print(f"{'─' * 60}")

            # IP e máscara
            try:
                output = subprocess.check_output(
                    ["ip", "-4", "addr", "show", iface], text=True, stderr=subprocess.DEVNULL
                )
                for line in output.splitlines():
                    line = line.strip()
                    if "inet " in line:
                        parts = line.split()
                        ip_mask = parts[1] if len(parts) > 1 else "N/A"
                        print(f"  📍 IP:      {ip_mask}")
                        if "/" in ip_mask:
                            cidr = ip_mask.split("/")[1]
                            mask = cidr_to_mask(cidr)
                            print(f"  📍 Máscara:  {mask}")
            except Exception:
                print("  📍 IP:      N/A (sem IPv4)")

            # MAC e status
            try:
                output = subprocess.check_output(
                    ["ip", "link", "show", iface], text=True, stderr=subprocess.DEVNULL
                )
                for line in output.splitlines():
                    line = line.strip()
                    if "link/ether" in line:
                        mac = line.split()[1]
                        print(f"  📡 MAC:     {mac}")
                    if "<" in line and ">" in line:
                        start = line.index("<") + 1
                        end = line.index(">")
                        flags = line[start:end]
                        status = "UP" if "UP" in flags else "DOWN"
                        print(f"  📡 Status:  {status}")
                        if "mtu" in line:
                            mtu = line.split("mtu")[1].strip().split()[0]
                            print(f"  📦 MTU:     {mtu}")
            except Exception:
                print("  📡 MAC:     N/A")
                print("  📡 Status:  N/A")

            # Gateway da interface
            try:
                rotas_iface = subprocess.check_output(
                    ["ip", "route", "show", "dev", iface], text=True, stderr=subprocess.DEVNULL
                ).strip()
                gateways = []
                for rota in rotas_iface.splitlines():
                    rota = rota.strip()
                    if " via " in rota:
                        parts = rota.split()
                        idx = parts.index("via")
                        if idx + 1 < len(parts):
                            gw = parts[idx + 1]
                            if gw not in gateways:
                                gateways.append(gw)
                if gateways:
                    print(f"  🚪 Gateway:  {', '.join(gateways)}")
            except Exception:
                pass

        print(f"\n{'─' * 60}")

        # DNS
        try:
            with open("/etc/resolv.conf", "r") as f:
                dns_servers = [line.strip().split()[1] for line in f if line.strip().startswith("nameserver")]
                if dns_servers:
                    print(f"   DNS:      {', '.join(dns_servers)}")
                else:
                    print("   DNS:      N/A")
        except Exception:
            print("   DNS:      N/A (não foi possível ler /etc/resolv.conf)")

        # IP público
        try:
            ip_publico = subprocess.check_output(
                ["curl", "-s", "--connect-timeout", "5", "ifconfig.me"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            print(f"   IP Público: {ip_publico}")
        except Exception:
            print("   IP Público: N/A (sem conexão ou timeout)")

        print(f"{'─' * 60}\n")
        input("Pressione Enter para continuar...")

    def verificar_boot_mode(self):
        """Verifica se o sistema está usando BIOS (Legacy) ou UEFI"""
        if os.path.exists("/sys/firmware/efi"):
            return "UEFI"
        return "BIOS"
