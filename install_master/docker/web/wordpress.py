import subprocess

from install_master.core.docker_base import DockerBase


class MixinWordPress(DockerBase):

    def instala_wordpress_puro(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        
        self.verifica_container_existe('mysql_5_7', self.instala_mysql_5_7)
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        dominio_ = dominio.replace('.', '_')
        comando1 = f"docker exec -i mysql_5_7 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE USER IF NOT EXISTS 'wordpress'@'%' IDENTIFIED BY 'wordpress';\""
        comando2 = f"docker exec -i mysql_5_7 mysql -uroot -p'{self.mysql_root_password}' -e \"CREATE DATABASE IF NOT EXISTS {dominio_}; GRANT ALL PRIVILEGES ON {dominio_}.* TO 'wordpress'@'%'; FLUSH PRIVILEGES;\""
        self.executar_comandos([comando1, comando2])
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -e WORDPRESS_DB_HOST=mysql_5_7:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME={dominio_} \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
        
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'{dominio_}')
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(dominio, endereco=f'{dominio_}', porta='80')
            self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=0)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=1)
        
    def instala_wordpress(self,):
        print('Instalando o wordpress.\n')
        dominio = input('Digite o dominio:')
        
        # Verifica se o objeto 'self' possui o atributo 'root_password' e se ele está definido (não vazio).
        if not hasattr(self, 'root_password') or not self.mysql_root_password:
            self.mysql_root_password = input("Digite a senha root para o MySQL: ")
        
        dominio_ = dominio.replace('.', '_')
        container_db = f"""docker run -d \
                        --name {dominio_}_bd \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -e MYSQL_DATABASE=wordpress \
                        -e MYSQL_USER=wordpress \
                        -e MYSQL_PASSWORD=wordpress \
                        -e MYSQL_RANDOM_ROOT_PASSWORD={self.mysql_root_password} \
                        -v {self.install_principal}/wordpress/{dominio_}/mysql:/var/lib/mysql \
                        mysql:5.7
                    """
        container = f"""docker run -d \
                        --name {dominio_} \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -e WORDPRESS_DB_HOST={dominio_}_bd:3306 \
                        -e WORDPRESS_DB_USER=wordpress \
                        -e WORDPRESS_DB_PASSWORD=wordpress \
                        -e WORDPRESS_DB_NAME=wordpress \
                        -v {self.install_principal}/wordpress/{dominio_}:/var/www/html \
                        wordpress:latest
                    """
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        # if resposta.lower() == 's':
        #     container = self.adiciona_redirecionamento_traefik(container, dominio, porta='80')
        
        self.remove_container(f'{dominio_}_bd')
        self.remove_container(f'{dominio_}')
        comandos = [
            container_db,
            container,
            ]
        resultados = self.executar_comandos(comandos)
        if resposta.lower() == 's':
            self.adiciona_roteador_servico_traefik(dominio, endereco=f'{dominio_}', porta='80')
            self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=0)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}_bd', numero_rede=1)
        self.cria_rede_docker(associar_container_nome=f'{dominio_}', numero_rede=1)
