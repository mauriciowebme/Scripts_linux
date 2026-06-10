import os
import shutil
import subprocess
import time

import mysql.connector

from install_master.core.docker_base import DockerBase


class MixinMySQL(DockerBase):

    def instala_mysql_5_7(self):
        self.instala_mysql('5.7')

    def instala_mysql_8_0(self):
        self.instala_mysql('8.0')

    def instala_mysql(self, selecao=None):

        if not selecao:
            selecao = input('Selecione a versão: \n1 - 5.7 \n2 - 8.0\n')
        if selecao == "1" or selecao == "5.7":
            versao = '5.7'
            porta = '3316'
        elif selecao == "2" or selecao == "8.0":
            versao = '8.0'
            porta = '3317'
        else:
            print("Seleção incorreta.")
            return

        versao_ = versao.replace('.', '_')
        novo_db = True
        pasta_bd = f'{self.bds}/mysql/{versao_}'

        if os.path.exists(pasta_bd):
            print('Tem uma pasta de instalação de banco de dados existente.')
            resposta = input('Deseja remover a pasta de banco de dados existente? s|n: ')

            if resposta.lower() == 's':
                shutil.rmtree(pasta_bd)
                os.makedirs(pasta_bd, exist_ok=True)
                os.chmod(pasta_bd, 0o777)
                if not self.mysql_root_password:
                    self.mysql_root_password = input("Digite a senha root para o MySQL: ")

            else:
                novo_db = False
                self.mysql_root_password = ''
        else:
            if not self.mysql_root_password:
                self.mysql_root_password = input("Digite a senha root para o MySQL: ")

        print('Instalando o mysql.\n')

        container_db = f"""docker run -d \
                        --name mysql_{versao_} \
                        --restart=unless-stopped \
                        --memory=1g \
                        --cpus=1 \
                        -p {porta}:3306 \
                        -e MYSQL_DATABASE=db_testes \
                        -e MYSQL_USER=testes \
                        -e MYSQL_PASSWORD=testes \
                        -e MYSQL_ROOT_PASSWORD='{self.mysql_root_password}' \
                        -v {self.bds}/mysql/{versao_}:/var/lib/mysql \
                        mysql:{versao} \
                        --server-id=1 \
                        --log-bin=mysql-bin \
                        --binlog-format=row \
                        --default-authentication-plugin=mysql_native_password
                    """
        comandos = [
            container_db,
        ]
        self.remove_container(f'mysql_{versao_}')
        self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'mysql_{versao_}', numero_rede=1)

        if not novo_db:
            self.mysql_root_password = None

        time.sleep(10)
        print(f'Instalação do Mysql completa.')
        print(f'Acesso:')
        print(f' - ssh -L {porta}:localhost:{porta} usuario@servidor_remoto')
        print(f' - Local instalação: {self.bds}/mysql/{versao_}')
        print(f' - Usuario: root')
        if self.mysql_root_password:
            print(f' - Senha: {self.mysql_root_password}')
        else:
            print(f' - Senha: já definida anteriormente.')
        print(f' - Porta interna: 3306')
        print(f' - Porta externa: {porta}')

    def configure_mysql_replication(self, master_container, master_host, master_user, master_password, master_porta,
                                    slave_container, slave_host, slave_user, slave_password, slave_porta,
                                    replication_user, replication_password):
        try:
            print("Conectando ao Master...")
            erro_conect = False
            for x in range(10):
                try:
                    master_conn = mysql.connector.connect(
                        host=master_host,
                        user=master_user,
                        password=master_password,
                        port=master_porta
                    )
                    master_cursor = master_conn.cursor()
                    print("Conexão com o Master estabelecida.")
                    erro_conect = False
                    break
                except Exception:
                    time.sleep(10)
                    erro_conect = True

            if erro_conect:
                print('Erro ao conectar ao Master.')
                return

            print("Conectando ao Slave...")
            erro_conect = False
            for x in range(10):
                try:
                    slave_conn = mysql.connector.connect(
                        host=slave_host,
                        user=slave_user,
                        password=slave_password,
                        port=slave_porta
                    )
                    slave_cursor = slave_conn.cursor()
                    print("Conexão com o Slave estabelecida.")
                    erro_conect = False
                    break
                except Exception:
                    time.sleep(10)
                    erro_conect = True

            if erro_conect:
                print('Erro ao conectar ao Slave.')
                return

            master_cursor.execute(f"CREATE USER IF NOT EXISTS '{replication_user}'@'172.%' IDENTIFIED BY '{replication_password}';")
            master_cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{replication_user}'@'172.%';")
            master_cursor.execute("FLUSH PRIVILEGES;")
            print("Usuário de replicação criado com sucesso no Master.")

            slave_cursor.execute(f"CREATE USER IF NOT EXISTS '{replication_user}'@'172.%' IDENTIFIED BY '{replication_password}';")
            slave_cursor.execute(f"GRANT REPLICATION SLAVE ON *.* TO '{replication_user}'@'172.%';")
            slave_cursor.execute("FLUSH PRIVILEGES;")
            print("Usuário de replicação criado com sucesso no Slave.")

            master_cursor.execute("SHOW MASTER STATUS;")
            result = master_cursor.fetchone()
            if result:
                master_log_file = result[0]
                master_log_pos = result[1]
                print(f"Master Log File: {master_log_file}, Position: {master_log_pos}")
            else:
                print("Erro: Não foi possível obter o status do log binário do Master.")
                return

            slave_cursor.execute("SHOW MASTER STATUS;")
            result = slave_cursor.fetchone()
            if result:
                slave_log_file = result[0]
                slave_log_pos = result[1]
                print(f"Slave Log File: {slave_log_file}, Position: {slave_log_pos}")
            else:
                print("Erro: Não foi possível obter o status do log binário do Slave.")
                return

            master_cursor.execute("STOP SLAVE;")
            porta_interna = '3306'
            master_cursor.execute(f"""
                CHANGE MASTER TO
                MASTER_HOST='{slave_container}',
                MASTER_PORT={porta_interna},
                MASTER_USER='{replication_user}',
                MASTER_PASSWORD='{replication_password}',
                MASTER_LOG_FILE='{slave_log_file}',
                MASTER_LOG_POS={slave_log_pos};
            """)
            master_cursor.execute("START SLAVE;")
            print("Replicação configurada com sucesso no Slave.")

            slave_cursor.execute("STOP SLAVE;")
            porta_interna = '3306'
            slave_cursor.execute(f"""
                CHANGE MASTER TO
                MASTER_HOST='{master_container}',
                MASTER_PORT={porta_interna},
                MASTER_USER='{replication_user}',
                MASTER_PASSWORD='{replication_password}',
                MASTER_LOG_FILE='{master_log_file}',
                MASTER_LOG_POS={master_log_pos};
            """)
            slave_cursor.execute("START SLAVE;")
            print("Replicação configurada com sucesso no Slave.")

            master_cursor.execute("SELECT VERSION();")
            master_version = master_cursor.fetchone()[0]
            print(f"Versão do Master: {master_version}")

            slave_cursor.execute("SELECT VERSION();")
            slave_version = slave_cursor.fetchone()[0]
            print(f"Versão do Slave: {slave_version}")

            if master_version.startswith("5.7"):
                print("Verificando status da replicação para MASTER MySQL 5.7...")
                master_cursor.execute("SHOW SLAVE STATUS;")
            else:
                print("Verificando status da replicação para MASTER MySQL 8.0...")
                master_cursor.execute("SHOW REPLICA STATUS;")
            for row in master_cursor:
                print(row)

            if slave_version.startswith("5.7"):
                print("Verificando status da replicação para SLAVE MySQL 5.7...")
                slave_cursor.execute("SHOW SLAVE STATUS;")
            else:
                print("Verificando status da replicação para SLAVE MySQL 8.0...")
                slave_cursor.execute("SHOW REPLICA STATUS;")
            for row in slave_cursor:
                print(row)

        except Exception as ex:
            print(f"Erro: {ex}")

        finally:
            if 'master_conn' in locals() and master_conn.is_connected():
                master_cursor.close()
                master_conn.close()
                print("Conexão com o Master fechada.")
            if 'slave_conn' in locals() and slave_conn.is_connected():
                slave_cursor.close()
                slave_conn.close()
                print("Conexão com o Slave fechada.")
