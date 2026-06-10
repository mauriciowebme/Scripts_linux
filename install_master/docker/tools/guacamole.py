import time
import subprocess

from install_master.core.docker_base import DockerBase


class MixinGuacamole(DockerBase):
    def instala_webserver_guacamole(self,):
        self.verifica_container_existe('mysql_8_0', self.instala_mysql_8_0)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para acessar o MySQL e criar o banco: ")
            
        # Verifica se a senha está correta antes de prosseguir
        max_attempts = 3
        for attempt in range(max_attempts):
            test_cmd = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e 'SELECT 1;'"
            result = self.executar_comandos([test_cmd], exibir_resultados=False)
            
            # Verifica se o comando foi executado com sucesso (sem erro)
            if test_cmd in result and 'Erro:True' not in str(result[test_cmd]):
                print("Senha MySQL verificada com sucesso.")
                break
            else:
                if attempt < max_attempts - 1:
                    print(f"Senha incorreta. Tentativa {attempt + 1}/{max_attempts}")
                    self.mysql_root_password = input("Digite a senha root para o MySQL novamente: ")
                else:
                    print("Número máximo de tentativas excedido. Saindo...")
                    return
        
        # Verifica se a base de dados guacamole_db já existe
        comando_verifica_db = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"SHOW DATABASES LIKE 'guacamole_db';\""
        resultado = self.executar_comandos([comando_verifica_db])
        
        if not any('guacamole_db' in line for line in resultado[comando_verifica_db]):
            comando1 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'guacamole_user'@'%' IDENTIFIED BY 'guacamole_password';\""
            comando2 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS guacamole_db; GRANT ALL PRIVILEGES ON guacamole_db.* TO 'guacamole_user'@'%'; FLUSH PRIVILEGES;\""
            comando3 = f"docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --mysql > initdb.sql"
            comando4 = f"docker cp initdb.sql mysql_8_0:/initdb.sql"
            comando5 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' guacamole_db -e \"SOURCE /initdb.sql;\""
            self.executar_comandos([comando1, comando2, comando3, comando4, comando5])
        else:
            print("A base de dados guacamole_db já existe.")
        
        # caminho_guacamole = f"{self.install_principal}/guacamole"
        # self.gerenciar_permissoes_pasta(caminho_guacamole, '777')
        # -v {caminho_guacamole}/guacamole:/etc/guacamole \
        container_guacamole = f"""docker run -d \
            --name guacamole \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            -p 8086:8080 \
            -e GUACD_HOSTNAME=guacamole_guacd \
            -e MYSQL_HOSTNAME=mysql_8_0 \
            -e MYSQL_DATABASE=guacamole_db \
            -e MYSQL_USER=guacamole_user \
            -e MYSQL_PASSWORD=guacamole_password \
            guacamole/guacamole:latest
        """
        # Container do Guacd
        container_guacd = """docker run -d \
            --name guacamole_guacd \
            --restart=unless-stopped \
            --memory=256m \
            --cpus=1 \
            guacamole/guacd:latest
        """
        
        comandos = [
            "docker pull guacamole/guacamole:latest",
            "docker pull guacamole/guacd:latest",
            container_guacamole,
            container_guacd,
            ]
        self.remove_container('guacamole')
        self.remove_container('guacamole_guacd')
        resultados = self.executar_comandos(comandos)
        
        self.cria_rede_docker(associar_container_nome='guacamole', numero_rede=1)
        self.cria_rede_docker(associar_container_nome='guacamole_guacd', numero_rede=1)
        
        # Configurar fontes e locale nos containers para renderização correta no Guacamole
        print("\n🔧 Configurando fontes e locale nos containers...")
        comandos_config = [
            f"docker exec -i -u root guacamole bash -c 'apt update && apt install -y fonts-dejavu-core fonts-liberation fontconfig locales && locale-gen en_US.UTF-8 && locale-gen pt_BR.UTF-8 && update-locale LANG=en_US.UTF-8 && fc-cache -fv'",
            f"docker exec -i -u root guacamole_guacd bash -c 'apt update && apt install -y fonts-dejavu-core fonts-liberation fontconfig locales && locale-gen en_US.UTF-8 && locale-gen pt_BR.UTF-8 && update-locale LANG=en_US.UTF-8 && fc-cache -fv'",
        ]
        self.executar_comandos(comandos_config, ignorar_erros=True, exibir_executando=False)
        
        # Reiniciar containers para aplicar configurações
        print("🔄 Reiniciando containers para aplicar configurações...")
        comandos_restart = [
            "docker restart guacamole",
            "docker restart guacamole_guacd",
        ]
        self.executar_comandos(comandos_restart, exibir_executando=False)
        
        print("✅ Configuração de fontes concluída!\n")
        
        print('Instalação do guacamole completa.\n')
        print('Acesse: http://<seu_ip>:8086/guacamole')
        print('Usuario: guacadmin')
        print('Senha: guacadmin')
