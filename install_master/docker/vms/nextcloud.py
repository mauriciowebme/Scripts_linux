import os
import subprocess
import textwrap
import time

from install_master.core.docker_base import DockerBase


class MixinNextcloud(DockerBase):

    def instala_nextcloud(self,):
        print('Instalando nextcloud...')
        local = input('Digite o local para armazenamento dos dados: Ex /install_principal/nextcloud: ')
        
        self.verifica_container_existe('mysql_8_0', self.instala_mysql_8_0)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        comando1 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'nextcloud'@'%' IDENTIFIED BY 'nextcloud';\""
        comando2 = f"docker exec -i mysql_8_0 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS nextcloud_bd; GRANT ALL PRIVILEGES ON nextcloud_bd.* TO 'nextcloud'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        
        comandos = [
            f"""docker run -d \
                    --name nextcloud \
                    --restart=unless-stopped \
                    --memory=1g \
                    --cpus=1 \
                    -p 8585:80 \
                    -e MYSQL_DATABASE=nextcloud_bd \
                    -e MYSQL_PASSWORD=nextcloud \
                    -e MYSQL_USER=nextcloud \
                    -e MYSQL_HOST=mysql_8_0:3306 \
                    -v {local}:/var/www/html \
                    nextcloud
                """,
            ]
        self.remove_container('nextcloud')
        resultados = self.executar_comandos(comandos)
        time.sleep(30)
        
        service_name = "cron.php"
        
        # Conteúdo do arquivo de serviço
        service_content = f"""[Unit]
Description=Nextcloud Cron Job
ConditionPathExists=!/tmp/{service_name}.lock

[Service]
ExecStartPre=/bin/touch /tmp/{service_name}.lock
ExecStart=/usr/bin/docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php
ExecStartPost=/bin/rm -f /tmp/{service_name}.lock
TimeoutStartSec=900
User=root
    """
        timer_content = f"""[Unit]
Description=Run {service_name}.service every 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
    """

        # Caminho do arquivo de serviço
        service_path = f"/etc/systemd/system/{service_name}.service"
        timer_path = f"/etc/systemd/system/{service_name}.timer"

        try:
            # Escreve o arquivo de serviço
            with open(service_path, "w") as f:
                f.write(service_content)
            print(f"Serviço {service_name}.service criado com sucesso em {service_path}")
            
            with open(timer_path, "w") as f:
                f.write(timer_content)
            print(f"Serviço {service_name}.service criado com sucesso em {timer_path}")

            # Recarrega o systemd para reconhecer o novo serviço
            os.system("sudo systemctl daemon-reload")

            # Ativa o serviço
            os.system(f"sudo systemctl enable {service_name}.timer")
            os.system(f"sudo systemctl start {service_name}.timer")
            os.system(f"sudo systemctl status {service_name}.timer")
            print(f"Timer {service_name}.timer ativado e iniciado com sucesso.")

        except PermissionError:
            print("Erro: Permissão negada. Execute o script como superusuário (sudo).")
        except Exception as e:
            print(f"Erro ao criar o serviço: {e}")
        
        # comandos = [
        #     f"echo '*/15 * * * * docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php' | sudo crontab -",
        #     ]
        # self.executar_comandos(comandos)
        
        self.cria_rede_docker(associar_container_nome=f'nextcloud', numero_rede=1)
        print("Instalação concluída. Nextcloud está pronto para uso.")
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos, exibir_executando=False)
        print("porta de acesso: 8585")
        print("Processos para automatizar:")
        print("A cada 5 mimutos:")
        print("docker exec -i -u www-data nextcloud /usr/local/bin/php /var/www/html/cron.php")
        print("Rodar fora de horario de pico uma vez ao dia:")
        print("docker exec -u www-data nextcloud php occ maintenance:repair --include-expensive")
