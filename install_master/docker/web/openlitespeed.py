import os
import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinOpenLiteSpeed(DockerBase):

    def instala_openlitespeed(self,):
        print("Instalando openlitespeed.")
        conf_completa = f"{self.install_principal}/openlitespeed/conf_completa"
        copiar = False
        if os.path.exists(conf_completa):
            if os.path.isdir(conf_completa):
                if not os.listdir(conf_completa):  # Retorna vazio se a pasta não contém arquivos ou subpastas
                    # return f"A pasta '{conf_completa}' existe e está vazia."
                    copiar = True
                else:
                    # return f"A pasta '{conf_completa}' existe, mas não está vazia."
                    pass
            else:
                # return f"O caminho '{conf_completa}' existe, mas não é uma pasta."
                copiar = True
        else:
            # return f"A pasta '{conf_completa}' não existe."
            copiar = True
        
        if copiar:
            # os.rmdir(conf_completa)
            os.makedirs(conf_completa, exist_ok=True)
            os.chmod(conf_completa, 0o777)
            container = f"""docker run -d \
                            --name openlitespeed \
                            --restart=unless-stopped \
                            litespeedtech/openlitespeed:latest
                    """
            
            self.remove_container('openlitespeed')
            comandos = [
                container,
                f"docker cp openlitespeed:/usr/local/lsws/. {conf_completa}",
                ]
            resultados = self.executar_comandos(comandos)
        
        container = f"""docker run -d \
                            --name openlitespeed \
                            --restart=unless-stopped \
                            --memory=1g \
                            --cpus=1 \
                            -p 8088:8088 \
                            -p 7080:7080 \
                            -v {self.install_principal}/openlitespeed/vhosts:/var/www/vhosts \
                            -v {conf_completa}:/usr/local/lsws \
                            litespeedtech/openlitespeed:latest
                    """
            
        self.remove_container('openlitespeed')
        comandos = [
            container,
            ]
        resultados = self.executar_comandos(comandos)
        self.cria_rede_docker(associar_container_nome=f'openlitespeed', numero_rede=0)
        
        # Instalar extensões PHP
        print("\n" + "="*60)
        print("Instalando PHP 8.4 e extensões...")
        print("="*60)
        
        script_bash = """set +e
export DEBIAN_FRONTEND=noninteractive

echo "Instalando PHP 8.4..."
apt-get update

# Instala o PHP 8.4 e extensões
echo "Instalando lsphp84 e extensões disponíveis..."
for ext in "" pgsql mysql curl common imap opcache gd; do
    pkg="lsphp84${ext:+-}${ext}"
    echo -n "  - ${pkg}: "
    if apt-get install -y ${pkg} >/dev/null 2>&1; then
        echo "OK"
    else
        echo "Não disponível"
    fi
done

# Define o PHP 8.4 como padrão
echo ""
echo "Configurando PHP 8.4 como padrão..."
ln -sf /usr/local/lsws/lsphp84/bin/lsphp /usr/local/lsws/fcgi-bin/lsphp

# Reinicia o servidor
/usr/local/lsws/bin/lswsctrl restart >/dev/null 2>&1

echo ""
echo "Versão PHP instalada:"
/usr/local/lsws/lsphp84/bin/php -v
echo ""
echo "Extensões PHP instaladas:"
/usr/local/lsws/lsphp84/bin/php -m | sort
"""
        subprocess.run(
            ["docker", "exec", "-u", "root", "-it", "openlitespeed", "bash", "-lc", script_bash],
            check=True,
            text=True
        )
        
        # Cria arquivo de configuração personalizado do PHP
        print("\n" + "="*60)
        print("Criando arquivo de configuração personalizado do PHP...")
        print("="*60)
        
        php_custom_ini_path = f"{conf_completa}/lsphp84/etc/php/8.4/mods-available/99-custom.ini"
        os.makedirs(os.path.dirname(php_custom_ini_path), exist_ok=True)
        
        php_custom_config = """;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Configurações Personalizadas PHP 8.4 - OpenLiteSpeed
; Arquivo: 99-custom.ini
; 
; Este arquivo contém APENAS configurações customizadas que sobrescrevem o php.ini padrão
; Edite conforme suas necessidades específicas
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

[PHP]
; ============================================================================
; TIMEOUTS E LIMITES DE RECURSOS
; ============================================================================
max_execution_time = 300
max_input_time = 300
default_socket_timeout = 300
memory_limit = 1024M
max_input_vars = 5000

; ============================================================================
; UPLOAD DE ARQUIVOS
; ============================================================================
upload_max_filesize = 1024M
post_max_size = 1024M
max_file_uploads = 20

; ============================================================================
; TIMEZONE
; ============================================================================
date.timezone = America/Sao_Paulo

; ============================================================================
; ERROS E LOGS (PRODUÇÃO)
; ============================================================================
display_errors = Off
display_startup_errors = Off
log_errors = On
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT

; ============================================================================
; SEGURANÇA - Funções desabilitadas
; Remova funções desta lista se precisar usá-las
; ============================================================================
disable_functions = exec,passthru,shell_exec,system,proc_open,popen

; ============================================================================
; OPCACHE - OTIMIZAÇÕES DE PERFORMANCE
; ============================================================================
[opcache]
opcache.enable = 1
opcache.enable_cli = 0
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 20000
opcache.validate_timestamps = 1
opcache.revalidate_freq = 2
opcache.save_comments = 1
opcache.enable_file_override = 1
opcache.fast_shutdown = 1

; ============================================================================
; SESSION - SEGURANÇA
; ============================================================================
[Session]
session.cookie_httponly = 1
session.cookie_samesite = Lax
session.use_strict_mode = 1
session.gc_maxlifetime = 3600

; ============================================================================
; MYSQLI - Configurações padrão
; ============================================================================
[MySQLi]
mysqli.default_socket = /var/run/mysqld/mysqld.sock

; ============================================================================
; POSTGRESQL
; ============================================================================
[PostgreSQL]
pgsql.allow_persistent = On

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; INSTRUÇÕES DE USO:
;
; 📝 Para editar: nano /install_principal/openlitespeed/conf_completa/lsphp84/etc/php/8.4/mods-available/99-custom.ini
; 🔄 Após editar: docker exec openlitespeed /usr/local/lsws/bin/lswsctrl restart
; 📊 Ver configurações: docker exec openlitespeed /usr/local/lsws/lsphp84/bin/php -i | grep -i "nome_da_config"
;
; EXEMPLOS DE CUSTOMIZAÇÃO:
; - Para debug: display_errors = On
; - Mais memória: memory_limit = 2048M
; - Uploads maiores: upload_max_filesize = 2048M
; - Timeout maior: max_execution_time = 600
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
"""
        with open(php_custom_ini_path, 'w') as f:
            f.write(php_custom_config)
        
        os.chmod(php_custom_ini_path, 0o644)
        
        print(f"✔ Arquivo de configuração criado: {php_custom_ini_path}")
        
        # Reinicia o container para aplicar as mudanças
        print("Reiniciando o container OpenLiteSpeed...")
        subprocess.run(
            ["docker", "restart", "openlitespeed"],
            check=True
        )
        time.sleep(10)  # Aguarda o container reiniciar completamente
        
        print(" ")
        print("Configurações de openlitespeed concluídas.")
        print(" ")
        print("Caminho de instalação:")
        print(f"{self.install_principal}/vhosts")
        print(" ")
        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
            ]
        resultados = self.executar_comandos(comandos)
        print("Porta de acesso: 7080")
        print(" ")
        print("Acesso padrão:")
        print("Usuario: admin")
        print("Senha: 123456")
        print(" ")
        print("Vá para a seção Security no painel de administração.")
        print("Escolha a opção Admin Password.")
        print("Insira a nova senha desejada e salve as alterações.")
        print(" ")
        
    def controle_sites_openlitespeed(self,):
        
        self.verifica_container_existe('openlitespeed', self.instala_openlitespeed)
        
        nome_dominio = input('Digite o dominio: ')
        senha_ftp = input('Digite uma senha para o ftp: ')
        nome_dominio_ = nome_dominio.replace('.', '_')
        resposta_traefik = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta_traefik.lower() == 's':
            self.adiciona_roteador_servico_traefik(nome_dominio, endereco='openlitespeed', porta='8088')
        sites_dir = f"{self.install_principal}/openlitespeed"
        # Diretório do site
        #/usr/local/lsws/
        site_dir = os.path.join(sites_dir, "vhosts", nome_dominio_)
        public_html = os.path.join(site_dir, "public_html")
        conf_dir = os.path.join(sites_dir, "conf_completa", "conf", "vhosts", nome_dominio_)
        listener_conf_path = os.path.join(sites_dir, "conf_completa", "conf", "httpd_config.conf")
        
        # Cria os diretórios necessários
        os.makedirs(public_html, exist_ok=True)
        os.makedirs(conf_dir, exist_ok=True)
        
        # Cria um arquivo de índice básico
        index_path = os.path.join(public_html, "index.php")
        if not os.path.exists(index_path):
            with open(index_path, "w") as index_file:
                index_file.write("<?php echo 'Site criado com sucesso! ' . $_SERVER['HTTP_HOST']; ?>")
        
        # Configuração do Virtual Host
        vhost_conf_path = os.path.join(conf_dir, "vhconf.conf")
        with open(vhost_conf_path, "w") as vhost_file:
            vhost_file.write(f"""\
docRoot                   /var/www/vhosts/{nome_dominio_}/public_html/
vhDomain                  {nome_dominio}
indexFiles                index.php, index.html
""")
        
        self.gerenciar_permissoes_pasta(site_dir, permissao='777')
        
        # Configuração do Virtual Host e Listener no httpd_config.conf
        virtualhost_config = f"""
virtualhost {nome_dominio_} {{
  vhRoot                  /var/www/vhosts/{nome_dominio_}/
  configFile              $SERVER_ROOT/conf/vhosts/$VH_NAME/vhconf.conf
  allowSymbolLink         1
  enableScript            1
  restrained              1
}}
"""
        listener_config = f"""
listener Default {{
  address                 *:8088
  secure                  0
  map                     Example *
  map                     {nome_dominio_} {nome_dominio}
}}
"""
        
        # Adiciona a configuração do Virtual Host e Listener se não existirem
        with open(listener_conf_path, "r+") as listener_file:
            content = listener_file.read()
            if virtualhost_config.strip() not in content:
                listener_file.write(virtualhost_config)
                print(f"Virtual Host para '{nome_dominio_}' adicionado.")
            else:
                print(f"Virtual Host para '{nome_dominio_}' já existe.")
            
            if listener_config.strip() not in content:
                listener_file.write(listener_config)
                print(f"Listener para '{nome_dominio_}' adicionado.")
            else:
                print(f"Listener para '{nome_dominio_}' já existe.")
        
        self.gerenciar_usuarios_sftp(manual=False, simples_usuario=nome_dominio_, simples_senha=senha_ftp, simples_base_diretorio=public_html)
        
        # Ajusta permissões para o usuário nobody (usuário do OpenLiteSpeed)
        print(f"Ajustando permissões do site '{nome_dominio_}'...")
        comandos_permissoes = [
            f"docker exec openlitespeed chown -R nobody:nogroup /var/www/vhosts/{nome_dominio_}",
            f"docker exec openlitespeed chmod -R 755 /var/www/vhosts/{nome_dominio_}",
            f"docker exec openlitespeed chmod -R 775 /var/www/vhosts/{nome_dominio_}/public_html",
        ]
        self.executar_comandos(comandos_permissoes)
        
        self.executar_comandos(['docker restart openlitespeed'], comando_direto=True)
        
        print(f"Configuração do site '{nome_dominio_}' criada com sucesso!")
        print(f"Arquivos criados em: {site_dir}")
