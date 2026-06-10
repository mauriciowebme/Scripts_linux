import os
import time
import subprocess

from install_master.core.docker_base import DockerBase


class MixinSFTP(DockerBase):
    def instala_ftp_sftpgo(self,):
        print('Instalando o ftp_sftpgo.\n')
        
        dir_dados = f"{self.install_principal}/ftp_sftpgo/dados"
        os.makedirs(dir_dados, exist_ok=True)
        os.chmod(dir_dados, 0o777)
        
        container = f"""docker run -d \
                        --name ftp_sftpgo \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -p 2025:2022 \
                        -p 8085:8080 \
                        -e SFTPGO_COMMON__IDLE_TIMEOUT=1 \
                        -e SFTPGO_COMMON__MAX_TOTAL_CONNECTIONS=200 \
                        -e SFTPGO_FILESYSTEM_UID=0 \
                        -e SFTPGO_FILESYSTEM_GID=0 \
                        -v {self.install_principal}:/install_principal \
                        -v {dir_dados}:/var/lib/sftpgo \
                        drakkan/sftpgo
                    """
        comandos = [
            container,
            ]
        self.remove_container(f'ftp_sftpgo')
        resultados = self.executar_comandos(comandos)
        print("sftpgo instalado com sucesso.")
        print("Instalação concluída. FTP SFTPGo está pronto para uso.")
        print("porta de acesso: 8085")
        print("Usuario e senha padrão: Vc cria no primeiro acesso. ")
        print("Crie o usuario admin e uma senha forte.")
        
    def gerenciar_usuarios_sftp(self, manual=True, simples_usuario=None, simples_senha=None, simples_base_diretorio=None):
        """
        Documentação:
        
        https://sftpgo.stoplight.io/docs/sftpgo/vjevihcqw0gy4-get-a-new-admin-access-token
        """
        
        self.verifica_container_existe('ftp_sftpgo', self.instala_ftp_sftpgo)
        
        max_attempts = 5
        admin_usuario = 'admin'
        admin_senha = 'admin'
        import requests
        from requests.auth import HTTPBasicAuth
        for attempt in range(max_attempts):
            if attempt > 0:
                print('\nUsuario e senha para permissão de administração FTP:')
                admin_usuario = input('Usuario admin: ')
                admin_senha = input('Senha: ')
            
            url = "http://localhost:8085/api/v2/token"
            response = requests.get(url, auth=HTTPBasicAuth(admin_usuario, admin_senha))
            if response.status_code == 200:
                print("Logado com sucesso\n")
                token = response.json()['access_token']
                break
            else:
                print(f"Usuario sem permissão ou não existe. Tentativas restantes: {max_attempts - attempt - 1}")
            if attempt == max_attempts - 1:
                print("Número máximo de tentativas atingido. Saindo...")
                exit()
            
        if manual:
            print('Digite os dados para criação do novo usuario FTP:')
            simples_usuario = input('Digite o nome de usuario: ')
            simples_senha = input('Digite uma senha: ')
            simples_base_diretorio = input('Digite um diretorio dentro de /install_principal começando com /. (Ex: /teste): ')
            print('\n')

        if '/' != simples_base_diretorio.split()[0]:
            simples_base_diretorio = '/'+simples_base_diretorio
        simples_base_diretorio = simples_base_diretorio.replace('//', '/')
        if '/install_principal' not in simples_base_diretorio:
            simples_base_diretorio = '/install_principal'+simples_base_diretorio
        
        os.makedirs(simples_base_diretorio, exist_ok=True)
        os.chmod(simples_base_diretorio, 0o777)
        
        # URL do endpoint para criar usuários
        url = "http://localhost:8085/api/v2/users"
        # Cabeçalhos com o token de autenticação
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # Corpo da requisição
        payload = {
            "status": 1,
            "username": simples_usuario,
            "password": simples_senha,
            "home_dir" : simples_base_diretorio ,
            "filesystem": {
                "provider": 0
            },
            "permissions": {
                "/": [
                "*"
                ]
            },
        }

        # Requisição POST para criar o usuário
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            print(f"Usuário '{simples_usuario}' criado com sucesso!")
            #print(response.json())
        else:
            print(f"Erro ao criar usuário '{simples_usuario}': {response.status_code}")
            print(response.json())
        pass
