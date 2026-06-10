import os
import json
import textwrap
import time

from install_master.core.docker_base import DockerBase


class MixinNodeJS(DockerBase):

    def instala_app_nodejs(self,):
        nome_dominio = input('Digite o dominio sem o www ou nome do projeto: ')
        desenvolvimento = input('O container é para desenvolvimento?: (s/n): ')
        
        if desenvolvimento.lower() != 's':
            senha_ftp = input('Digite uma senha para acessar por SFTP: ')
        
        # self.verifica_container_existe('redis', self.instala_redis_docker)
        nome_dominio_ = nome_dominio.replace('.', '_')
        portas = self.escolher_porta_disponivel()
        
        diretorio_projeto = f"{self.install_principal}/node/{nome_dominio_}"
        # Verifica se o diretório do projeto já existe
        if os.path.exists(diretorio_projeto):
            resposta = input(f"O diretório {diretorio_projeto} já existe. Deseja removê-lo? (s/n): ")
            if resposta.lower() == 's':
                comandos = [
                    f"rm -rf {diretorio_projeto}",
                ]
                self.executar_comandos(comandos)
        self.gerenciar_permissoes_pasta(diretorio_projeto, '777')
        
        dir_dados_arquivos = f"{diretorio_projeto}/arquivos"
        os.makedirs(dir_dados_arquivos, exist_ok=True)
        
        dir_dados_assets = f"{diretorio_projeto}/assets"
        os.makedirs(dir_dados_assets, exist_ok=True)
        
        dir_dados_assets_public = f"{dir_dados_assets}/public"
        os.makedirs(dir_dados_assets_public, exist_ok=True)
        
        dir_dados_assets_scripts_python = f"{dir_dados_assets}/scripts_python"
        os.makedirs(dir_dados_assets_scripts_python, exist_ok=True)
        
        dir_dados_assets_scripts_node = f"{dir_dados_assets}/scripts_node"
        os.makedirs(dir_dados_assets_scripts_node, exist_ok=True)
        
        if desenvolvimento.lower() != 's':
            self.gerenciar_usuarios_sftp(manual=False, simples_usuario=nome_dominio_, simples_senha=senha_ftp, simples_base_diretorio=diretorio_projeto)
        
        # Define a estrutura do package.json
        package_json = {
            "name": nome_dominio_,
            "version": "1.0",
            "main": "index.js",
            "scripts": {
                "prestart": "npm install",
                "start": "nodemon"
            },
            "dependencies": {
                "nodemon": "^2.0.0",
                "express": "^4.17.2"
            },
        }
        # Caminho para o arquivo package.json 
        caminho_package_json = os.path.join(diretorio_projeto, "package.json")
        if not os.path.exists(caminho_package_json):
            # Escreve o conteúdo no arquivo package.json
            with open(caminho_package_json, "w") as arquivo:
                json.dump(package_json, arquivo, indent=4)
            print(f"Arquivo package.json criado em {caminho_package_json}")
            
        yml_content = textwrap.dedent("""\
            name: SFTP Deploy

            on:
            push:
                branches:
                - main

            concurrency:
            group: sftp-deploy
            cancel-in-progress: false

            jobs:
            deploy:
                name: Deploy via SFTP
                runs-on: ubuntu-latest

                steps:
                - name: Checkout repository
                    uses: actions/checkout@v3

                - name: Install LFTP
                    run: sudo apt-get install -y lftp

                - name: Deploy files to server
                    env:
                    SFTP_HOST: ${{ secrets.SFTP_HOST }}
                    SFTP_USER: ${{ secrets.SFTP_USER }}
                    SFTP_PASSWORD: ${{ secrets.SFTP_PASSWORD }}
                    run: |
                    lftp -u "$SFTP_USER","$SFTP_PASSWORD" sftp://$SFTP_HOST:2025 <<EOF
                    set sftp:connect-program "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
                    mirror --reverse --only-newer --ignore-time --verbose \\
                    --exclude-glob .git/ \\
                    --exclude-glob node_modules/ \\
                    --exclude-glob python_env/ \\
                    --exclude-glob arquivos/ \\
                    --exclude-glob package-lock.json \\
                    ./ /
                    bye
                    EOF
            """)
        
        caminho_yml = os.path.join(diretorio_projeto, ".github", "workflows", "sftp-deploy.yml")
        os.makedirs(os.path.dirname(caminho_yml), exist_ok=True)
        if not os.path.exists(caminho_yml):
            with open(caminho_yml, "w") as arquivo:
                arquivo.write(yml_content)
            print(f"Arquivo sftp-deploy.yml criado em {caminho_yml}")
            
        nodemon_json = {
            "ignore": [
                "/root/.npm/**/*",
                ".vscode",
                "package-lock.json",
                "arquivos",
                ".git",
                "python_env",
                "node_modules",
                "*.log*"
            ],
            "exec": "npm install && node index.js"
        }
        # Caminho para o arquivo nodemon.json
        caminho_nodemon_json = os.path.join(diretorio_projeto, "nodemon.json")
        if not os.path.exists(caminho_nodemon_json):
            # Escreve o conteúdo no arquivo nodemon.json
            with open(caminho_nodemon_json, "w") as arquivo:
                json.dump(nodemon_json, arquivo, indent=4)
            print(f"Arquivo nodemon.json criado em {caminho_nodemon_json}")
            
        index_html = textwrap.dedent("""\
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bem-vindo</title>
            <style>
                body {
                margin: 0;
                font-family: Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                background: linear-gradient(135deg, #6a11cb, #2575fc);
                color: white;
                text-align: center;
                }
                h1 {
                font-size: 3rem;
                margin-bottom: 0.5rem;
                }
                p {
                font-size: 1.5rem;
                margin-bottom: 1rem;
                }
                .button-container {
                margin-top: 2rem;
                }
                a {
                text-decoration: none;
                color: #ffffff;
                background-color: #ff7f50;
                padding: 0.8rem 1.5rem;
                border-radius: 5px;
                font-size: 1.2rem;
                transition: background-color 0.3s ease;
                }
                a:hover {
                background-color: #ff6347;
                }
            </style>
            </head>
            <body>
                <div>
                    <h1>Bem-vindo ao Servidor Node.js com Python.</h1>
                    <p>Seu ambiente está configurado e funcionando corretamente.</p>
                    <div class="button-container">
                    <a href="/teste">Ir para a pagina de teste</a>
                    </div>
                </div>
            </body>
            </html>
            """)
        
        # Caminho para o arquivo index.html
        caminho_index_html = os.path.join(dir_dados_assets_public, "index.html")
        if not os.path.exists(caminho_index_html):
            # Cria e escreve o conteúdo no arquivo index.html
            with open(caminho_index_html, "w") as arquivo:
                arquivo.write(index_html)
            print(f"Arquivo index.html criado em {caminho_index_html}")

        index_js = textwrap.dedent(f"""\
            require('./assets/scripts_node/start.js');
            """)
        
        # Caminho para o arquivo index.js
        caminho_index_js = os.path.join(diretorio_projeto, "index.js")
        if not os.path.exists(caminho_index_js):
            # Escreve o conteúdo no arquivo index.js
            with open(caminho_index_js, "w") as arquivo:
                arquivo.write(index_js)
            print(f"Arquivo index.js criado em {caminho_index_js}")
            
        start_js = textwrap.dedent(f"""\
            // Importa o setupPythonEnv
            const {{ setupPythonEnv, runPythonScript }} = require('./setupPythonEnv');
            const express = require('express');
            const app = express();
            const PORT = {portas[0]};
            const path = require('path');

            // Diretório publico do projeto
            app.use('/public', express.static(path.join(__dirname, '../public')));

            // Diretório raiz do projeto
            const projectRoot = path.dirname(require.main.filename);

            pythonOutput = 'Aguardando ambiente Python...';

            app.listen(PORT, () => {{
            console.log(`Servidor rodando na porta {portas[0]}`);
            }});

            ///////////////////////////////////////////////////////////////////////////////////////////////////
            // Criação de rotas Nodejs adicionais aqui...

            // Rota de testes
            app.get('/teste', (req, res) => {{
            const responseText = `
            Servidor Node.js com Express funcionando!<br>
            ${{pythonOutput}}
            `;
            res.send(responseText);
            }});

            // Rota index.html
            app.get('/', (req, res) => {{
            const htmlPath = path.join(projectRoot, 'assets', 'public', 'index.html');
            res.sendFile(htmlPath);
            }});

            ///////////////////////////////////////////////////////////////////////////////////////////////////

            // Configura o ambiente Python em paralelo
            setupPythonEnv(() => {{
            console.log('Terminada a configuração do ambiente Python.');
            
            ///////////////////////////////////////////////////////////////////////////////////////////////////
            // Rotas dos scripts Python
            
            // Rota do start.py
            runPythonScript('start.py', (error, output) => {{
            if (error) {{
                console.error('Erro ao executar o script:', error);
                return;
            }}
                console.log('Saída recebida do script Python:', output);
                pythonOutput = output; // Armazena o resultado do script
            }});
            
            ///////////////////////////////////////////////////////////////////////////////////////////////////

            }});
            """)
        
        # Caminho para o arquivo start.js
        caminho_start_js = os.path.join(dir_dados_assets_scripts_node, "start.js")
        if not os.path.exists(caminho_start_js):
            # Escreve o conteúdo no arquivo start.js
            with open(caminho_start_js, "w") as arquivo:
                arquivo.write(start_js)
            print(f"Arquivo start.js criado em {caminho_start_js}")
        
        # Conteúdo do arquivo setupPythonEnv.js
        setup_python_env_js = textwrap.dedent("""\
            const { exec } = require('child_process');
            const path = require('path');
            const fs = require('fs');

            // Diretório raiz do projeto
            const projectRoot = path.dirname(require.main.filename);

            const scripts_python = path.join(projectRoot, 'assets', 'scripts_python'); // Diretório do ambiente virtual Python
            const pythonDir = path.join(projectRoot, 'python_env'); // Diretório do ambiente virtual Python
            const pythonBin = path.join(pythonDir, 'bin', 'python'); // Python do ambiente virtual
            const pipPath = path.join(pythonDir, 'bin', 'pip');
            const requirementsFile = path.join(projectRoot, 'requirements.txt');

            // Instala Python3 e ferramentas necessárias
            function installPython(callback) {
            const installCmd = 'sudo apt update && apt install -y python3 python3-pip python3-venv';

            console.log('Instalando Python3 e ferramentas...');
            exec(installCmd, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao instalar Python3: ' + stderr);
                return;
                }
                console.log('Python3 e ferramentas instalados com sucesso.');
                if (callback) callback();
            });
            }

            // Cria o ambiente virtual, se necessário
            function createVirtualEnv(callback) {
            console.log('Criando ambiente virtual...');
            exec('python3 -m venv ' + pythonDir, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao criar o ambiente virtual: ' + stderr);
                return;
                }
                console.log('Ambiente virtual criado com sucesso.');
                if (callback) callback();
            });
            }

            // Instala dependências do arquivo requirements.txt
            function installDependencies(callback) {
            if (!fs.existsSync(requirementsFile)) {
                console.error('Erro: O arquivo requirements.txt não foi encontrado.');
                return;
            }

            console.log('Instalando dependências no ambiente virtual...');
            exec(pipPath + ' install -r ' + requirementsFile, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao instalar dependências: ' + stderr);
                return;
                }
                console.log('Dependências instaladas com sucesso.');
                if (callback) callback();
            });
            }

            // Configura o ambiente Python
            function setupPythonEnv(callback) {
            if (fs.existsSync(path.join(pythonDir, 'bin', 'python'))) {
                console.log('Ambiente virtual já existe. Instalando dependências...');
                installDependencies(() => {
                if (callback) callback();
                });
            } else {
                console.log('Ambiente virtual não encontrado. Atualizando ferramentas e criando...');
                installPython(() => {
                createVirtualEnv(() => {
                    installDependencies(() => {
                    if (callback) callback();
                    });
                });
                });
            }
            }

            // Função para garantir que um script Python exista (como "start.py")
            function createStartPy() {
            // Garante que o diretório de scripts Python exista
            if (!fs.existsSync(scripts_python)) {
                console.log(`Criando o diretório: ${scripts_python}`);
                fs.mkdirSync(scripts_python, { recursive: true });
                console.log(`Diretório ${scripts_python} criado com sucesso.`);
            }
            
            const scriptPath = path.join(scripts_python, 'start.py');
            if (!fs.existsSync(scriptPath)) {
                console.log(`Criando o script ${path.basename(scriptPath)}...`);
                const content = `# ${path.basename(scriptPath)}\nprint("O ambiente Python está funcionando corretamente!")\n`;
                fs.writeFileSync(scriptPath, content);
                console.log(`Script ${path.basename(scriptPath)} criado com sucesso.`);
            } else {
                console.log(`O script ${path.basename(scriptPath)} já existe.`);
            }
            }

            // Função para rodar o script Python com nome dinâmico e capturar a saída via callback
            function runPythonScript(scriptName, callback) {
            const scriptPy = path.join(scripts_python, scriptName);

            // Verifica se o script fornecido existe
            if (!fs.existsSync(scriptPy)) {
                console.warn(`O script "${scriptName}" não foi encontrado. Rodando o script padrão para testes "start.py"...`);
                createStartPy(); // Garante que start.py exista
                runPythonScript('start.py', callback); // Rechama a função para rodar o start.py
                return;
            }

            console.log(`Executando o script Python: ${scriptName}...`);

            exec(`${pythonBin} ${scriptPy}`, (error, stdout, stderr) => {
                if (error) {
                console.error('Erro ao executar o script Python: ' + stderr);
                callback(stderr, null);
                return;
                }
                console.log('Script Python executado com sucesso.');
                // console.log(stdout);
                callback(null, stdout); // Passa a saída do script para o callback
            });
            }

            module.exports = { setupPythonEnv, runPythonScript };
            """)
        
        # Caminho para o arquivo setupPythonEnv.js
        caminho_setup_python_env_js = os.path.join(dir_dados_assets_scripts_node, "setupPythonEnv.js")
        if not os.path.exists(caminho_setup_python_env_js):
            # Escreve o conteúdo no arquivo setupPythonEnv.js
            with open(caminho_setup_python_env_js, "w") as arquivo:
                arquivo.write(setup_python_env_js)
            print(f"Arquivo setupPythonEnv.js criado em {caminho_setup_python_env_js}")
        
        # Lista de dependências
        dependencias = [
            "psycopg2",
            "xmltodict",
            "paramiko"
        ]
        # Caminho para o arquivo requirements.txt
        caminho_requirements = os.path.join(diretorio_projeto, "requirements.txt")
        # Escreve as dependências no arquivo
        if not os.path.exists(caminho_requirements):
            with open(caminho_requirements, "w") as arquivo:
                arquivo.write("\n".join(dependencias))
        desenvolvimento_atuvacao = 'npm start'
        if desenvolvimento.lower() == 's':
            desenvolvimento_atuvacao = 'sleep infinity'
            
        print(f'Porta interna para uso: {portas[0]}')
        
        comandos = [
            f"""docker run -d \
                --name {nome_dominio_} \
                --restart=unless-stopped \
                --memory=256m \
                --cpus=1 \
                -p {portas[0]}:{portas[0]} \
                -v {diretorio_projeto}:/usr/src/app:rw \
                -w /usr/src/app \
                node:latest \
                /bin/sh -c \"{desenvolvimento_atuvacao}\"
            """,
            ]
        self.remove_container(nome_dominio_)
        self.gerenciar_permissoes_pasta(diretorio_projeto, '777')
        self.executar_comandos(comandos)
        
        print("Instalação concluída. O projeto está pronto para uso.")
        print(f"Acesse o projeto pelo IP do servidor na porta {portas[0]}")
