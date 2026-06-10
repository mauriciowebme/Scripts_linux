import os
import re
import secrets
import time
import subprocess
from urllib.parse import quote_plus

from install_master.core.docker_base import DockerBase


class MixinWhatsApp(DockerBase):
    def instala_evolution_api_whatsapp(self):
        print("Iniciando instalação Evolution API WhatsApp:")
        
        # Preparar diretórios
        caminho_evolution = f'{self.install_principal}/evolution_api_whatsapp'
        caminho_store = f'{caminho_evolution}/store'
        caminho_instances = f'{caminho_evolution}/instances'
        caminho_env = f'{caminho_evolution}/config'
        
        os.makedirs(caminho_store, exist_ok=True)
        os.makedirs(caminho_instances, exist_ok=True)
        os.makedirs(caminho_env, exist_ok=True)
        os.chmod(caminho_evolution, 0o777)
        
        # Verificar se o arquivo .env já existe ANTES de pedir configurações
        env_file_path = f'{caminho_env}/.env'
        usar_config_existente = False
        
        if os.path.exists(env_file_path):
            print("\n⚠️  ATENÇÃO: Arquivo .env já existe!")
            print(f"Localização: {env_file_path}")
            resposta = input("Deseja usar as configurações existentes? (s/n) [padrão: s]: ").strip().lower()
            if resposta != 'n':
                usar_config_existente = True
                print("✅ Usando arquivo .env existente.")
                print("💡 A instalação continuará com as configurações já salvas.")
            else:
                print("⚠️  As configurações serão solicitadas para sobrescrever o arquivo existente...")
        
        # Só solicita configurações se NÃO estiver usando arquivo existente
        if not usar_config_existente:
            # Gerar chave de autenticação forte automaticamente
            api_key = secrets.token_urlsafe(32)
            print("\n=== CHAVE DE AUTENTICAÇÃO GERADA ===")
            print(f"AUTHENTICATION_API_KEY: {api_key}")
            print("⚠️  Guarde esta chave em local seguro!")
            print("Ela será salva automaticamente no arquivo .env")
            
            # Configurar versão do Telefone
            print("\n=== CONFIGURAÇÃO DA VERSÃO DO TELEFONE ===")
            print("A versão do Telefone determina qual cliente será usado pela API.")
            print("Versões mais recentes podem ter mais recursos, mas versões estáveis são mais confiáveis.")
            yarn_version = input("Digite a versão do Telefone (padrão: 1.22.22): ").strip() or "1.22.22"

            # Configurar versão do WhatsAppWeb (para evitar banimento)
            print("\n=== CONFIGURAÇÃO DA VERSÃO DO WhatsAppWeb ===")
            print("Esta configuração simula uma versão específica do WhatsApp no WhatsAppWeb.")
            print("Ajuda a evitar detecção e possível banimento pela API oficial do WhatsApp.")
            phone_version = input("Digite a versão do WhatsAppWeb (padrão: 2.3000.1028956288): ").strip() or "2.3000.1028956288"

            # Configurar URL do servidor
            print("\n=== CONFIGURAÇÃO DA URL DO SERVIDOR ===")
            print("Esta URL é usada para webhooks e integrações externas.")
            print("Exemplo: http://seu-ip:porta ou https://seu-dominio.com")
            server_url = input("Digite a URL do servidor (opcional, pressione Enter para pular): ").strip()
            
            # Configuração do banco de dados PostgreSQL
            print("\n=== CONFIGURAÇÃO DO BANCO DE DADOS POSTGRESQL ===")
            print("Informe os dados de conexão com o PostgreSQL:")
            
            host_db = input("Host do PostgreSQL (ex: postgres_17, localhost, IP): ").strip()
            porta_db = input("Porta do PostgreSQL (padrão: 5435): ").strip() or "5435"
            nome_banco = input("Nome do banco de dados (padrão: evolution): ").strip() or "evolution"
            usuario_db = input("Nome do usuário do banco (padrão: evolution): ").strip() or "evolution"
            senha_db = input("Senha do usuário: ").strip()
            
            # Validação dos campos obrigatórios
            if not host_db or not nome_banco or not usuario_db or not senha_db:
                print("ERRO: Todos os campos são obrigatórios!")
                return
            
            # Validação de caracteres especiais que podem causar problemas na URI
            
            # Caracteres que precisam ser escapados na URI
            caracteres_problematicos = r'[@:/\?#\[\]!$&\'()*+,;=]'
            
            if re.search(caracteres_problematicos, usuario_db):
                print("⚠️  AVISO: O nome de usuário contém caracteres especiais que serão codificados na URI.")
                usuario_db = quote_plus(usuario_db)
            
            if re.search(caracteres_problematicos, senha_db):
                print("⚠️  AVISO: A senha contém caracteres especiais que serão codificados na URI.")
                senha_db = quote_plus(senha_db)
            
            if re.search(caracteres_problematicos, nome_banco):
                print("⚠️  AVISO: O nome do banco contém caracteres especiais que serão codificados na URI.")
                nome_banco = quote_plus(nome_banco)
            
            # Construir URI de conexão com os dados fornecidos (já codificados se necessário)
            database_uri = f"postgresql://{usuario_db}:{senha_db}@{host_db}:{porta_db}/{nome_banco}?schema=public"
            
            # Criar/sobrescrever o arquivo .env
            with open(env_file_path, 'w') as f:
                f.write(f"AUTHENTICATION_API_KEY={api_key}\n")
                f.write(f"DATABASE_CONNECTION_URI={database_uri}\n")
                f.write(f"YARN_VERSION={yarn_version}\n")
                f.write(f"CONFIG_SESSION_PHONE_VERSION={phone_version}\n")
                if server_url:
                    f.write(f"SERVER_URL={server_url}\n")
            
            # Definir permissões restritas no arquivo .env (apenas owner pode ler)
            os.chmod(env_file_path, 0o600)
            print("✅ Arquivo .env criado com sucesso!")
        
        portas = self.escolher_porta_disponivel()
        
        # Construir o comando docker usando --env-file (credenciais não aparecem em docker inspect)
        container = f"""docker run -d \
                        --name evolution_api_whatsapp \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -p {portas[0]}:8080 \
                        --env-file {env_file_path} \
                        -e TZ="America/Sao_Paulo" \
                        -e DATABASE_ENABLED="true" \
                        -e DATABASE_PROVIDER="postgresql" \
                        -e CACHE_REDIS_ENABLED="false" \
                        -e CACHE_LOCAL_ENABLED="true" \
                        -v {caminho_store}:/evolution/store \
                        -v {caminho_instances}:/evolution/instances \
                        atendai/evolution-api
                    """
        
        self.remove_container('evolution_api_whatsapp')
        resultados = self.executar_comandos([container])
        
        self.cria_rede_docker(associar_container_nome='evolution_api_whatsapp', numero_rede=1)
        
        print("\n" + "="*60)
        print("Instalação do Evolution API WhatsApp concluída.")
        print("="*60)
        print(f"Porta de acesso: {portas[0]}")
        
        # Só exibe detalhes se foram coletados (novo .env criado)
        if not usar_config_existente:
            print(f"API Key: {api_key}")
            print(f"Versão WhatsApp Web: {yarn_version}")
            print(f"Versão do Telefone: {phone_version}")
            if server_url:
                print(f"URL do Servidor: {server_url}")
            print(f"Banco de dados: {host_db}:{porta_db}/{nome_banco}")
        else:
            print("📋 Configurações: Usando arquivo .env existente")
            print(f"   (Verifique o arquivo para detalhes: {env_file_path})")
        
        print(f"Cache: Local (Redis desabilitado)")
        print(f"Diretório store: {caminho_store}")
        print(f"Diretório instances: {caminho_instances}")
        print(f"\nARQUIVO DE CONFIGURAÇÃO (.env):")
        print(f"  Localização: {env_file_path}")
        print(f"  Permissões: 600 (apenas owner pode ler)")
        print(f"  Contém: API_KEY, DATABASE_URI, YARN_VERSION, PHONE_VERSION, SERVER_URL (opcional)")
        print("\nIPs possíveis para acesso:")
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f"\nAcesse: http://<seu_ip>:{portas[0]}")
        print("="*60)
            
    def instala_waha_whatsapp(self):
        print("Iniciando instalação WAHA WhatsApp HTTP API (devlikeapro/waha):")

        caminho_waha = f'{self.install_principal}/waha_whatsapp'
        caminho_sessions = f'{caminho_waha}/sessions'
        caminho_media = f'{caminho_waha}/media'
        caminho_env = f'{caminho_waha}/config'

        portas = self.escolher_porta_disponivel()

        os.makedirs(caminho_waha, exist_ok=True)
        os.makedirs(caminho_sessions, exist_ok=True)
        os.makedirs(caminho_media, exist_ok=True)
        os.makedirs(caminho_env, exist_ok=True)
        os.chmod(caminho_waha, 0o777)

        env_file_path = f'{caminho_env}/.env'
        usar_config_existente = False

        if os.path.exists(env_file_path):
            print("\n⚠  ATENÇÃO: Arquivo .env já existe para o WAHA!")
            print(f"Localização: {env_file_path}")
            resposta = input("Deseja usar as configurações existentes? (s/n) [padrão: s]: ").strip().lower()
            if resposta != 'n':
                usar_config_existente = True
                print("✅ Usando arquivo .env existente.")
            else:
                print("As novas configurações serão solicitadas e sobrescreverão o arquivo.")

        api_key = dashboard_user = dashboard_password = None
        swagger_user = swagger_password = None
        base_url = engine_padrao = None
        dashboard_enabled = swagger_enabled = None

        if not usar_config_existente:
            api_key = secrets.token_hex(16)
            print("\n=== CHAVE DE AUTENTICAÇÃO GERADA ===")
            print(f"WAHA_API_KEY: {api_key}")
            print("Anote esta chave, ela será necessária para proteger as chamadas API.")

            dashboard_user = input("\nUsuário do dashboard (padrão: admin): ").strip() or "admin"
            dashboard_password = input("Senha do dashboard (Enter para gerar automaticamente): ").strip()
            if not dashboard_password:
                dashboard_password = secrets.token_urlsafe(16)
                print(f"Senha do dashboard gerada: {dashboard_password}")

            swagger_user = input("\nUsuário do Swagger (padrão: admin): ").strip() or "admin"
            swagger_password = input("Senha do Swagger (Enter para gerar automaticamente): ").strip()
            if not swagger_password:
                swagger_password = secrets.token_urlsafe(16)
                print(f"Senha do Swagger gerada: {swagger_password}")

            base_url_padrao = f"http://localhost:{portas[0]}"
            base_url = input(f"\nBase URL pública da API (padrão: {base_url_padrao}): ").strip() or base_url_padrao

            engine_padrao = input("\nEngine padrão do WhatsApp (WEBJS/GOWS/NOWEB) [WEBJS]: ").strip().upper() or "WEBJS"

            dash_enabled_input = input("Deseja habilitar o dashboard web? (s/n) [s]: ").strip().lower()
            dashboard_enabled = "False" if dash_enabled_input == 'n' else "True"

            swagger_enabled_input = input("Deseja habilitar o Swagger? (s/n) [s]: ").strip().lower()
            swagger_enabled = "False" if swagger_enabled_input == 'n' else "True"

            with open(env_file_path, 'w') as f:
                f.write(f"WAHA_API_KEY={api_key}\n")
                f.write(f"WAHA_DASHBOARD_USERNAME={dashboard_user}\n")
                f.write(f"WAHA_DASHBOARD_PASSWORD={dashboard_password}\n")
                f.write(f"WHATSAPP_SWAGGER_USERNAME={swagger_user}\n")
                f.write(f"WHATSAPP_SWAGGER_PASSWORD={swagger_password}\n")
                f.write(f"WAHA_DASHBOARD_ENABLED={dashboard_enabled}\n")
                f.write(f"WHATSAPP_SWAGGER_ENABLED={swagger_enabled}\n")
                f.write(f"WAHA_BASE_URL={base_url}\n")
                f.write(f"WHATSAPP_DEFAULT_ENGINE={engine_padrao}\n")
                f.write("WAHA_MEDIA_STORAGE=LOCAL\n")
                f.write("WHATSAPP_FILES_FOLDER=/app/.media\n")
                f.write("WHATSAPP_FILES_LIFETIME=0\n")
                f.write("WAHA_LOG_FORMAT=JSON\n")
                f.write("WAHA_LOG_LEVEL=info\n")
                f.write("WAHA_PRINT_QR=False\n")

            os.chmod(env_file_path, 0o600)
            print("✅ Arquivo .env criado com sucesso!")

        container = f"""docker run -d \
                        --name waha_whatsapp \
                        --restart=unless-stopped \
                        --memory=512m \
                        --cpus=1 \
                        -p {portas[0]}:3000 \
                        --env-file {env_file_path} \
                        -e TZ="America/Sao_Paulo" \
                        -v {caminho_sessions}:/app/.sessions \
                        -v {caminho_media}:/app/.media \
                        devlikeapro/waha
                    """

        self.remove_container('waha_whatsapp')
        resultados = self.executar_comandos([container])

        self.cria_rede_docker(associar_container_nome='waha_whatsapp', numero_rede=1)

        print("\n" + "="*60)
        print("Instalação do WAHA WhatsApp concluída.")
        print("="*60)
        print(f"Porta de acesso: {portas[0]}")

        if not usar_config_existente:
            print(f"API Key: {api_key}")
            print(f"Usuário Dashboard: {dashboard_user}")
            print(f"Senha Dashboard: {dashboard_password}")
            print(f"Usuário Swagger: {swagger_user}")
            print(f"Senha Swagger: {swagger_password}")
            print(f"Base URL configurada: {base_url}")
            print(f"Engine padrão: {engine_padrao}")
            print(f"Dashboard habilitado: {dashboard_enabled}")
            print(f"Swagger habilitado: {swagger_enabled}")
        else:
            print("Usando configurações existentes do arquivo .env.")
            print(f"Consulte: {env_file_path}")

        print(f"Diretório Sessions: {caminho_sessions}")
        print(f"Diretório Media: {caminho_media}")
        print("\nArquivo .env")
        print(f"  Localização: {env_file_path}")
        print(f"  Permissões: 600 (somente proprietário)")

        print("\nIPs disponíveis para acesso:")
        comandos = [
            "hostname -I | tr ' ' '\\n'",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f"\nDashboard: http://<seu_ip>:{portas[0]}/dashboard")
        print(f"Swagger:   http://<seu_ip>:{portas[0]}/swagger")
        print("="*60)
