import os
import json
import shutil
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path

from install_master.core.docker_base import DockerBase


class MixinOpenCode(DockerBase):
    def gerenciar_opencode(self):
        """Gerenciador centralizado do OpenCode (Instalar, Reiniciar, Status, Reconfigurar)"""
        
        def opcao_instalar():
            """Chama a instalação/atualização padrão"""
            self.instala_opencode()
            input("\nPressione Enter para voltar ao menu...")

        def opcao_reiniciar():
            """Reinicia o serviço systemd"""
            print("\n🔄 Reiniciando serviço OpenCode...")
            try:
                subprocess.run(["sudo", "systemctl", "restart", "opencode-web.service"], check=True)
                print("✅ Serviço reiniciado com sucesso!")
            except Exception as e:
                print(f" Erro ao reiniciar: {e}")
            input("\nPressione Enter para voltar ao menu...")

        def opcao_status():
            """Mostra o status e oferece logs se houver erro"""
            print("\n📊 Status do serviço OpenCode:")
            print("-" * 40)
            try:
                result = subprocess.run(
                    ["systemctl", "status", "opencode-web.service"],
                    capture_output=True, text=True
                )
                print(result.stdout)
                
                # Se o status indicar falha ou inatividade, oferece logs
                if "failed" in result.stdout.lower() or "inactive" in result.stdout.lower():
                    ver_logs = input("\n⚠️  O serviço parece estar parado ou com erro. Deseja ver os logs? (s/n): ").strip().lower()
                    if ver_logs == 's':
                        print("\n📜 Últimas linhas do log:")
                        subprocess.run(["journalctl", "-u", "opencode-web.service", "-e", "--no-pager", "-n", "50"])
            except Exception as e:
                print(f"❌ Erro ao verificar status: {e}")
            input("\nPressione Enter para voltar ao menu...")

        def opcao_reconfigurar():
            """Reconfigura porta e senha sem reinstalar"""
            print("\n⚙️  RECONFIGURAÇÃO DO MODO WEB")
            print("="*40)

            # 1. Detectar configuração atual
            config_file = Path.home() / ".config" / "opencode" / "opencode.json"
            porta_atual = "7860"
            senha_atual = ""

            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                    # Tenta extrair do formato novo (server) ou antigo
                    if "server" in data:
                        porta_atual = str(data["server"].get("port", "7860"))
                    elif "web" in data:
                        porta_atual = str(data["web"].get("port", "7860"))
                        senha_atual = data["web"].get("password", "")
                except:
                    pass
            
            print(f"Configuração atual detectada:")
            print(f" - Porta: {porta_atual}")
            print(f" - Senha: {'*' * len(senha_atual) if senha_atual else 'Não definida'}")

            # 2. Pedir novos dados
            nova_porta_input = input(f"\nNova porta para o modo web (Enter para manter {porta_atual}): ").strip()
            nova_porta = nova_porta_input if nova_porta_input else porta_atual

            nova_senha_input = input("Nova senha (Enter para manter a atual): ").strip()
            nova_senha = nova_senha_input if nova_senha_input else senha_atual
            
            if not nova_senha:
                print("⚠️  Senha vazia! Gerando senha automática...")
                nova_senha = self.generate_password(16)
                print(f"🔑 Senha gerada: {nova_senha}")

            # 3. Aplicar configuração
            print("\n📝 Aplicando novas configurações...")
            
            # Atualiza JSON
            opencode_config_dir = Path.home() / ".config" / "opencode"
            opencode_config_dir.mkdir(parents=True, exist_ok=True)
            
            config_data = {}
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                except:
                    pass
            
            # Limpa chaves antigas e aplica nova estrutura
            config_data.pop("web", None)
            config_data["server"] = {
                "port": int(nova_porta),
                "hostname": "0.0.0.0"
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✔ Arquivo de configuração atualizado: {config_file}")

            # Atualiza Serviço Systemd
            # Precisamos detectar o binário novamente para garantir que o service file esteja correto
            opencode_bin = None
            service_user = os.getenv('USER', 'root')
            service_home = os.path.expanduser(f"~{service_user}")
            
            search_paths = [
                Path.home() / ".opencode" / "bin" / "opencode",
                Path.home() / ".local" / "bin" / "opencode",
                Path("/usr/local/bin/opencode"),
            ]
            for p in search_paths:
                if p.exists():
                    opencode_bin = str(p)
                    break
            
            if not opencode_bin:
                 try:
                    result = subprocess.run(["find", "/home", "-name", "opencode", "-type", "f"], capture_output=True, text=True, timeout=5)
                    if result.stdout.strip():
                        opencode_bin = result.stdout.strip().split('\n')[0]
                        service_user = opencode_bin.split('/')[2]
                        service_home = f"/home/{service_user}"
                 except: pass

            if opencode_bin:
                service_path = Path("/etc/systemd/system/opencode-web.service")
                service_content = textwrap.dedent(f"""\
                    [Unit]
                    Description=OpenCode Web Server
                    After=network-online.target
                    Wants=network-online.target

                    [Service]
                    Type=simple
                    User={service_user}
                    Environment=HOME={service_home}
                    Environment=PATH={service_home}/.opencode/bin:{service_home}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
                    Environment=OPENCODE_SERVER_PASSWORD={nova_senha}
                    ExecStart={opencode_bin} serve --hostname 0.0.0.0 --port {nova_porta} --cors "*"
                    Restart=on-failure
                    RestartSec=10

                    [Install]
                    WantedBy=multi-user.target
                """)

                try:
                    try:
                        service_path.write_text(service_content)
                    except PermissionError:
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as tmp:
                            tmp.write(service_content)
                            tmp_path = tmp.name
                        subprocess.run(["sudo", "mv", tmp_path, str(service_path)], check=True)
                        subprocess.run(["sudo", "chmod", "644", str(service_path)], check=True)
                    
                    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                    subprocess.run(["sudo", "systemctl", "restart", "opencode-web.service"], check=True)
                    print("✔ Serviço atualizado e reiniciado com sucesso!")
                except Exception as e:
                    print(f"⚠️  Erro ao atualizar serviço: {e}")

            # Atualiza Firewall
            print(f"\n Liberando nova porta {nova_porta} no firewall...")
            try:
                # Verifica se já existe
                check_result = subprocess.run(
                    ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(nova_porta), "-j", "ACCEPT"],
                    capture_output=True
                )
                if check_result.returncode != 0:
                    subprocess.run(
                        ["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(nova_porta), "-j", "ACCEPT"],
                        check=True
                    )
                    print(f"✔ Porta {nova_porta} liberada no iptables")
                    
                    if shutil.which("netfilter-persistent"):
                        subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)
                else:
                    print(f"  Porta {nova_porta} já estava liberada.")
            except Exception as e:
                print(f"  ⚠️  Erro ao configurar firewall: {e}")

            # Final
            print("\n" + "="*60)
            print("✅ RECONFIGURAÇÃO CONCLUÍDA!")
            print("="*60)
            print(f"   Endereço: http://<seu_ip>:{nova_porta}")
            print(f"   Senha: {nova_senha}")
            print("="*60)
            input("\nPressione Enter para voltar ao menu...")

        def opcao_desinstalar():
            """Remove completamente o OpenCode do sistema"""
            print("\n🗑️  DESINSTALAÇÃO DO OPENCODE")
            print("="*40)

            # 1. Detectar o que existe para remover
            itens_para_remover = []
            service_path = Path("/etc/systemd/system/opencode-web.service")
            opencode_dir = Path.home() / ".opencode"
            config_dir = Path.home() / ".config" / "opencode"
            cache_dir = Path.home() / ".cache" / "opencode"
            share_dir = Path.home() / ".local" / "share" / "opencode"
            tmp_dir = Path("/tmp/opencode")
            local_bin = Path.home() / ".local" / "bin" / "opencode"
            usr_local_bin = Path("/usr/local/bin/opencode")
            usr_bin = Path("/usr/bin/opencode")

            if service_path.exists():
                itens_para_remover.append(f"Serviço systemd: {service_path}")
            if opencode_dir.exists():
                itens_para_remover.append(f"Diretório do binário: {opencode_dir}")
            if config_dir.exists():
                itens_para_remover.append(f"Diretório de configuração: {config_dir}")
            if cache_dir.exists():
                itens_para_remover.append(f"Diretório de cache: {cache_dir}")
            if share_dir.exists():
                itens_para_remover.append(f"Banco de dados de sessões: {share_dir}")
            if tmp_dir.exists():
                itens_para_remover.append(f"Temporários: {tmp_dir}")
            if local_bin.exists():
                itens_para_remover.append(f"Binário local: {local_bin}")
            if usr_local_bin.exists():
                itens_para_remover.append(f"Binário global (/usr/local/bin): {usr_local_bin}")
            if usr_bin.exists():
                itens_para_remover.append(f"Binário sistema (/usr/bin): {usr_bin}")

            if not itens_para_remover:
                print("   Nenhum componente do OpenCode encontrado no sistema.")
                input("\nPressione Enter para voltar ao menu...")
                return

            print("\nOs seguintes itens serão removidos:")
            for item in itens_para_remover:
                print(f"   - {item}")

            # 2. Confirmação
            print("\n⚠️  ATENÇÃO: Esta ação é irreversível!")
            confirmar = input("Deseja realmente desinstalar o OpenCode? (s/n): ").strip().lower()
            if confirmar != 's':
                print("   Desinstalação cancelada.")
                input("\nPressione Enter para voltar ao menu...")
                return

            # 3. Função de remoção forçada em cascata
            def forcar_remocao(caminho, descricao):
                """Remove diretório/arquivo usando múltiplas estratégias até confirmar que sumiu"""
                if not caminho.exists():
                    print(f"   ⏭️  {descricao} já não existe")
                    return True

                print(f"   🗑️  Removendo {descricao}...")
                caminho_str = str(caminho)

                # Estratégia 1: rm -rf direto
                try:
                    subprocess.run(["rm", "-rf", caminho_str], check=False, capture_output=True)
                    if not caminho.exists():
                        print(f"   ✔ {descricao} removido")
                        return True
                except:
                    pass

                # Estratégia 2: sudo rm -rf
                try:
                    print(f"   ⚠️  Tentando com sudo...")
                    subprocess.run(["sudo", "rm", "-rf", caminho_str], check=False, capture_output=True)
                    if not caminho.exists():
                        print(f"   ✔ {descricao} removido com sudo")
                        return True
                except:
                    pass

                # Estratégia 3: find -delete para limpar conteúdo interno primeiro
                if caminho.is_dir():
                    try:
                        print(f"   ⚠️  Limpando conteúdo interno com find...")
                        subprocess.run(["sudo", "find", caminho_str, "-delete"], check=False, capture_output=True, timeout=10)
                        subprocess.run(["sudo", "rm", "-rf", caminho_str], check=False, capture_output=True)
                        if not caminho.exists():
                            print(f"   ✔ {descricao} removido após limpeza interna")
                            return True
                    except:
                        pass

                # Estratégia 4: remover permissões especiais e tentar novamente
                try:
                    print(f"   ⚠️  Removendo atributos especiais e tentando novamente...")
                    subprocess.run(["sudo", "chattr", "-i", "-a", caminho_str], check=False, capture_output=True)
                    subprocess.run(["sudo", "chmod", "-R", "777", caminho_str], check=False, capture_output=True)
                    subprocess.run(["sudo", "rm", "-rf", caminho_str], check=False, capture_output=True)
                    if not caminho.exists():
                        print(f"   ✔ {descricao} removido após remover atributos")
                        return True
                except:
                    pass

                # Verificação final
                if not caminho.exists():
                    print(f"   ✔ {descricao} removido")
                    return True
                else:
                    print(f"   ❌ Falha crítica ao remover {descricao}")
                    return False

            # 4. Executar remoção
            print("\n🧹 Removendo componentes...")

            # Parar e remover serviço
            if service_path.exists():
                try:
                    print("   ⏹️  Parando serviço...")
                    subprocess.run(["sudo", "systemctl", "stop", "opencode-web.service"], check=False, capture_output=True)
                    subprocess.run(["sudo", "systemctl", "disable", "opencode-web.service"], check=False, capture_output=True)
                    forcar_remocao(service_path, f"Serviço {service_path}")
                except Exception as e:
                    print(f"   ⚠️  Erro ao remover serviço: {e}")

            # Daemon reload
            try:
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False, capture_output=True)
            except:
                pass

            # Remover todos os diretórios e binários com remoção forçada
            todos_caminhos = [
                (Path.home() / ".opencode", "~/.opencode (binário)"),
                (Path.home() / ".config" / "opencode", "~/.config/opencode (config)"),
                (Path.home() / ".cache" / "opencode", "~/.cache/opencode (cache)"),
                (Path.home() / ".local" / "share" / "opencode", "~/.local/share/opencode (banco de dados)"),
                (Path("/tmp/opencode"), "/tmp/opencode (temp)"),
                (Path.home() / ".local" / "bin" / "opencode", "~/.local/bin/opencode"),
                (Path("/usr/local/bin/opencode"), "/usr/local/bin/opencode"),
                (Path("/usr/bin/opencode"), "/usr/bin/opencode"),
            ]

            for caminho, descricao in todos_caminhos:
                forcar_remocao(caminho, descricao)

            # 5. Varredura final agressiva por qualquer resíduo
            print("\n   🔍 Varredura final por resíduos...")
            try:
                result = subprocess.run(
                    ["sudo", "find", "/home", "/usr/local", "/usr/bin", "/tmp",
                     "-iname", "*opencode*", "-o", "-iname", "*opencode-ai*", "-o", "-path", "*/.local/share/opencode*"],
                    capture_output=True, text=True, timeout=20
                )
                if result.stdout.strip():
                    residuos = [r for r in result.stdout.strip().split('\n') if r]
                    # Filtra apenas os caminhos que já foram tratados explicitamente
                    caminhos_tratados = [str(c) for c, _ in todos_caminhos]
                    residuos_filtrados = [r for r in residuos if r not in caminhos_tratados]
                    
                    if residuos_filtrados:
                        print(f"   Encontrados {len(residuos_filtrados)} resíduos adicionais:")
                        for res in residuos_filtrados:
                            print(f"   🗑️  Removendo: {res}")
                            subprocess.run(["sudo", "rm", "-rf", res], check=False, capture_output=True)
                        print("   ✔ Resíduos adicionais removidos")
                    else:
                        print("   Nenhum resíduo adicional encontrado")
                else:
                    print("   Nenhum resíduo encontrado")
            except Exception as e:
                print(f"   ⚠️  Erro na varredura: {e}")

            # 6. Verificação final de limpeza
            print("\n   🔎 Verificando limpeza completa...")
            pendentes = []
            for caminho, descricao in todos_caminhos:
                if caminho.exists():
                    pendentes.append(descricao)

            if pendentes:
                print(f"   ⚠️  Atenção: {len(pendentes)} item(ns) ainda existem:")
                for p in pendentes:
                    print(f"      - {p}")
                print("   Isso pode ser normal se houver outra instalação do OpenCode.")
            else:
                print("   ✔ Todos os componentes foram removidos com sucesso!")

            # Final
            print("\n" + "="*60)
            print("✅ OPENCODE COMPLETAMENTE REMOVIDO!")
            print("="*60)
            print("   Todos os arquivos, configurações e serviços foram removidos.")
            print("="*60)
            input("\nPressione Enter para voltar ao menu...")

        def opcao_gerar_script():
            """Mostra scripts prontos para copiar (Linux e Windows)"""
            print("\n" + "="*50)
            print(" SCRIPTS PARA INICIAR SERVIDOR")
            print("="*50)

            print("\n🐧 LINUX - Iniciar servidor:")
            print("─" * 50)
            print("""OPENCODE_SERVER_USERNAME=opencode
OPENCODE_SERVER_PASSWORD=sua_senha
opencode serve --hostname 0.0.0.0 --port 7860 --cors \"*\"""")

            print("\n🪟 WINDOWS - Script .bat:")
            print("─" * 50)
            print("""@echo off
title OpenCode Server
set OPENCODE_SERVER_USERNAME=opencode
set OPENCODE_SERVER_PASSWORD=sua_senha
opencode serve --port 7860 --hostname 127.0.0.1 --cors "*"
pause""")

            print("\n" + "="*50)
            input("Pressione Enter para voltar ao menu...")

        # Loop do Menu
        while True:
            print("\n" + "="*50)
            print("🤖 GERENCIADOR OPENCODE")
            print("="*50)
            print("[1] 📦  Instalar / Atualizar")
            print("[2] 🔄  Reiniciar Serviço")
            print("[3] 📊  Ver Status")
            print("[4] ⚙️  Reconfigurar Modo Web (Porta/Senha)")
            print("[5] 📝  Gerar Script Servidor")
            print("[6] 🗑️  Desinstalar OpenCode")
            print("[0] ↩️  Voltar")
            print("="*50)

            opt = input("\nEscolha uma opção: ").strip()

            if opt == '1': opcao_instalar()
            elif opt == '2': opcao_reiniciar()
            elif opt == '3': opcao_status()
            elif opt == '4': opcao_reconfigurar()
            elif opt == '5': opcao_gerar_script()
            elif opt == '6': opcao_desinstalar()
            elif opt == '0': break
            else: print("❌ Opção inválida.")

    def instala_opencode(self):
        """Instala o OpenCode (CLI AI) e configura o modo web com senha"""
        print("\n" + "="*60)
        print("🚀 INSTALAÇÃO DO OPENCODE (AI CLI TOOL)")
        print("="*60)

        # Pede senha para o modo web
        print("\n🔐 O OpenCode possui um modo web (interface browser).")
        senha_web = input("Digite uma senha para proteger o modo web: ").strip()
        if not senha_web:
            print("⚠️  Senha vazia! Gerando senha automática...")
            senha_web = self.generate_password(16)
            print(f"🔑 Senha gerada: {senha_web}")
            print("⚠️  GUARDE ESTA SENHA! Necessária para acessar o modo web.")

        # Pergunta sobre porta
        print("\n🌐 Configuração de porta para o modo web:")
        porta_input = input("Porta para o modo web (padrão: 7860, Enter para usar padrão): ").strip()
        porta_web = porta_input if porta_input else "7860"

        # Verificação de versão
        versao_local = None
        versao_remota = None
        precisa_instalar = True
        opencode_bin_path = None

        # 1. Tenta localizar o executável (busca ampla para achar instalações de usuários)
        search_paths = [
            Path.home() / ".opencode" / "bin" / "opencode",
            Path.home() / ".local" / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/usr/bin/opencode"),
        ]
        
        # Se não achar nos padrões, tenta um find rápido no /home
        for p in search_paths:
            if p.exists():
                opencode_bin_path = str(p)
                break
        
        if not opencode_bin_path:
            try:
                result = subprocess.run(
                    ["find", "/home", "-name", "opencode", "-type", "f", "-path", "*/bin/opencode"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    opencode_bin_path = result.stdout.strip().split('\n')[0]
            except Exception:
                pass

        # 2. Tenta pegar versão instalada usando o caminho encontrado
        if opencode_bin_path:
            try:
                result = subprocess.run([opencode_bin_path, '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    versao_local = result.stdout.strip().lstrip('v')
                    print(f"📦 Versão local detectada em {opencode_bin_path}: {versao_local}")
            except Exception:
                pass
        else:
            print("📦 OpenCode não encontrado no sistema.")

        # 3. Tenta pegar versão mais recente do GitHub
        try:
            import urllib.request
            url_api = "https://api.github.com/repos/anomalyco/opencode/releases/latest"
            req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                versao_remota = data.get('tag_name', '').lstrip('v')
                print(f"🌐 Última versão disponível: {versao_remota}")
        except Exception as e:
            print(f"⚠️  Não foi possível verificar a versão online: {e}")
            print("   Prosseguindo com instalação/atualização por segurança.")

        # 4. Decide o que fazer
        if versao_local and versao_remota:
            if versao_local == versao_remota:
                print("\n✅ Seu OpenCode já está na versão mais recente!")
                precisa_instalar = False
                # Pergunta se quer reconfigurar mesmo assim
                reconfigurar = input("Deseja reconfigurar o modo web e firewall? (s/n): ").strip().lower()
                if reconfigurar != 's':
                    return
            elif versao_local < versao_remota:
                print(f"\n🔄 Atualização disponível! ({versao_local} -> {versao_remota})")
            else:
                print(f"\n📦 Sua versão local ({versao_local}) parece mais recente que a remota ({versao_remota}).")
                precisa_instalar = False

        if precisa_instalar:
            # Confirmação
            print("\n" + "="*60)
            print("📋 RESUMO DA OPERAÇÃO:")
            if versao_local:
                print(f"   - Ação: Atualizar de {versao_local} para {versao_remota}")
            else:
                print(f"   - Ação: Instalação nova")
            print(f"   - Modo web: ATIVADO")
            print(f"   - Porta do modo web: {porta_web}")
            print(f"   - Senha do modo web: {'*' * len(senha_web)}")
            print("="*60)

            confirmar = input("\n✅ Deseja prosseguir? (s/n): ").strip().lower()
            if confirmar != 's':
                print("Operação cancelada.")
                return

            # Executa instalação
            print("\n📦 Baixando e executando script de instalação...")
            print("⏳ Aguarde, isso pode levar alguns minutos...\n")

            try:
                subprocess.run(
                    "curl -fsSL https://opencode.ai/install | bash",
                    shell=True,
                    check=True
                )
                print("\n✅ OpenCode instalado/atualizado com sucesso!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Erro durante a instalação: {e}")
                print("Verifique sua conexão e tente novamente.")
                return
            except FileNotFoundError:
                print("\n❌ curl não encontrado. Instalando...")
                subprocess.run(["sudo", "apt", "update"], check=False)
                subprocess.run(["sudo", "apt", "install", "-y", "curl"], check=True)
                print("Tentando novamente...")
                try:
                    subprocess.run(
                        "curl -fsSL https://opencode.ai/install | bash",
                        shell=True,
                        check=True
                    )
                    print("\n✅ OpenCode instalado/atualizado com sucesso!")
                except Exception as e2:
                    print(f"\n❌ Erro na segunda tentativa: {e2}")
                    return

        # Limpeza de resíduos da instalação
        print("\n🧹 Limpando arquivos temporários de instalação...")
        subprocess.run(["sudo", "rm", "-rf", "/tmp/opencode"], check=False)

        # Configura variáveis de ambiente para o modo web
        print("\n⚙️ Configurando modo web...")

        # Determina onde salvar as configurações
        opencode_config_dir = Path.home() / ".config" / "opencode"
        opencode_config_dir.mkdir(parents=True, exist_ok=True)

        # Salva configuração do modo web
        config_file = opencode_config_dir / "opencode.json"
        
        # Tenta ler config existente ou cria nova
        config_data = {}
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            except:
                pass

        # Remove chave antiga "web" que causa erro "Unrecognized key" no v1.15+
        config_data.pop("web", None)

        # Adiciona/atualiza configuração do web mode (formato correto v1.15+)
        config_data["server"] = {
            "port": int(porta_web),
            "hostname": "0.0.0.0"
        }

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        print(f"✔ Configuração salva em: {config_file}")

        # Cria serviço systemd para iniciar no boot
        print("\n️ Configurando inicialização automática no boot...")

        # 1. Detectar caminho do executável e usuário correto
        opencode_bin = None
        service_user = os.getenv('USER', 'root')
        service_home = os.path.expanduser(f"~{service_user}")

        # Lista de caminhos prováveis
        search_paths = [
            Path.home() / ".opencode" / "bin" / "opencode",
            Path.home() / ".local" / "bin" / "opencode",
            Path("/usr/local/bin/opencode"),
            Path("/usr/bin/opencode"),
        ]

        for p in search_paths:
            if p.exists():
                opencode_bin = str(p)
                break

        # Se não achou nos caminhos padrão, tenta um find rápido
        if not opencode_bin:
            try:
                result = subprocess.run(
                    ["find", "/home", "-name", "opencode", "-type", "f"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    opencode_bin = result.stdout.strip().split('/')[0]
                    # Tenta inferir o usuário dono da pasta
                    service_user = opencode_bin.split('/')[2] # Assume /home/USUARIO/...
                    service_home = f"/home/{service_user}"
            except Exception:
                pass

        if not opencode_bin:
            print("⚠️  Não foi possível localizar o executável do OpenCode automaticamente.")
            print("   O serviço systemd não será criado. Você precisará iniciar manualmente.")
        else:
            print(f"📍 Executável encontrado em: {opencode_bin}")
            print(f"👤 Configurando serviço para usuário: {service_user}")

            service_path = Path("/etc/systemd/system/opencode-web.service")
            service_content = textwrap.dedent(f"""\
                [Unit]
                Description=OpenCode Web Server
                After=network-online.target
                Wants=network-online.target

                [Service]
                Type=simple
                User={service_user}
                Environment=HOME={service_home}
                Environment=PATH={service_home}/.opencode/bin:{service_home}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
                Environment=OPENCODE_SERVER_PASSWORD={senha_web}
                ExecStart={opencode_bin} serve --hostname 0.0.0.0 --port {porta_web} --cors "*"
                Restart=on-failure
                RestartSec=10

                [Install]
                WantedBy=multi-user.target
            """)

            try:
                # Tenta escrever o arquivo. Se falhar por permissão, usa sudo.
                try:
                    service_path.write_text(service_content)
                except PermissionError:
                    # Cria um arquivo temporário e move com sudo
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as tmp:
                        tmp.write(service_content)
                        tmp_path = tmp.name
                    subprocess.run(["sudo", "mv", tmp_path, str(service_path)], check=True)
                    subprocess.run(["sudo", "chmod", "644", str(service_path)], check=True)
                
                print(f"✔ Serviço criado em: {service_path}")

                # Recarrega e habilita o serviço
                subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
                subprocess.run(["sudo", "systemctl", "enable", "opencode-web.service"], check=True)
                subprocess.run(["sudo", "systemctl", "restart", "opencode-web.service"], check=True)
                print("✔ Serviço habilitado e reiniciado com sucesso!")
            except Exception as e:
                print(f"️  Erro ao criar serviço systemd: {e}")

        # Libera porta no firewall
        print(f"\n🔓 Liberando porta {porta_web} no firewall...")

        # Tenta UFW (firewall padrão do Ubuntu)
        try:
            ufw_check = subprocess.run(
                ["sudo", "ufw", "status"],
                capture_output=True, text=True
            )
            if "active" in ufw_check.stdout.lower():
                subprocess.run(
                    ["sudo", "ufw", "allow", str(porta_web), "tcp"],
                    check=True
                )
                print(f"✔ Porta {porta_web} liberada no UFW")
            else:
                print("  UFW inativo, pulando...")
        except Exception as e:
            print(f"  UFW não encontrado: {e}")

        # Tenta iptables SEMPRE (independente do UFW)
        # IMPORTANTE: Usa -I (insert) no topo da cadeia para garantir que a regra
        # seja processada ANTES de qualquer regra de REJECT/DROP (comum no Oracle Cloud)
        try:
            # Verifica se regra já existe
            check_result = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta_web), "-j", "ACCEPT"],
                capture_output=True
            )
            if check_result.returncode == 0:
                print(f"  Porta {porta_web} já liberada no iptables")
            else:
                # Insere no TOPO da cadeia INPUT (posição 1) para evitar conflito com regras de REJECT
                subprocess.run(
                    ["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(porta_web), "-j", "ACCEPT"],
                    check=True
                )
                print(f"✔ Porta {porta_web} liberada no iptables (inserida no topo da cadeia)")

                # Salva regras iptables para persistir no boot
                # Tenta netfilter-persistent (padrão Debian/Ubuntu)
                if shutil.which("netfilter-persistent"):
                    subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)
                    print("  Regras salvas via netfilter-persistent")
                elif shutil.which("iptables-save"):
                    subprocess.run(
                        ["sudo", "sh", "-c", "iptables-save > /etc/iptables.rules"],
                        check=False
                    )
                    print("  Regras salvas em /etc/iptables.rules")
                else:
                    print("  ⚠️  Não foi encontrado utilitário para salvar regras iptables automaticamente.")
        except Exception as e:
            print(f"  ⚠️  Não foi possível configurar iptables: {e}")

        # Instruções finais
        print("\n" + "="*60)
        print("🎉 OPERAÇÃO CONCLUÍDA!")
        print("="*60)
        print(f"\n📌 INFORMAÇÕES DE ACESSO:")
        print(f"   Usuário do Sistema (para rodar comandos): {service_user}")
        print(f"   Endereço Web: http://<seu_ip>:{porta_web}")
        print(f"   Usuário Web: opencode")
        print(f"   Senha de Acesso: {senha_web}")
        print(f"\n💡 COMANDO PARA INICIAR O SERVIDOR:")
        print(f"   Rode este comando como o usuário '{service_user}':")
        print(f"   OPENCODE_SERVER_PASSWORD={senha_web} opencode serve --hostname 0.0.0.0 --port {porta_web} --cors \"*\"")
        print(f"\n🛠️ COMANDOS ÚTEIS:")
        print(f"   opencode              # Inicia no terminal (modo interativo)")
        print(f"   opencode web          # Inicia modo web (servidor)")
        print(f"   opencode --help       # Ajuda completa")
        print(f"   systemctl status opencode-web  # Ver status do serviço automático")
        print("\n⚠️  IMPORTANTE:")
        print(f"   - Guarde a senha '{senha_web}' em local seguro!")
        print(f"   - O serviço systemd foi configurado para iniciar no boot.")
        print(f"   - Se o serviço falhar, inicie manualmente com o comando acima.")
        print("="*60)
