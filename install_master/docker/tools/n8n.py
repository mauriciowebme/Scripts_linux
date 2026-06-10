import os
import shlex
import shutil
import time
import subprocess

from install_master.core.docker_base import DockerBase


class MixinN8N(DockerBase):
    def instalar_n8n(self):
        print("Iniciando instalação do n8n (workflow automation).")
        print("\n" + "="*60)
        
        # PASSO 1: Pergunta tipo de instalação
        print("Tipo de instalação:")
        print("1 - Simples (SQLite local, sem banco externo)")
        print("2 - Main (servidor principal com PostgreSQL e Redis)")
        print("3 - Worker (processador de tarefas)")
        tentativas = 0
        is_simples = False
        is_main = False
        is_worker = False
        while tentativas < 3:
            tipo_instalacao = input("Digite sua escolha (1, 2 ou 3): ").strip()
            is_simples = tipo_instalacao == "1"
            is_main = tipo_instalacao == "2"
            is_worker = tipo_instalacao == "3"
            if is_simples or is_main or is_worker:
                break
            tentativas += 1
            print(f"❌ Opção inválida! ({tentativas}/3 tentativas)")
        if not (is_simples or is_main or is_worker):
            print("❌ Nenhuma opção válida após 3 tentativas. Retornando ao menu principal...")
            return
        
        # Define o sufixo e caminhos baseado no tipo escolhido
        if is_simples:
            tipo_suffix = "simples"
        elif is_main:
            tipo_suffix = "main"
        else:
            tipo_suffix = "worker"
            
        caminho_n8n = f'{self.install_principal}/n8n_{tipo_suffix}'
        env_file_path = os.path.join(caminho_n8n, 'n8n.env')
        container_name = f"n8n_{tipo_suffix}"

        # PASSO 2: Verificação de instalação anterior e decisão manter/limpar
        try:
            dados_existentes = os.path.isdir(caminho_n8n) and any(os.scandir(caminho_n8n))
        except Exception:
            dados_existentes = os.path.isdir(caminho_n8n)
        
        clean_install = False
        pending_delete_dir = None
        if dados_existentes:
            print("\n=== Instalação existente detectada (arquivos) ===")
            try:
                qtd = len(list(os.scandir(caminho_n8n)))
            except Exception:
                qtd = -1
            print(f" - Pasta de dados: {caminho_n8n} (itens: {qtd if qtd>=0 else 'desconhecido'})")
            print("\nO que deseja fazer?")
            if is_main:
                print("Nota: Ao escolher nova instalação, o banco PostgreSQL também será limpo.")
            elif is_worker:
                print("Nota: A nova instalação do worker não alterará o banco PostgreSQL compartilhado.")
            print("1) Manter dados (recomendado)")
            print("2) Nova instalação limpa (apagar pasta de dados)")
            print("3) Cancelar")
            escolha = input("Escolha [1/2/3] (padrão: 1): ").strip() or "1"
            if escolha == "3":
                print("Operação cancelada pelo usuário.")
                return
            if escolha == "2":
                # Remoção da pasta será feita após as ações adicionais abaixo
                pending_delete_dir = caminho_n8n
                if is_main:
                    print(f"Pasta {caminho_n8n} será removida após a limpeza do banco.")
                else:
                    print(f"Pasta {caminho_n8n} será removida para preparar a nova instalação.")
                clean_install = True
            else:
                print("Mantendo a pasta de dados existente.")
                clean_install = False

        # Garante existência e permissões da pasta de dados apenas se NÃO for instalação limpa
        if not clean_install:
            os.makedirs(caminho_n8n, exist_ok=True)
            os.chmod(caminho_n8n, 0o777)
        
        # PASSO 3: Reutilização automática do n8n.env somente se manter dados
        reuse_env = False
        env_data = {}
        if (not clean_install) and os.path.isfile(env_file_path):
            print(f"\nReutilizando arquivo de configuração existente: {env_file_path}")
            reuse_env = True
            try:
                with open(env_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            env_data[k.strip()] = v.strip()
                print("✔ Configurações carregadas do arquivo existente.")
            except Exception as ex:
                print(f"Aviso: erro ao ler {env_file_path}: {ex}")
                reuse_env = False
        
        # PASSO 4: Coletar configurações DB/Redis apenas se não reaproveitar
        postgres_host = ""
        postgres_db = ""
        postgres_user = ""
        postgres_password = ""
        postgres_port = ""
        redis_host = ""
        redis_port = ""
        redis_password = ""
        
        if (is_main or is_worker) and not reuse_env:
            print("\n" + "="*60)
            print("Configurações de banco de dados PostgreSQL:")
            postgres_host = input("Host do PostgreSQL (padrão: postgres): ").strip() or "postgres"
            postgres_port = input("Porta do PostgreSQL (padrão: 5432): ").strip() or "5432"
            postgres_db = input("Nome do banco (padrão: N8N): ").strip() or "N8N"
            postgres_user = input("Usuário do banco (padrão: N8N): ").strip() or "N8N"
            postgres_password = input(f"Senha do usuário '{postgres_user}' do PostgreSQL: ").strip()
            
            if not postgres_password:
                postgres_password = self.generate_password()
                print("⚠️ Senha gerada automaticamente para o PostgreSQL.")
            
            print("\n" + "="*60)
            print("Configurações Redis (fila):")
            redis_host = input("Host do Redis (padrão: redis): ").strip() or "redis"
            redis_port = input("Porta do Redis (padrão: 6379): ").strip() or "6379"
            redis_password = input("Senha do Redis (deixe vazio se não tiver): ").strip()
        elif (is_main or is_worker) and reuse_env:
            # Carrega do env_data
            postgres_host = env_data.get('DB_POSTGRESDB_HOST', 'postgres')
            postgres_port = env_data.get('DB_POSTGRESDB_PORT', '5432')
            postgres_db = env_data.get('DB_POSTGRESDB_DATABASE', 'N8N')
            postgres_user = env_data.get('DB_POSTGRESDB_USER', 'N8N')
            postgres_password = env_data.get('DB_POSTGRESDB_PASSWORD', '')
            redis_host = env_data.get('QUEUE_BULL_REDIS_HOST', 'redis')
            redis_port = env_data.get('QUEUE_BULL_REDIS_PORT', '6379')
            redis_password = env_data.get('QUEUE_BULL_REDIS_PASSWORD', '')

        # PASSO 4.1: Se usuário escolheu nova instalação no Main, limpar o banco automaticamente
        if is_main and clean_install:
            # Garante senha caso reuse_env não tenha trazido
            if not postgres_password:
                postgres_password = self.generate_password()
                print("[!] Senha do owner do banco estava vazia e foi gerada automaticamente.")
            try:
                print("\n=== Limpando banco de dados (DROP e recriação) ===")
                print(f"Banco: '{postgres_db}' em {postgres_host}:{postgres_port} (owner: {postgres_user})")
                self.limpar_banco_postgres(postgres_host, postgres_port, postgres_db, postgres_user, postgres_password)
                print("✔ Banco de dados limpo e recriado com sucesso.")
            except Exception as ex:
                print(f"Aviso: falha ao limpar o banco de dados: {ex}")
        
        # Após limpeza do banco (se aplicável), remover a pasta de dados se estiver pendente
        if clean_install and pending_delete_dir:
            try:
                if os.path.exists(pending_delete_dir):
                    shutil.rmtree(pending_delete_dir, ignore_errors=True)
                    print(f"Pasta {pending_delete_dir} removida para nova instalação.")
            except Exception as ex:
                print(f"Aviso: não foi possível remover {pending_delete_dir}: {ex}")

        # Garantia final: a pasta de dados do n8n precisa existir e ser gravável
        # para que o usuário 'node' dentro do container consiga criar /home/node/.n8n/config
        try:
            os.makedirs(caminho_n8n, exist_ok=True)
            os.chmod(caminho_n8n, 0o777)
            nodes_dir = os.path.join(caminho_n8n, 'nodes')
            os.makedirs(nodes_dir, exist_ok=True)
            try:
                os.chmod(nodes_dir, 0o777)
            except Exception:
                pass
        except Exception:
            pass
        # PASSO 5: Configurações específicas do Main ou Simples (domínio, chave, porta)
        n8n_host = ""
        webhook_url = ""
        encryption_key = ""
        porta_publicar = ""
        
        if is_main or is_simples:
            print("\n" + "="*60)
            tipo_texto = "servidor" if is_main else "instalação simples"
            print(f"Configurações do {tipo_texto}:")
            
            if reuse_env:
                n8n_host = env_data.get('N8N_HOST', '')
                encryption_key = env_data.get('N8N_ENCRYPTION_KEY', '')
                # Se estiver reutilizando env, mas a chave estiver ausente em modo Main, gere uma nova
                if is_main and not encryption_key:
                    try:
                        encryption_key = self.generate_password(32)
                        print(f"?? Chave de encriptação ausente no n8n.env. Gerada: {encryption_key}")
                        print("?? GUARDE ESTA CHAVE! Necessária para descriptografar credenciais.")
                        # Garante que o env_data contenha a chave para persistência adiante
                        env_data['N8N_ENCRYPTION_KEY'] = encryption_key
                    except Exception as ex:
                        print(f"Aviso: falha ao gerar chave de encriptação: {ex}")
                porta_publicar = "5678"  # Porta padrão quando reutilizando
            else:
                n8n_host = input("Domínio público (ex: n8n.seudominio.com, deixe vazio para pular): ").strip()
                
                if not is_simples:  # Encryption key só é necessário para Main com banco
                    encryption_key = input("Chave de encriptação (deixe vazio para gerar): ").strip()
                    if not encryption_key:
                        encryption_key = self.generate_password(32)
                        print(f"⚠️ Chave gerada: {encryption_key}")
                        print("⚠️ GUARDE ESTA CHAVE! Necessária para descriptografar credenciais.")
                
                porta_publicar = input("Porta para expor (padrão: 5678): ").strip() or "5678"
            
            if n8n_host:
                webhook_url = f"https://{n8n_host}/"
                print(f"✔ Webhook URL: {webhook_url}")

        # PASSO 5.1: Concorrência de workers (apenas Simples e Worker)
        # Worker: solicitar a N8N_ENCRYPTION_KEY usada no Main
        if is_worker and not reuse_env:
            encryption_key = input("Informe a mesma N8N_ENCRYPTION_KEY usada no servidor Main: ").strip()
            if not encryption_key:
                print("Aviso: N8N_ENCRYPTION_KEY nao informada no Worker; workflows com credenciais podem falhar.")
        elif is_worker and reuse_env:
            encryption_key = env_data.get('N8N_ENCRYPTION_KEY', encryption_key)
        worker_concurrency = "10"
        if is_simples or is_worker:
            # Segue o mesmo padrão de entrada com fallback: input(...).strip() or "10"
            worker_concurrency = (
                env_data.get('N8N_WORKER_CONCURRENCY', '') if reuse_env else input("Quantidade de processos em paralelo (padrão: 10): ").strip()
            ) or "10"
            # Sanitiza valor inválido
            if not str(worker_concurrency).isdigit() or int(worker_concurrency) < 1:
                worker_concurrency = "10"
        
        # PASSO 6: Constrói comando base do container
        comando_base = f"""docker run -d \
            --name {container_name} \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -v {caminho_n8n}:/home/node/.n8n"""
        
        # Variáveis de ambiente - diferentes para cada tipo
        if is_simples:
            # Instalação simples: sem banco externo, sem Redis, sem workers
            # Adiciona variáveis recomendadas para evitar warnings
            env_vars = f""" \
            -e DB_SQLITE_POOL_SIZE=3 \
            -e N8N_RUNNERS_ENABLED=true \
            -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
            -e N8N_GIT_NODE_DISABLE_BARE_REPOS=true \
            -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true"""
        else:
            # Main ou Worker: com PostgreSQL e Redis
            env_vars = f""" \
            -e DB_TYPE=postgresdb \
            -e DB_POSTGRESDB_HOST={shlex.quote(str(postgres_host))} \
            -e DB_POSTGRESDB_PORT={shlex.quote(str(postgres_port))} \
            -e DB_POSTGRESDB_DATABASE={shlex.quote(str(postgres_db))} \
            -e DB_POSTGRESDB_USER={shlex.quote(str(postgres_user))} \
            -e DB_POSTGRESDB_PASSWORD={shlex.quote(str(postgres_password))} \
            -e QUEUE_BULL_REDIS_HOST={shlex.quote(str(redis_host))} \
            -e QUEUE_BULL_REDIS_PORT={shlex.quote(str(redis_port))} \
            -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
            -e N8N_RUNNERS_ENABLED=true \
            -e N8N_BLOCK_ENV_ACCESS_IN_NODE=false \
            -e N8N_GIT_NODE_DISABLE_BARE_REPOS=true"""
        
        # Adiciona senha do Redis se informada (só para Main/Worker)
        if redis_password and not is_simples:
            env_vars += f""" \
            -e QUEUE_BULL_REDIS_PASSWORD={shlex.quote(str(redis_password))}"""

        # Configurações específicas por tipo
        if is_simples:
            # Instalação simples: apenas configurações básicas
            if n8n_host:
                env_vars += f""" \
            -e N8N_HOST={shlex.quote(str(n8n_host))} \
            -e N8N_PROTOCOL=https \
            -e WEBHOOK_URL={shlex.quote(str(webhook_url))} \
            -e N8N_PROXY_HOPS=1 \
            -e N8N_SECURE_COOKIE=true"""
            
            # Porta exposta
            env_vars += f""" \
            -p {porta_publicar}:5678"""
            # Limita processos em paralelo (aplicado também no simples; sem efeito no main)
            env_vars += f""" \
            -e N8N_WORKER_CONCURRENCY={shlex.quote(str(worker_concurrency))}"""
            
        elif is_main:
            # Variáveis específicas do Main
            env_vars += f""" \
            -e EXECUTIONS_MODE=queue \
            -e OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true"""
            # Exporta N8N_ENCRYPTION_KEY somente se não estiver vazia
            if encryption_key:
                env_vars += f""" \
            -e N8N_ENCRYPTION_KEY={shlex.quote(str(encryption_key))}"""
            
            if n8n_host:
                env_vars += f""" \
            -e N8N_HOST={shlex.quote(str(n8n_host))} \
            -e N8N_PROTOCOL=https \
            -e WEBHOOK_URL={shlex.quote(str(webhook_url))} \
            -e N8N_PROXY_HOPS=1 \
            -e N8N_SECURE_COOKIE=true"""
            
            # Porta exposta apenas no Main
            env_vars += f""" \
            -p {porta_publicar}:5678"""
        
        else:  # Worker
            # Worker apenas processa, não precisa de porta exposta
            env_vars += f""" \
            -e EXECUTIONS_MODE=queue \
            -e QUEUE_WORKER_ID={shlex.quote(str(container_name))} \
            -e N8N_WORKER_CONCURRENCY={shlex.quote(str(worker_concurrency))}"""
        
        # Injeta N8N_ENCRYPTION_KEY para Worker, se informada
        try:
            if is_worker and encryption_key:
                env_vars += f""" \
            -e N8N_ENCRYPTION_KEY={shlex.quote(str(encryption_key))}"""
        except Exception:
            pass

        # Comando completo
        # Persiste .env com as variáveis utilizadas para reutilização futura
        try:
            env_map = {}
            if is_simples:
                env_map.update({
                    'DB_SQLITE_POOL_SIZE': '3',
                    'N8N_RUNNERS_ENABLED': 'true',
                    'N8N_BLOCK_ENV_ACCESS_IN_NODE': 'false',
                    'N8N_GIT_NODE_DISABLE_BARE_REPOS': 'true',
                    'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS': 'true',
                    'N8N_WORKER_CONCURRENCY': str(worker_concurrency),
                })
            else:
                env_map.update({
                    'DB_TYPE': 'postgresdb',
                    'DB_POSTGRESDB_HOST': str(postgres_host),
                    'DB_POSTGRESDB_PORT': str(postgres_port),
                    'DB_POSTGRESDB_DATABASE': str(postgres_db),
                    'DB_POSTGRESDB_USER': str(postgres_user),
                    'DB_POSTGRESDB_PASSWORD': str(postgres_password),
                    'QUEUE_BULL_REDIS_HOST': str(redis_host),
                    'QUEUE_BULL_REDIS_PORT': str(redis_port),
                    'N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS': 'true',
                    'N8N_RUNNERS_ENABLED': 'true',
                    'N8N_BLOCK_ENV_ACCESS_IN_NODE': 'false',
                    'N8N_GIT_NODE_DISABLE_BARE_REPOS': 'true',
                })
                if redis_password:
                    env_map['QUEUE_BULL_REDIS_PASSWORD'] = str(redis_password)
                # Para workers, define concorrência
                if is_worker:
                    env_map['N8N_WORKER_CONCURRENCY'] = str(worker_concurrency)
                    if encryption_key:
                        env_map['N8N_ENCRYPTION_KEY'] = str(encryption_key)
            if is_main:
                env_map['EXECUTIONS_MODE'] = 'queue'
                env_map['OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS'] = 'true'
                if encryption_key:
                    env_map['N8N_ENCRYPTION_KEY'] = str(encryption_key)
            if n8n_host:
                env_map.update({
                    'N8N_HOST': str(n8n_host),
                    'N8N_PROTOCOL': 'https',
                    'WEBHOOK_URL': str(webhook_url),
                    'N8N_PROXY_HOPS': '1',
                    'N8N_SECURE_COOKIE': 'true',
                })
            # Salva arquivo env
            os.makedirs(caminho_n8n, exist_ok=True)
            with open(env_file_path, 'w', encoding='utf-8') as fenv:
                fenv.write('# n8n environment variables\n')
                for k, v in env_map.items():
                    if v is None:
                        continue
                    # Evita quebras de linha e espaços à direita
                    fenv.write(f"{k}={str(v).strip()}\n")
            try:
                os.chmod(env_file_path, 0o600)
            except Exception:
                pass
            print(f"\n✔ Arquivo de configuração salvo: {env_file_path}")
        except Exception as ex:
            print(f"Aviso: não foi possível salvar o env em {env_file_path}: {ex}")

        # Seleciona a imagem e entrypoint correto (web padrão ou worker)
        image_cmd = "docker.n8n.io/n8nio/n8n:latest"
        if is_worker:
            image_cmd += " worker"

        comando_completo = comando_base + env_vars + f" \\\n+            {image_cmd}\n            "
        
        # Saneia string do comando para evitar '+' deixado por engano e quebras formatadas
        comando_completo = comando_completo.replace("+            ", "")
        comandos = [comando_completo]
        
        # Remove container se existir
        self.remove_container(container_name)
        
        # Executa instalação
        self.executar_comandos(comandos)
        
        time.sleep(30)
        os.chmod(caminho_n8n, 0o777)
        
        # Mensagens finais
        print("\n" + "="*60)
        print(f"✔ Instalação do n8n ({tipo_suffix.upper()}) concluída!")
        print("="*60)
        
        if is_simples:
            print(f'\n✔ Instalação simples configurada!')
            print(f'\nAcesse o n8n em http://<seu_ip>:{porta_publicar}')
            if n8n_host:
                print(f'Ou via domínio: https://{n8n_host}')
            print('\nNa primeira execução você precisará criar um usuário e senha.')
            print('\n📝 Características desta instalação:')
            print('   - Banco de dados: SQLite (arquivo local)')
            print('   - Execuções: Modo local (sem fila/workers)')
            print('   - Dados salvos em: ' + caminho_n8n)
            print('\n⚠️ NOTA: Para produção com múltiplos workers, use a opção "Main"')
            
        elif is_main:
            print(f'\nAcesse o n8n em http://<seu_ip>:{porta_publicar}')
            if n8n_host:
                print(f'Ou via domínio: https://{n8n_host}')
            print('\nNa primeira execução você precisará criar um usuário e senha.')
            print(f'\n⚠️ IMPORTANTE - Guarde estas informações:')
            print(f'   - Chave de encriptação: {encryption_key}')
            print(f'   - Senha PostgreSQL: [oculta]')
        else:
            print('\n✔ Worker configurado e em execução.')
            print('Este worker processará tarefas da fila automaticamente.')
        
        # Note about secure cookies when behind HTTPS
        try:
            if n8n_host:
                print("\nAviso: N8N_SECURE_COOKIE=true habilitado (requer HTTPS).")
                print("Para testar via HTTP, pare o container e defina N8N_SECURE_COOKIE=false, depois reinicie.")
        except Exception:
            pass

        print("\n" + "="*60)
