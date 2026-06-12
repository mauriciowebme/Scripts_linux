import json
import os
import shutil
import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinOllama(DockerBase):

    def gerenciar_open_claw(self):
        """Gerenciador centralizado do Open Claw"""

        print("\n⚠️  AVISO: A instalação correta do Open Claw não deve ser feita com usuário root!")
        print("   Recomendamos usar um usuário comum para evitar problemas de permissão.\n")

        def ensure_node_options():
            os.environ["NODE_OPTIONS"] = "--max-old-space-size=2048"

            print("Configurando persistência global da variável NODE_OPTIONS (2GB)...")

            cmd_profile = 'echo \'export NODE_OPTIONS="--max-old-space-size=2048"\' | sudo tee /etc/profile.d/99-node-options.sh > /dev/null'
            subprocess.run(cmd_profile, shell=True)
            subprocess.run('sudo chmod 644 /etc/profile.d/99-node-options.sh', shell=True)

            cmd_remove = "sudo sed -i '/^NODE_OPTIONS=/d' /etc/environment"
            cmd_add = 'echo \'NODE_OPTIONS="--max-old-space-size=2048"\' | sudo tee -a /etc/environment > /dev/null'
            subprocess.run(cmd_remove, shell=True)
            subprocess.run(cmd_add, shell=True)

        def install():
            print('Instalando/Atualizando Open Claw...')
            ensure_node_options()

            print("NOTA: O instalador pode iniciar o servidor (Gateway) automaticamente ao final.")
            print("      Se o processo ficar parado em 'Onboarding complete' ou similar,")
            print("      pressione Ctrl+C para encerrar o servidor e voltar ao menu.\n")

            try:
                subprocess.run('curl -fsSL https://openclaw.bot/install.sh | sudo bash', shell=True)
            except KeyboardInterrupt:
                print("\n\nExecução interrompida. Retornando ao menu...")

        def doctor():
            print('Executando diagnóstico (doctor)...')
            ensure_node_options()

            try:
                print("Aplicando correções de segurança...")
                subprocess.run("chmod 700 ~/.openclaw/credentials", shell=True)

                print("✅ Correções de permissões aplicadas.")
            except Exception as e:
                print(f"⚠️ Erro ao aplicar correções preventivas: {e}")

            try:
                res = subprocess.run("openclaw doctor", shell=True)
                if res.returncode != 0:
                    raise Exception("Doctor falhou")
                print("Tentando executar auto-fix (openclaw doctor --fix)...")
                subprocess.run("openclaw doctor --fix", shell=True)
            except Exception:
                print("Comando 'openclaw doctor' falhou ou não foi encontrado.")
                print("Tentando rodar o script de instalação para correção...")
                install()

        def configure():
            print("\n=== Configuração Geral (API e Canais) ===")
            print("Executando o assistente de configuração principal...")
            subprocess.run("openclaw configure", shell=True)

        def chat_terminal():
            """Chat via Terminal usando comando CLI"""
            print("\n=== Chat Terminal Open Claw (TUI) ===")
            print("Executando: openclaw tui")
            try:
                subprocess.run("openclaw tui", shell=True)
            except Exception as e:
                print(f"❌ Erro ao tentar executar 'openclaw tui': {e}")
                print("💡 Dica: Verifique se o comando existe ou use o Dashboard.")

        def clean_install():
            print("ATENÇÃO: Isso irá remover o Open Claw e configurações locais (como ~/.openclaw) antes de reinstalar.")
            if input("Tem certeza? (s/N): ").lower() == 's':
                print("Removendo Open Claw...")
                subprocess.run("sudo npm uninstall -g openclaw", shell=True)
                subprocess.run("rm -f $HOME/.local/bin/openclaw", shell=True)
                subprocess.run("rm -rf ~/.openclaw", shell=True)
                print("Instalação limpa iniciada...")
                install()

        def status():
            print("\n=== Status Open Claw ===")
            print("Executando: openclaw status")
            try:
                res = subprocess.run("openclaw status", shell=True)
                if res.returncode != 0:
                    print("⚠️  Comando 'openclaw status' retornou erro ou não disponível.")
                    print("Tentando 'openclaw doctor'...")
                    subprocess.run("openclaw doctor", shell=True)
            except Exception as e:
                print(f"❌ Erro ao executar status: {e}")

            print("\nDashboard Web: http://localhost:18789")

        while True:
            print("\n" + "="*45)
            print("🦀 OPEN CLAW MANAGER - MENU CENTRALIZADO")
            print("="*45)
            print("[1] 📦  Instalar / Atualizar")
            print("[2] 🩺  Correção (Doctor)")
            print("[3] ⚙️  Configurar (openclaw configure)")
            print("[4] 📊  Status")
            print("[5] 🗑️  Reinstalar do Zero (Limpar e Instalar)")
            print("[6] 💬  Chat no Terminal (openclaw tui)")
            print("[0] ↩️  Voltar ao Menu Anterior")
            print("="*45)

            opt = input("\nEscolha uma opção: ").strip()

            if opt == '1': install()
            elif opt == '2': doctor()
            elif opt == '3': configure()
            elif opt == '4': status()
            elif opt == '5': clean_install()
            elif opt == '6': chat_terminal()
            elif opt == '0': break
            else: print("❌ Opção inválida, tente novamente.")

    def gerenciar_ollama(self):
        """Gerenciador Centralizado para Ollama"""

        def check_status():
            print("\n=== STATUS DO SERVIÇO OLLAMA ===")
            print("Executando: sudo systemctl status ollama")
            subprocess.run("sudo systemctl status ollama", shell=True)

        def restart_service():
            print("\n=== REINICIAR SERVIÇO OLLAMA ===")
            print("Executando: sudo systemctl restart ollama")
            subprocess.run("sudo systemctl restart ollama", shell=True)

        def install_ollama():
            print("\n=== INSTALAÇÃO OLLAMA (LOCAL) ===\n")
            print("Baixando e executando script de instalação oficial...")
            if shutil.which("curl") is None:
                print("Instalando curl...")
                subprocess.run("sudo apt install -y curl", shell=True)

            cmd = "curl -fsSL https://ollama.com/install.sh | sudo sh"
            try:
                subprocess.run(cmd, shell=True, check=True)
                print("\n✅ Ollama instalado com sucesso!")
                print("O serviço deve iniciar automaticamente via systemd.")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Erro durante a instalação: {e}")
                print("Verifique se você tem permissões de root ou sudo ajustado.")

        def run_modelo(nome_modelo):
            print(f"\n🚀 Iniciando modelo: {nome_modelo}")
            print("O download será iniciado automaticamente se o modelo não existir.")
            print("Pressione Ctrl+D ou digite '/bye' para sair do chat.\n")
            try:
                subprocess.run(f"ollama run {nome_modelo}", shell=True)
            except Exception as e:
                print(f"❌ Erro ao rodar modelo: {e}")

        def remover_modelo():
            print("\n=== REMOVER MODELO ===")
            subprocess.run("ollama list", shell=True)
            modelo = input("\nDigite o nome do modelo para remover: ").strip()
            if modelo:
                print(f"Removendo {modelo}...")
                subprocess.run(f"ollama rm {modelo}", shell=True)

        def integracao_openclaw():
            print("\n=== INTEGRAÇÃO OPEN CLAW ===")

            print("Configurando gateway.mode=local...")
            subprocess.run("openclaw config set gateway.mode local", shell=True)

            print("Configurando URL do provider Ollama para http://127.0.0.1:11434...")
            subprocess.run("openclaw config set models.providers.ollama.baseUrl http://127.0.0.1:11434", shell=True)

            try:
                print("Verificando conexão com Ollama...")
                res = subprocess.run("curl -s http://127.0.0.1:11434", shell=True, capture_output=True, text=True)
                if "Ollama is running" in res.stdout:
                     print("✅ Ollama detectado e respondendo.")
                else:
                     print("⚠️  Aviso: Não foi possível confirmar se o Ollama está respondendo em 127.0.0.1:11434.")
                     print("   Tentando reiniciar o serviço Ollama...")
                     subprocess.run("sudo systemctl restart ollama", shell=True)
            except Exception:
                pass

            print("Executando: ollama launch openclaw --config")
            try:
                subprocess.run("ollama launch openclaw --config", shell=True)
            except Exception as e:
                print(f"❌ Erro ao executar integração: {e}")

        def submenu_modelos():
            while True:
                print("\n" + "="*45)
                print("🧠 MODELOS OLLAMA - SELECIONE")
                print("="*45)
                print("[1] 🦙  Llama 3.1")
                print("[2] 🦙  Llama 3.2")
                print("[3] 💎  Gemma 3 (Beta)")
                print("[4] 🤖  Qwen 2.5 (3B) 32k - Suporte a Tools")
                print("[5] ✏️  Outro Modelo (Digitar Nome)")
                print("[6] 📋  Listar Instalados")
                print("[7] 🗑️  Remover Modelo")
                print("[0] ↩️  Voltar")
                print("="*45)

                escolha = input("\nEscolha: ").strip()

                if escolha == '1': run_modelo("llama3.1")
                elif escolha == '2': run_modelo("llama3.2")
                elif escolha == '3': run_modelo("gemma3")
                elif escolha == '4': run_modelo("qwen2.5")
                elif escolha == '5':
                    nome = input("Digite o nome do modelo: ").strip()
                    if nome: run_modelo(nome)
                elif escolha == '6':
                    subprocess.run("ollama list", shell=True)
                    input("\nEnter para continuar...")
                elif escolha == '7':
                    remover_modelo()
                    input("\nEnter para continuar...")
                elif escolha == '0':
                    break
                else:
                    print("❌ Opção inválida.")

        while True:
            print("\n" + "="*45)
            print("🦙 GERENCIADOR OLLAMA (LOCAL)")
            print("="*45)
            print("[1] 📦  Instalar Ollama (Script Oficial)")
                print("[2] 💬  Gerenciar Modelos / Chat")
            print("[3] 📊️  Verificar Status do Serviço")
            print("[4] 🔄  Reiniciar Serviço")
            print("[5] ️  Integração Open Claw")
            print("[0] ↩️  Voltar ao Menu Principal")
            print("="*45)

            opt = input("\nEscolha uma opção: ").strip()

            if opt == '1':
                install_ollama()
                input("\nEnter para continuar...")
            elif opt == '2':
                submenu_modelos()
            elif opt == '3':
                check_status()
                input("\nEnter para continuar...")
            elif opt == '4':
                restart_service()
                input("\nEnter para continuar...")
            elif opt == '5':
                integracao_openclaw()
                input("\nEnter para continuar...")
            elif opt == '0':
                break
            else:
                print("❌ Opção inválida.")
