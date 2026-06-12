import os
import shutil
import subprocess
import textwrap
import time
from pathlib import Path

from install_master.core.docker_base import DockerBase


class MixinServices(DockerBase):

    def setup_inicializar_service(self):
        """
        1. Cria /install_principal/inicializar.py (com log simples) se não existir.
        2. Cria /etc/systemd/system/inicializar.service apontando para ele se não existir.
        3. Recarrega o systemd e habilita o serviço.

        → Execute como root ou via sudo.
        """
        script_path = Path("/install_principal/inicializar.py")
        service_path = Path("/etc/systemd/system/inicializar.service")

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
            script_path.chmod(0o755)
            print(f"✔ Script criado em {script_path}")
        else:
            print(f"✓ Script {script_path} já existe, mantendo o arquivo existente")

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

    def gerenciar_cloudflare_warp(self):
        """Gerencia o Cloudflare WARP para contornar bloqueios de ISP (Claro/NET/Vivo)"""
        while True:
            try:
                result = subprocess.run("warp-cli status", shell=True, capture_output=True, text=True)
                if "Connected" in result.stdout:
                    status_warp = "🟢 Conectado"
                elif "Disconnected" in result.stdout:
                    status_warp = "🔴 Desconectado"
                else:
                    status_warp = "⚪ Não instalado"
            except:
                status_warp = "⚪ Não instalado"

            print("\n" + "="*55)
            print("☁️  CLOUDFLARE WARP - VPN GRATUITA")
            print("="*55)
            print(f"Status: {status_warp}")
            print("-"*55)
            print("Útil para contornar bloqueios de ISP (Claro/NET/Vivo)")
            print("que impedem downloads do Ollama, Docker Hub, etc.")
            print("-"*55)
            print("[1] 📦  Instalar WARP")
            print("[2] 🔌  Conectar")
            print("[3] 🔌  Desconectar")
            print("[4] 📊  Ver Status Detalhado")
            print("[5] 🌐  Testar Conexão com Cloudflare")
            print("[6] ⚡  Habilitar Conexão Automática (boot)")
            print("[0] ↩️  Voltar")
            print("="*55)

            opt_warp = input("\nEscolha: ").strip()

            if opt_warp == '1':
                print("\n📦 Instalando Cloudflare WARP...")
                cmds = [
                    "curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg",
                    'echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list',
                    "sudo apt update",
                    "sudo apt install -y cloudflare-warp"
                ]
                for cmd in cmds:
                    subprocess.run(cmd, shell=True)

                print("\n🔑 Registrando dispositivo...")
                subprocess.run("warp-cli registration new", shell=True)
                print("✅ WARP instalado! Use a opção 2 para conectar.")
                input("\nEnter para continuar...")

            elif opt_warp == '2':
                print("\n🔌 Conectando ao WARP...")
                subprocess.run("warp-cli connect", shell=True)
                time.sleep(2)
                subprocess.run("warp-cli status", shell=True)
                input("\nEnter para continuar...")

            elif opt_warp == '3':
                print("\n🔌 Desconectando do WARP...")
                subprocess.run("warp-cli disconnect", shell=True)
                input("\nEnter para continuar...")

            elif opt_warp == '4':
                subprocess.run("warp-cli status", shell=True)
                subprocess.run("warp-cli settings", shell=True)
                input("\nEnter para continuar...")

            elif opt_warp == '5':
                print("\n🔍 Testando conexão com Cloudflare (CDN de vários serviços)...")
                result = subprocess.run("ping -c 3 r2.cloudflarestorage.com", shell=True)
                if result.returncode == 0:
                    print("\n✅ Conexão OK! Downloads devem funcionar normalmente.")
                else:
                    print("\n❌ Sem conexão com Cloudflare. Conecte o WARP (opção 2).")
                input("\nEnter para continuar...")

            elif opt_warp == '6':
                print("\n⚙️ Habilitando conexão automática no boot...")
                subprocess.run("warp-cli set-mode warp", shell=True)
                subprocess.run("warp-cli connect", shell=True)
                print("\n✅ WARP configurado para conectar automaticamente!")
                print("O servidor reconectará ao WARP após cada reinicialização.")
                input("\nEnter para continuar...")

            elif opt_warp == '0':
                break

    def fecha_tela_noot(self):
        config_path = "/etc/systemd/logind.conf"

        with open(config_path, "r") as file:
            lines = file.readlines()

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
        Verifica se um pacote está instalado no sistema (via dpkg) ou se o comando existe no PATH.
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
            if resultado.returncode == 0:
                return True
        except Exception:
            pass

        if shutil.which(pacote):
            return True

        return False
