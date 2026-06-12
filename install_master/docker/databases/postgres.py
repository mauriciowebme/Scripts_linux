import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinPostgres(DockerBase):

    def instala_postgres(self, selecao=None):
        if not selecao:
            selecao = input('Selecione a versão: \n1 - 15 \n2 - 16 \n3 - 17\n')
        if selecao == "1" or selecao == "15":
            versao = '15'
            porta = '5433'
        elif selecao == "2" or selecao == "16":
            versao = '16'
            porta = '5434'
        elif selecao == "3" or selecao == "17":
            versao = '17'
            porta = '5435'
        else:
            print("Seleção incorreta.")
            return

        if not self.postgres_password:
            self.postgres_password = input("Digite a senha do usuário postgres: ")

        versao_ = versao.replace('.', '_')

        print('Instalando o Postgres.\n')

        container_db = f"""docker run -d \
            --name postgres_{versao_} \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -p {porta}:5432 \
            -e POSTGRES_PASSWORD={self.postgres_password} \
            -v {self.bds}/postgres/{versao_}:/var/lib/postgresql/data \
            postgres:{versao}"""

        comandos = [container_db]
        self.remove_container(f'postgres_{versao_}')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'postgres_{versao_}', numero_rede=1)

        time.sleep(30)

        print(f'Instalação do Postgres completa.\n')
        print(f'Acesso:')
        print(f' - ssh -L {porta}:localhost:{porta} usuario@servidor_remoto')
        print(f' - Local instalação: {self.bds}/postgres/{versao_}')
        print(f' - Usuario: postgres')
        print(f' - Porta interna: 5432')
        print(f' - Porta externa: {porta}')

    def gerenciar_bancos_postgres(self):
        print("\n=== GERENCIAMENTO DE BANCOS DE DADOS POSTGRESQL ===\n")

        print("Verificando containers PostgreSQL disponíveis...")
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=postgres_", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )

        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]

        if not containers:
            print("❌ Nenhum container PostgreSQL em execução encontrado.")
            print("Instale o PostgreSQL primeiro usando a opção '** BD ** Instala postgres'")
            return

        print("\nContainers PostgreSQL disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")

        escolha = input("\nEscolha o container (número): ").strip()
        try:
            container_idx = int(escolha) - 1
            if container_idx < 0 or container_idx >= len(containers):
                print("❌ Opção inválida.")
                return
            container = containers[container_idx]
        except ValueError:
            print("❌ Entrada inválida.")
            return

        print(f"\n=== OPERAÇÕES NO CONTAINER: {container} ===")
        print("📋 GERENCIAMENTO POSTGRESQL")
        print("-" * 50)
        print("[1] 🗄️ Criar banco de dados")
        print("[2] 📋 Listar bancos de dados")
        print("[3] 🗑️ Apagar banco de dados")
        print("[0] ↩️ Voltar")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == "1":
            self.criar_banco_postgres(container)
        elif opcao == "2":
            self.listar_bancos_postgres(container)
        elif opcao == "3":
            self.apagar_banco_postgres(container)
        elif opcao == "0":
            return
        else:
            print("❌ Opção inválida.")

    def criar_banco_postgres(self, container):
        print("\n=== CRIAR BANCO DE DADOS POSTGRESQL ===\n")

        max_tentativas = 3

        for tentativa in range(1, max_tentativas + 1):
            nome_banco = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome do banco de dados: ").strip()
            if nome_banco:
                break
            print(f"❌ Nome do banco não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return

        for tentativa in range(1, max_tentativas + 1):
            usuario = input(f"[Tentativa {tentativa}/{max_tentativas}] Nome do usuário (deixe vazio para usar '{nome_banco}'): ").strip()
            if not usuario:
                usuario = nome_banco
                print(f"ℹ️  Usando '{usuario}' como nome de usuário.")
                break
            elif len(usuario) >= 3:
                break
            print(f"❌ Usuário deve ter pelo menos 3 caracteres. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return

        for tentativa in range(1, max_tentativas + 1):
            senha = input(f"[Tentativa {tentativa}/{max_tentativas}] Senha para o usuário '{usuario}' (mínimo 4 caracteres): ").strip()
            if len(senha) >= 4:
                break
            print(f"❌ Senha deve ter pelo menos 4 caracteres. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                return

        print("\n" + "=" * 60)
        print("📋 RESUMO DA OPERAÇÃO:")
        print(f"   Banco de dados: {nome_banco}")
        print(f"   Usuário: {usuario}")
        print(f"   Senha: {'*' * len(senha)}")
        print(f"   Container: {container}")
        print("=" * 60)

        confirmar = input("\n✅ Confirma a criação com esses dados? (s/n): ").strip().lower()
        if confirmar != 's':
            print("❌ Operação cancelada pelo usuário.")
            return

        print(f"\n📝 Criando banco de dados '{nome_banco}' com usuário '{usuario}'...")

        try:
            cmd_usuario = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"CREATE USER \"{usuario}\" WITH PASSWORD '{senha}';"
            ]
            resultado = subprocess.run(cmd_usuario, capture_output=True, text=True)

            if resultado.returncode != 0 and "already exists" not in resultado.stderr:
                print(f"❌ Erro ao criar usuário: {resultado.stderr}")
                return
            elif "already exists" in resultado.stderr:
                print(f"⚠️  Usuário '{usuario}' já existe, usando existente.")
            else:
                print(f"✅ Usuário '{usuario}' criado com sucesso.")

            cmd_banco = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"CREATE DATABASE \"{nome_banco}\" OWNER \"{usuario}\";"
            ]
            resultado = subprocess.run(cmd_banco, capture_output=True, text=True)

            if resultado.returncode != 0:
                if "already exists" in resultado.stderr:
                    print(f"⚠️  Banco '{nome_banco}' já existe.")
                else:
                    print(f"❌ Erro ao criar banco: {resultado.stderr}")
                    return
            else:
                print(f"✅ Banco de dados '{nome_banco}' criado com sucesso.")

            cmd_grant = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"GRANT ALL PRIVILEGES ON DATABASE \"{nome_banco}\" TO \"{usuario}\";"
            ]
            subprocess.run(cmd_grant, capture_output=True, text=True)
            print(f"✅ Privilégios concedidos ao usuário '{usuario}'.")

            print("\n" + "=" * 60)
            print("📌 INFORMAÇÕES DE CONEXÃO:")
            print(f"   Host: localhost (ou IP do servidor)")
            print(f"   Banco: {nome_banco}")
            print(f"   Usuário: {usuario}")
            print(f"   Senha: {senha}")
            print(f"   Container: {container}")
            print("=" * 60)

        except Exception as e:
            print(f"❌ Erro ao criar banco de dados: {e}")

    def listar_bancos_postgres(self, container):
        print(f"\n=== BANCOS DE DADOS NO CONTAINER: {container} ===\n")
        try:
            cmd = [
                "docker", "exec", container, "psql", "-U", "postgres", "-A", "-F|", "-c",
                "SELECT datname, pg_catalog.pg_get_userbyid(datdba) as owner FROM pg_database ORDER BY datname;"
            ]
            resultado = subprocess.run(cmd, capture_output=True, text=True)
            if resultado.returncode != 0:
                print(f"❌ Erro ao listar bancos: {resultado.stderr}")
                return
            linhas = resultado.stdout.strip().split('\n')
            bancos_padrao = ['postgres', 'template0', 'template1']
            bancos_usuario = []
            bancos_sistema = []

            for linha in linhas:
                if not linha or linha.startswith('datname|') or linha.startswith('(') or linha.startswith('-'):
                    continue

                partes = linha.split('|')
                if len(partes) < 2:
                    continue

                nome = partes[0].strip()
                owner = partes[1].strip()

                if not nome:
                    continue

                if nome in bancos_padrao:
                    bancos_sistema.append((nome, owner))
                else:
                    bancos_usuario.append((nome, owner))

            print("--- Bancos do sistema (padrão) ---")
            for nome, owner in bancos_sistema:
                print(f"  {nome:<15} (owner: {owner})")
            print("\n--- Bancos criados pelo usuário ---")
            if bancos_usuario:
                for nome, owner in bancos_usuario:
                    print(f"  {nome:<15} (owner: {owner})")
            else:
                print("  Nenhum banco de usuário encontrado.")
        except Exception as e:
            print(f"❌ Erro ao listar bancos de dados: {e}")

    def apagar_banco_postgres(self, container):
        print(f"\n=== APAGAR BANCO DE DADOS NO CONTAINER: {container} ===\n")

        self.listar_bancos_postgres(container)

        max_tentativas = 3

        for tentativa in range(1, max_tentativas + 1):
            nome_banco = input(f"\n[Tentativa {tentativa}/{max_tentativas}] Nome do banco de dados a ser APAGADO: ").strip()

            if not nome_banco:
                print(f"❌ Nome do banco não pode ser vazio. Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                    return
                continue

            bancos_sistema = ['postgres', 'template0', 'template1']
            if nome_banco in bancos_sistema:
                print(f"❌ Não é permitido apagar bancos do sistema: {', '.join(bancos_sistema)}")
                print(f"   Tentativas restantes: {max_tentativas - tentativa}")
                if tentativa == max_tentativas:
                    print("❌ Número máximo de tentativas atingido. Operação cancelada.")
                    return
                continue

            break

        for tentativa in range(1, max_tentativas + 1):
            print(f"\n⚠️  ATENÇÃO: Você está prestes a APAGAR o banco '{nome_banco}'!")
            print("⚠️  Esta ação é IRREVERSÍVEL e todos os dados serão perdidos!")
            confirmacao = input(f"[Tentativa {tentativa}/{max_tentativas}] Digite 'CONFIRMAR' para prosseguir: ").strip()

            if confirmacao == "CONFIRMAR":
                break

            print(f"❌ Confirmação incorreta. Digite exatamente 'CONFIRMAR'.")
            print(f"   Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("❌ Número máximo de tentativas atingido. Operação cancelada por segurança.")
                return

        for tentativa in range(1, max_tentativas + 1):
            apagar_usuario = input(f"[Tentativa {tentativa}/{max_tentativas}] Apagar também o usuário de mesmo nome? (s/n): ").strip().lower()

            if apagar_usuario in ['s', 'n']:
                break

            print(f"❌ Responda apenas 's' ou 'n'. Tentativas restantes: {max_tentativas - tentativa}")
            if tentativa == max_tentativas:
                print("⚠️  Assumindo 'n' (não apagar usuário).")
                apagar_usuario = 'n'

        try:
            print(f"\n📝 Desconectando sessões ativas do banco '{nome_banco}'...")
            cmd_disconnect = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{nome_banco}';"
            ]
            subprocess.run(cmd_disconnect, capture_output=True, text=True)

            print(f"📝 Apagando banco de dados '{nome_banco}'...")
            cmd_drop = [
                "docker", "exec", container, "psql", "-U", "postgres", "-c",
                f"DROP DATABASE \"{nome_banco}\";"
            ]
            resultado = subprocess.run(cmd_drop, capture_output=True, text=True)

            if resultado.returncode == 0:
                print(f"✅ Banco de dados '{nome_banco}' apagado com sucesso.")
            else:
                print(f"❌ Erro ao apagar banco: {resultado.stderr}")
                return

            if apagar_usuario == 's':
                print(f"📝 Apagando usuário '{nome_banco}'...")
                cmd_drop_user = [
                    "docker", "exec", container, "psql", "-U", "postgres", "-c",
                    f"DROP USER IF EXISTS \"{nome_banco}\";"
                ]
                resultado = subprocess.run(cmd_drop_user, capture_output=True, text=True)

                if resultado.returncode == 0:
                    print(f"✅ Usuário '{nome_banco}' apagado com sucesso.")
                else:
                    print(f"⚠️  Aviso ao apagar usuário: {resultado.stderr}")

        except Exception as e:
            print(f"❌ Erro ao apagar banco de dados: {e}")

    def limpar_banco_postgres(self, host, port, db_name, db_owner, db_password):
        print("Iniciando container temporário do Postgres para limpar via schema (psql)...")
        base_cmd = ["docker", "run", "--rm"]
        if str(host) in ("localhost", "127.0.0.1"):
            base_cmd += ["--network=host"]
        base_cmd += [
            "-e", f"PGPASSWORD={db_password}",
            "postgres:17",
            "psql",
            "-h", str(host),
            "-p", str(port),
            "-U", str(db_owner),
            "-d", str(db_name),
            "-v", "ON_ERROR_STOP=1",
        ]

        schema_cmds = [
            "DROP SCHEMA IF EXISTS public CASCADE;",
            f"CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION \"{db_owner}\";",
            f"GRANT ALL ON SCHEMA public TO \"{db_owner}\";",
            "GRANT ALL ON SCHEMA public TO public;",
        ]
        for sql in schema_cmds:
            cmd = base_cmd + ["-c", sql]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"Falha ao executar psql via container temporário: {r.stderr}")
        print("Schema public limpo e recriado (via container temporário).")

    def configure_postgres_replication(self, master_container, slave_container, replication_user, replication_password):
        try:
            print("Configurando replicação...")

            print("Configurando o Master...")
            master_commands = [
                f"docker exec {master_container} bash -c \"echo 'wal_level = replica' >> /var/lib/postgresql/data/postgresql.conf\"",
                f"docker exec {master_container} bash -c \"echo 'max_wal_senders = 5' >> /var/lib/postgresql/data/postgresql.conf\"",
                f"docker exec {master_container} bash -c \"echo 'host replication {replication_user} 0.0.0.0/0 md5' >> /var/lib/postgresql/data/pg_hba.conf\"",
                f"docker exec {master_container} bash -c \"psql -U postgres -c \\\"CREATE ROLE {replication_user} REPLICATION LOGIN ENCRYPTED PASSWORD '{replication_password}';\\\"\"",
            ]

            self.executar_comandos(master_commands)
            self.executar_comandos([f"docker restart {master_container}"])
            print("Master configurado com sucesso.")

            print("Preparando o Slave...")
            self.executar_comandos([f"docker stop {slave_container}"])
            self.executar_comandos([
                f"docker exec {master_container} bash -c \"rm -rf /mnt/_slave/*\"",
                f"docker exec {master_container} bash -c \"pg_basebackup -h localhost -D /mnt/_slave -U {replication_user} -Fp -Xs -P -R\""
            ])
            self.executar_comandos([f"docker start {slave_container}"])
            time.sleep(10)
            self.executar_comandos([
                f"docker exec {slave_container} bash -c \"echo \\\"primary_conninfo = 'host={master_container} port=5432 user={replication_user} password={replication_password}'\\\" >> /var/lib/postgresql/data/postgresql.auto.conf\""
            ])
            self.executar_comandos([f"docker restart {slave_container}"])
            print("Slave preparado com sucesso.")

        except Exception as ex:
            print(f"Erro na configuração da replicação: {ex}")
