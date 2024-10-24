#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.sh https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.sh && sudo bash install_master.sh

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "==========================================================================="
echo "==========================================================================="
echo " "
echo "Arquivo install_master.sh iniciado!"
echo " "
echo "Versão 2.31"
echo " "
echo "==========================================================================="
echo "==========================================================================="
echo " "
echo " "

instala_docker(){
    echo "instalando docker..."
    apt update && apt upgrade -y
    #https://docs.docker.com/engine/install/ubuntu/

    for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update

    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    cria_rede_docker
}

verifica_instalacao_docker(){
    if ! command -v docker &> /dev/null; then
        echo "Docker não está instalado. Instalando agora..."
        instala_docker
    fi
    cria_rede_docker
}

instala_mongodb_docker(){
    echo "Instalando o MongoDB Docker..."
    container_name="mongodb"
    
    # Checa se o container já está em execução
    if sudo docker ps -q -f name=^/${container_name}$; then
        echo "O container $container_name já está em execução."
        return
    fi

    DATA_DIR_MONGODB="${DIR_Principal}/mongodb"
    options=("Local padrão ($DATA_DIR_MONGODB)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR_MONGODB)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR_MONGODB
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done

    # Cria a estrutura de diretórios e arquivos necessários
    echo "Preparando instalação em: $DATA_DIR_MONGODB"
    sudo mkdir -p $DATA_DIR_MONGODB
    sudo chmod 777 $DATA_DIR_MONGODB  # Considere usar permissões mais restritivas

    # Cria e inicia o container MongoDB
    sudo docker run -d \
        --name $container_name \
        --restart always \
        -p 27017:27017 \
        --network rede_docker \
        -v $DATA_DIR_MONGODB:/data/db \
        mongo:latest
    
    echo "MongoDB Docker está configurado e rodando."
}

cria_rede_docker(){
    NETWORK_NAME="rede_docker"
    # Verifica se a rede já existe
    if ! docker network ls | grep -wq $NETWORK_NAME; then
        echo "Rede '$NETWORK_NAME' não encontrada. Criando rede..."
        docker network create $NETWORK_NAME
        echo "Rede '$NETWORK_NAME' criada com sucesso."
    else
        echo "Rede '$NETWORK_NAME' já existe."
    fi

    # Associa todos os containers existentes à rede
    for container_id in $(docker ps -q); do
        echo "Associando container $container_id à rede '$NETWORK_NAME'..."
        docker network connect $NETWORK_NAME $container_id
        echo "Container $container_id associado à rede '$NETWORK_NAME' com sucesso."
    done
}

instala_pritunel_docker(){
    echo " "
    echo "Instalando Pritunel via Docker..."
    echo "Escolha a opção de instalação:"

    # Definição do diretório padrão
    DATA_DIR_pritunl="${DIR_Principal}/pritunl"
    options=("Local padrão ($DATA_DIR_pritunl)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR_pritunl)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR_pritunl
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done

    verifica_instalacao_docker

    # Preparação do ambiente
    echo "Preparando a instalação em: $DATA_DIR_pritunl"
    sudo rm -rf ${DATA_DIR_pritunl}
    sudo mkdir -p ${DATA_DIR_pritunl}/pritunl ${DATA_DIR_pritunl}/mongodb
    sudo touch ${DATA_DIR_pritunl}/pritunl.conf

    # Remoção de container pré-existente
    sudo docker rm -f pritunl

    # Execução do container Docker
    docker run \
        --name pritunl \
        --privileged \
        --publish 81:80 \
        --publish 447:443 \
        --publish 446:446 \
        --publish 11940:11940 \
        --publish 11940:11940/udp \
        --publish 11941:11941 \
        --publish 11941:11941/udp \
        --publish 11942:11942 \
        --publish 11942:11942/udp \
        --publish 11943:11943 \
        --publish 11943:11943/udp \
        --publish 11944:11944 \
        --publish 11944:11944/udp \
        --publish 11945:11945 \
        --publish 11945:11945/udp \
        --dns 127.0.0.1 \
        --restart=unless-stopped \
        --detach \
        --volume ${DATA_DIR_pritunl}/pritunl.conf:/etc/pritunl.conf \
        --volume ${DATA_DIR_pritunl}/pritunl:/var/lib/pritunl \
        --volume ${DATA_DIR_pritunl}/mongodb:/var/lib/mongodb \
        ghcr.io/jippi/docker-pritunl

    echo "Aguarde enquanto o container é inicializado..."
    sleep 30

    # Configuração inicial pós-instalação
    sudo docker exec pritunl pritunl reset-password
    echo "Instalação concluída. Pritunl está pronto para uso."
    echo "porta de acesso: 447"
    echo "Mude a porta da interface apos logar para: 446"
    echo "Mude a porta do servidor apos logar para: 11944"
    echo "IPs possíveis para acesso:"
    hostname -I | tr ' ' '\n'
    echo "Acesse o container com: sudo docker exec -it pritunl /bin/bash"
}


instala_postgres_docker(){
    echo "Instalando postgres docker..."
    
    # Definição do diretório padrão
    DATA_DIR="${DIR_Principal}/postgres"
    options=("Local padrão ($DATA_DIR)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done

    verifica_instalacao_docker
        
    # Remover container existente se houver
    docker rm -f postgres
    sudo rm -rf ${DATA_DIR}

    # Rodar novo container PostgreSQL com configurações de log
    docker run -d \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_USER=postgres \
        --name postgres \
        --restart always \
        -p 5432:5432 \
        -v $DATA_DIR:/var/lib/postgresql/data \
        -m 512M \
        --log-opt max-size=10m \
        --log-opt max-file=3 \
        postgres:15.3

    # Esperar um pouco para o container iniciar
    sleep 10

    # Ajustar configuração de logs dentro do container
    docker exec postgres bash -c "echo \"log_min_messages = warning\" >> /var/lib/postgresql/data/postgresql.conf"
    docker exec postgres bash -c "echo \"log_statement = 'none'\" >> /var/lib/postgresql/data/postgresql.conf"

    # Reiniciar o PostgreSQL para aplicar configurações
    docker restart postgres
}

instala_postgres_docker_primario(){
    echo "Instalando postgres docker..."

    # Definição do diretório padrão
    DATA_DIR="${DIR_Principal}/postgres1"
    options=("Local padrão ($DATA_DIR)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done

    verifica_instalacao_docker
        
    # Remover container existente se houver
    echo ${DATA_DIR}
    docker rm -f postgres1
    sudo rm -rf ${DATA_DIR}

    # recriando diretorios
    mkdir -p ${DATA_DIR}
    
    # Rodar novo container PostgreSQL com configurações de log
    docker run -d \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_USER=postgres \
        --name postgres1 \
        --restart always \
        -p 5432:5432 \
        -v ${DATA_DIR}:/var/lib/postgresql/data \
        -m 512M \
        --log-opt max-size=10m \
        --log-opt max-file=3 \
        postgres:15.3

    # Esperar um pouco para o container iniciar
    sleep 10

    # Ajustar configuração de logs dentro do container
    docker exec postgres1 bash -c "echo \"log_min_messages = warning\" >> /var/lib/postgresql/data/postgresql.conf"
    docker exec postgres1 bash -c "echo \"log_statement = 'none'\" >> /var/lib/postgresql/data/postgresql.conf"

    docker stop postgres1

    echo 'wal_level = replica' >> $DATA_DIR/postgresql.conf
    echo 'max_wal_senders = 3' >> $DATA_DIR/postgresql.conf
    echo 'wal_keep_size = 500' >> $DATA_DIR/postgresql.conf
    echo "archive_mode = on" >> $DATA_DIR/postgresql.conf
    # Criar diretório de arquivamento
    ARCHIVE_DIR="${DATA_DIR}/archive"
    mkdir -p ${ARCHIVE_DIR}
    echo "archive_command = 'cp %p ${ARCHIVE_DIR}/%f'" >> $DATA_DIR/postgresql.conf

    echo 'host replication postgres 0.0.0.0/0 md5' >> $DATA_DIR/pg_hba.conf

    # Reiniciar o PostgreSQL para aplicar configurações
    docker restart postgres1

    # Criar slot de replicação
    sleep 10
    docker exec -it postgres1 psql -U postgres -c "SELECT * FROM pg_create_physical_replication_slot('meu_slot');"
}

instala_postgres_docker_secundario(){
    echo "Instalando postgres docker..."

    # Definição do diretório padrão
    DATA_DIR="${DIR_Principal}/postgres2"
    options=("Local padrão ($DATA_DIR)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done

    verifica_instalacao_docker
        
    # Remover container existente se houver
    docker rm -f postgres2
    sudo rm -rf ${DATA_DIR}
    
    # Rodar novo container PostgreSQL com configurações de log
    docker run -d \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_USER=postgres \
        --name postgres2 \
        --restart always \
        -p 5432:5432 \
        -v $DATA_DIR:/var/lib/postgresql/data \
        -m 512M \
        --log-opt max-size=10m \
        --log-opt max-file=3 \
        postgres:15.3

    # Esperar um pouco para o container iniciar
    sleep 10

    # Ajustar configuração de logs dentro do container
    docker exec postgres2 bash -c "echo \"log_min_messages = warning\" >> /var/lib/postgresql/data/postgresql.conf"
    docker exec postgres2 bash -c "echo \"log_statement = 'none'\" >> /var/lib/postgresql/data/postgresql.conf"

    read -p "Digite o IP da máquina primária: " PRIMARY_IP
    docker stop postgres2

    sudo rm -rf $DATA_DIR/*

    # Copiar dados do primário
    docker run --rm -v $DATA_DIR:/var/lib/postgresql/data postgres:15.3 bash -c "
    PGPASSWORD=postgres pg_basebackup -h $PRIMARY_IP -D /var/lib/postgresql/data -U postgres -P --wal-method=stream
    "

    cat >> $DATA_DIR/postgresql.conf <<EOF
primary_conninfo = 'host=$PRIMARY_IP port=5432 user=postgres password=postgres'
primary_slot_name = 'meu_slot'
EOF

    # Criar o sinalizador de recuperação
    touch $DATA_DIR/standby.signal

    # Criar diretório de arquivamento
    ARCHIVE_DIR="${DATA_DIR}/archive"
    mkdir -p ${ARCHIVE_DIR}

    # Reiniciar o PostgreSQL para aplicar configurações
    docker start postgres2
}

# Função para ativar o secundário como primário
ativa_postgres_docker_secundario_primario() {
    docker exec -it postgres2 bash -c "
    touch /tmp/postgresql.trigger
    pg_ctl promote -D /var/lib/postgresql/data
    "
}

cria_pasta_compartilhada(){

    echo "Criando pasta compartilhada..."
    
    # Atualiza os repositórios e instala o Samba
    sudo apt-get update
    sudo apt-get install samba -y

    # Cria uma pasta compartilhada
    sudo mkdir -p "${DIR_Principal}/compartilhado"
    sudo chmod 777 "${DIR_Principal}/compartilhado"

    # Adiciona configuração ao smb.conf
    echo "
    [Compartilhado]
        comment = Pasta Compartilhada
        path = ${DIR_Principal}/compartilhado
        browsable = yes
        guest ok = yes
        read only = no
    " | sudo tee -a /etc/samba/smb.conf

    # Reinicia o serviço Samba para aplicar as configurações
    sudo systemctl restart smbd
}

limpa_containers_imagens_docker(){
    verifica_instalacao_docker  # Assume que esta função verifica e instala o Docker se necessário
    echo "Escolha a opção de limpeza:"
    options=("Limpeza apenas de containers" "Limpeza completa" "Apagar um container específico" "Voltar ao menu principal")
    select opt in "${options[@]}";
    do
        case $opt in
            "Limpeza apenas de containers")
                echo "Iniciando limpeza de containers..."
                sudo docker stop $(sudo docker ps -q)
                sudo docker rm $(sudo docker ps -aq)
                echo "Limpeza de containers concluída."
                break
                ;;
            "Limpeza completa")
                echo "Iniciando limpeza completa..."
                sudo docker stop $(sudo docker ps -q)
                sudo docker rm $(sudo docker ps -aq)
                sudo docker rmi $(sudo docker images -q)
                echo "Limpeza completa realizada."
                break
                ;;
            "Apagar um container específico")
                echo "Listando containers ativos..."
                sudo docker ps
                echo "Digite o ID ou nome do container que deseja apagar:"
                read container_id
                sudo docker stop $container_id
                sudo docker rm $container_id
                echo "Container $container_id apagado."
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done
}



instala_pritunel(){
    sudo tee /etc/apt/sources.list.d/pritunl.list << EOF
    deb http://repo.pritunl.com/stable/apt jammy main
EOF

    # Import signing key from keyserver
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A
    # Alternative import from download if keyserver offline
    curl https://raw.githubusercontent.com/pritunl/pgp/master/pritunl_repo_pub.asc | sudo apt-key add -

    sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list << EOF
    deb https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse
EOF

    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

    sudo apt update
    sudo apt --assume-yes upgrade

    # WireGuard server support
    sudo apt -y install wireguard wireguard-tools

    sudo ufw disable

    sudo apt -y install pritunl mongodb-org
    sudo systemctl enable mongod pritunl
    sudo systemctl start mongod pritunl

}

instala_redis_docker(){
    echo " "
    echo "Iniciando instalação redis_docker:"
    echo " "
    read -p "Configure uma senha para acessar: " SENHA
    # --network host
    docker run --name cont-redis -d --restart always -p 6379:6379 redis redis-server --requirepass "$SENHA"
    # sleep 10
    # docker exec -it cont-redis apt update
    # docker exec -it cont-redis apt-get install nano -y
    echo ""
    echo "Porta de acesso: 6379"
    echo ""
    echo "Realize testes assim:"
    echo "docker exec -it cont-redis redis-cli"
    
    echo "AUTH sua_senha_aqui"
    echo "set meu-teste "funcionando""
    echo "get meu-teste"
    echo " "
}

instala_openlitespeed(){
    mkdir -p "${DIR_Principal}/vhosts"
    docker run -d --name openlitespeed \
        -p 8088:8088 \
        -p 80:80 \
        -p 443:443 \
        -v $DIR_Principal/vhosts:/var/www/vhosts/ \
        litespeedtech/openlitespeed:latest
}

instala_node_docker(){
    echo " "
    echo "Configuração de porta."
    PORTA=3000
    options=("Porta padrão ($PORTA)" "Especificar porta manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Porta padrão ($PORTA)")
                # Diretório já definido
                break
                ;;
            "Especificar porta manualmente")
                read -p "Informe a porta: " PORTA
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done
    # Nome do container
    CONTAINER_NAME=node_container
    

    # Cria o diretório app se não existir
    #sudo rm -rf ${DIR_Principal}/app
    mkdir -p "${DIR_Principal}/app"

    # Cria o arquivo index.js dentro do diretório app
    cat > $DIR_Principal/app/index.js <<EOF
const express = require('express');
const app = express();
const port = $PORTA;

app.get('/', (req, res) => {
    res.send('Node rodando!');
});

app.listen(port, () => {
    console.log(\`Servidor rodando em http://localhost:\${port}\`);
});
EOF

    # Remover container existente se houver
    docker rm -f $CONTAINER_NAME

    # Rodar novo container Node.js com mapeamento de porta e volume
    docker run -d \
        --name $CONTAINER_NAME \
        --restart always \
        -p $PORTA:$PORTA \
        -v $DIR_Principal/app/:/usr/src/app \
        -w /usr/src/app \
        node:latest \
        bash -c "npm init -y && npm install && npm install express && node index.js"

    # Esperar um pouco para o container iniciar
    sleep 10
    # Verifica se o ufw está ativo
    ufw_status=$(sudo ufw status | grep -i "Status: active")
    if [ -n "$ufw_status" ]; then
        echo "UFW está ativo. Aplicando regras..."
        sudo ufw allow $PORTA
        sudo ufw reload
    else
        echo "UFW não está ativo. Pule a configuração do UFW."
    fi

    # Verifica se o iptables está ativo (verifica se há alguma regra configurada)
    iptables_status=$(sudo iptables -L | grep "Chain INPUT (policy")
    if [ -n "$iptables_status" ]; then
        echo "iptables está ativo. Aplicando regras..."
        sudo iptables -A INPUT -p tcp --dport $PORTA -j ACCEPT
        sudo iptables-save | sudo tee /etc/iptables/rules.v4
    else
        echo "iptables não está ativo. Pule a configuração do iptables."
    fi

    echo "Configurações de firewall concluídas."
    echo " "
    echo "Caminho de instalação:"
    echo "${DIR_Principal}/app"
    echo " "
    echo "IPs possíveis para acesso:"
    hostname -I | tr ' ' '\n'
    echo "Porta de acesso: $PORTA"
}

criar_servico_inicializar(){
    # Criar o arquivo de serviço systemd
    cat << 'EOF' > /etc/systemd/system/inicializar.service
[Unit]
Description=Executa o script /teste.txt 30 segundos após a inicialização
After=network.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 30
ExecStart=/bin/bash -c 'docker start postgres'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

    # Recarregar os serviços do systemd para reconhecer o novo serviço
    systemctl daemon-reload

    # Habilitar o serviço para iniciar no boot
    systemctl enable inicializar.service

    # Iniciar o serviço imediatamente
    systemctl start inicializar.service

    # Mostrar o status do serviço
    systemctl status inicializar.service
}

atualizacoes(){
    echo " "
    echo "Escolha a opção para atualização do sistema:"
    options=("Atualização completa sem reinicialização" "Atualização completa com reinicialização" "Atualização mínima sem reinicialização" "Voltar ao menu principal")
    select opt in "${options[@]}";
    do
        case $opt in
            "Atualização completa sem reinicialização")
                echo "Atualizando o sistema..."
                sudo apt update && sudo apt upgrade -y
                echo "Sistema atualizado sem reinicializar."
                break
                ;;
            "Atualização completa com reinicialização")
                echo "Atualizando o sistema..."
                sudo apt update && sudo apt upgrade -y
                echo "O sistema será reiniciado para concluir as atualizações."
                sudo reboot
                break
                ;;
            "Atualização mínima sem reinicialização")
                echo "Realizando atualização mínima..."
                sudo apt update && sudo apt upgrade --with-new-pkgs -y
                echo "Atualização mínima concluída."
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done
}

instala_pritunel_cliente(){
    # Atualizar o sistema
    echo "Atualizando o sistema..."
    sudo apt update
    sudo apt upgrade -y

    sudo tee /etc/apt/sources.list.d/pritunl.list << EOF
deb https://repo.pritunl.com/stable/apt jammy main
EOF

    sudo apt --assume-yes install gnupg
    gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys 7568D9BB55FF9E5287D586017AE645C0CF8E292A
    gpg --armor --export 7568D9BB55FF9E5287D586017AE645C0CF8E292A | sudo tee /etc/apt/trusted.gpg.d/pritunl.asc
    sudo apt update
    sudo apt install pritunl-client -y
}

importa_perfil_pritunel(){
    # Solicitar localização do perfil
    read -p "Digite o caminho para o arquivo de perfil (.tar): " perfil_caminho
    
    echo "Realizando checagens Pritunl..."

    # Limpa antigos
    sudo pritunl-client list | awk '/Disconnected/ {print $2}' | xargs -I {} sudo pritunl-client remove {}
    sleep 2

    # adiciona perfil
    sudo pritunl-client add "$perfil_caminho"
    sleep 2

    # pegando ID
    perfil_id=$(sudo pritunl-client list | awk 'NR==4 {print $2}')
    sleep 2

    # Iniciar o perfil
    echo "Conectando ao servidor Pritunl..."
    sudo pritunl-client start "$perfil_id"

    sleep 20
    # Verificar a conexão VPN
    if ip a | grep -q -e 'tun' -e 'tap'; then
        echo "A conexão VPN foi estabelecida com sucesso."
    elif sudo pritunl-client status "$perfil_id" | grep -q 'Connected'; then
        echo "A conexão VPN foi estabelecida com sucesso."
    else
        echo "Falha ao estabelecer a conexão VPN."
    fi

    sudo pritunl-client list

    echo "Configuração concluída!"
}

exclui_conexao_pritunel(){
    read -p "Digite o ID de conexão para excluir: " id_exclusao
    sudo pritunl-client stop $id_exclusao
    sleep 2
    sudo pritunl-client remove $id_exclusao
    sleep 2
    echo "Mostrando conexões."
    sudo pritunl-client list
}

perfil_pritunel(){
    echo "Mostrando conexões."
    sudo pritunl-client list

    echo "Escolha uma opção:"
    options=("Importa perfil pritunel" "Excluir conexão")
    select opt in "${options[@]}";
    do
        case $opt in
            "Importa perfil pritunel")
                importa_perfil_pritunel
                break
                ;;
            "Excluir conexão")
                exclui_conexao_pritunel
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) 
                echo "Opção inválida. Tente novamente."
                ;;
        esac
    done
}

pritunel(){
    echo " "
    echo "Escolha uma opção:"
    options=("Instala pritunel" "Instala cliente pritunel" "Perfil/conexões pritunel")
    select opt in "${options[@]}";
    do
        case $opt in
            "Instala pritunel")
                instala_pritunel
                break
                ;;
            "Instala cliente pritunel")
                instala_pritunel_cliente
                break
                ;;
            "Perfil/conexões pritunel")
                perfil_pritunel
                break
                ;;
            # "Instala cliente openvpn")
            #     instala_openvpn_cliente
            #     break
            #     ;;
            # "importa perfil openvpn")
            #     importa_perfil_openvpn
            #     break
            #     ;;
            "Voltar ao menu principal")
                return
                ;;
            *) 
                echo "Opção inválida. Tente novamente."
                ;;
        esac
    done
}

abre_bash_docker(){
    echo "Containers em execução:"
    docker ps --format "table {{.Names}}\t{{.ID}}\t{{.Image}}\t{{.Status}}"
    # Solicita o nome do container ao usuário
    read -p "Digite o nome ou ID do container: " container_name

    # Verifica se o container existe
    if [ "$(docker ps -q -f name=$container_name)" ]; then
        # Abre uma sessão bash no container
        docker exec -it $container_name bash
    else
        echo "Container não encontrado. Verifique o nome ou ID e tente novamente."
    fi
}

docker_options(){
    echo " "
    PS3='Digite sua opção: '
    options=(
        "Instala docker"
        "Realiza limpeza do docker"
        "Abre bash docker"
        "Cria rede docker"
        "Instala pritunel docker"
        "Instala mongodb docker"
        "Instala postgres docker"
        "Instala postgres docker primario"
        "Instala postgres docker secundario"
        "Ativa postgres docker secundario primario"
        "Instala NodeJS docker"
        "Instala vscode_server docker"
        "Instala Redis docker"
        "Instala openlitespeed"
        "Voltar ao menu principal"
        )
    select opt in "${options[@]}"
    do
        case $opt in
            "Instala openlitespeed")
                instala_openlitespeed
                break
                ;;
            "Cria rede docker")
                cria_rede_docker
                break
                ;;
            "Abre bash docker")
                abre_bash_docker
                break
                ;;
            "Instala docker")
                instala_docker
                break
                ;;
            "Instala mongodb docker")
                instala_mongodb_docker
                break
                ;;
            "Instala vscode_server docker")
                vscode_server
                break
                ;;
            "Instala pritunel docker")
                instala_pritunel_docker
                break
                ;;
            "Instala postgres docker")
                instala_postgres_docker
                break
                ;;
            "Instala postgres docker primario")
                instala_postgres_docker_primario
                break
                ;;
            "Instala postgres docker secundario")
                instala_postgres_docker_secundario
                break
                ;;
            "Ativa postgres docker secundario primario")
                ativa_postgres_docker_secundario_primario
                break
                ;;
            "Realiza limpeza do docker")
                limpa_containers_imagens_docker
                break
                ;;
            "Instala NodeJS docker")
                instala_node_docker
                break
                ;;
            "Instala Redis docker")
                instala_redis_docker
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida";;
        esac
    done
}

teste_velocidade(){
    # Verifica se o speedtest-cli está instalado
    if ! which speedtest > /dev/null; then
        echo "Speedtest não está instalado. Instalando..."
        sudo apt-get update
        sudo apt-get install -y speedtest-cli
    fi

    # Executa o teste de velocidade
    echo "Executando teste de velocidade..."
    speedtest

    # Informa o término do teste
    echo "Teste de velocidade concluído."
}

monitor_rede(){
    # Verificar se vnstat já está instalado
    if ! command -v vnstat &> /dev/null
    then
        echo "vnstat não está instalado. Instalando vnstat..."
        sudo apt-get update
        sudo apt-get install -y vnstat
    else
        echo "vnstat já está instalado."
    fi

    # Verificar se o serviço vnstat está habilitado
    if systemctl is-enabled vnstat &> /dev/null
    then
        echo "O serviço vnstat já está habilitado."
    else
        echo "Habilitando o serviço vnstat..."
        sudo systemctl enable vnstat
    fi

    # Verificar se o serviço vnstat está em execução
    if systemctl is-active vnstat &> /dev/null
    then
        echo "O serviço vnstat já está em execução."
    else
        echo "Iniciando o serviço vnstat..."
        sudo systemctl start vnstat
    fi
    
    # Verificar se há dados suficientes para exibir a visão mensal
    if vnstat --months | grep -q "Not enough data available yet"
    then
        echo "Ainda não há dados suficientes disponíveis para exibir a visão mensal. Por favor, aguarde um tempo para que o vnstat colete os dados necessários."
    else
        # Mostrar visão mensal
        vnstat --months
    fi
}

# Função para verificar o arquivo de swap
function verificar_swap() {
    echo "Verificando o arquivo de swap existente..."
    sudo swapon --show
    free -h
}

# Função para modificar o arquivo de swap existente
function modificar_swap() {
    echo "Digite o tamanho desejado para o arquivo de swap (ex: 4G):"
    read novo_tamanho

    echo "Desativando o swap atual..."
    sudo swapoff /swap.img

    echo "Removendo o arquivo de swap atual..."
    sudo rm /swap.img

    echo "Criando novo arquivo de swap de tamanho $novo_tamanho..."
    sudo fallocate -l $novo_tamanho /swap.img
    sudo chmod 600 /swap.img
    sudo mkswap /swap.img
    sudo swapon /swap.img
    echo " "
    echo "Arquivo de swap modificado e ativado com sucesso."
    echo " "
    verificar_swap
}

menu_swap(){
    echo " "
    echo "Escolha uma opção:"
    echo "1. Verificar arquivo de swap existente"
    echo "2. Criar/Modificar arquivo de swap existente"
    read opcao

    case $opcao in
        1)
            verificar_swap
            ;;
        2)
            modificar_swap
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
}

instala_webmin(){
    curl -o setup-repos.sh https://raw.githubusercontent.com/webmin/webmin/master/setup-repos.sh
    sh setup-repos.sh -y
    apt-get install -y --install-recommends webmin
    echo " "
    echo "IPs possíveis para acesso:"
    hostname -I | tr ' ' '\n'
    echo "Porta de acesso: 10000"
}

instala_cyberpanel(){
    sudo apt update && sudo apt upgrade -y
    sudo su - -c "sh <(curl https://cyberpanel.net/install.sh || wget -O - https://cyberpanel.net/install.sh)"
}

habilitar_ufw(){
    # Habilitar UFW se não estiver habilitado
    if sudo ufw status | grep -q "Status: inactive"; then
        echo "Habilitando o UFW..."
        sudo ufw enable
    fi
}

firewall_configuracao(){

    # Solicitar ao usuário a porta a ser aberta
    read -p "Digite a porta que deseja abrir: " PORT

    # Verificar se a entrada é um número válido
    if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Erro: Porta inválida. Por favor, insira um número."
    exit 1
    fi

    # Verificar se o UFW está instalado
    if ! command -v ufw &> /dev/null; then
        echo "UFW não está instalado. Instalando..."
        sudo apt update
        sudo apt install -y ufw
    fi
    # Abrir a porta especificada com o UFW
    echo "Abrindo a porta $PORT no UFW..."
    sudo ufw allow "$PORT"
    
    # Abrir a porta especificada para tráfego
    echo "Abrindo a porta $PORT no iptables..."
    sudo iptables -A INPUT -p tcp --dport "$PORT" -j ACCEPT
    sudo iptables -A INPUT -p udp --dport "$PORT" -j ACCEPT
    # Salvar as regras do iptables
    echo "Salvando as regras do iptables..."
    if [ ! -d /etc/iptables ]; then
        sudo mkdir -p /etc/iptables
    fi
    sudo sh -c "iptables-save > /etc/iptables/rules.v4"
}

habilitando_ecaminhamentos_portas_tuneis(){
    echo "habilitando ecaminhamentos portas tuneis."
    read -p "Digite o usuario da maquina remota: " VPS_USER
    read -p "Digite o IP da maquina remota: " VPS_IP

    SSH_CONFIG_FILE="/etc/ssh/sshd_config"
    echo "Habilitando encaminhamento de portas no VPS..."
    ssh-keygen -R $VPS_IP
    #ssh $VPS_USER@$VPS_IP "sudo cp $SSH_CONFIG_FILE ${SSH_CONFIG_FILE}.bak && sudo sed -i '/^#GatewayPorts yes/s/^#//; /GatewayPorts no/s/no/yes/; /GatewayPorts yes/!s/$/\\nGatewayPorts yes/' $SSH_CONFIG_FILE && sudo systemctl restart ssh"
    ssh $VPS_USER@$VPS_IP "
        sudo cp $SSH_CONFIG_FILE ${SSH_CONFIG_FILE}.bak && \
        sudo sed -i '/^#GatewayPorts yes/s/^#//; /GatewayPorts no/s/no/yes/; /GatewayPorts yes/! s/\$// ' $SSH_CONFIG_FILE && \
        if ! grep -q '^GatewayPorts yes' $SSH_CONFIG_FILE; then echo 'GatewayPorts yes' | sudo tee -a $SSH_CONFIG_FILE; fi && \
        sudo systemctl restart ssh
    "
    echo "Encaminhamento de portas habilitado."
}

criacao_tuneis(){
    echo "habilitando ecaminhamentos portas tuneis."
    read -p "Digite o usuario da maquina remota: " VPS_USER
    read -p "Digite o IP da maquina remota: " VPS_IP
    read -p "Digite a porta remota: " REMOTE_PORT
    read -p "Digite a porta local: " LOCAL_PORT

    echo "Criando túnel SSH para porta ${LOCAL_PORT}"
    ssh -fN -R $REMOTE_PORT:localhost:$LOCAL_PORT $VPS_USER@$VPS_IP
    echo "Túnel SSH para porta HTTP criado."
}

listar_tuneis(){
    echo "Listando túneis SSH ativos..."
    echo "Enviando..."
    ps aux | grep "[s]sh -fN -R"

    echo "Listando túneis SSH ativos..."
    echo "Recebendo..."
    sudo ss -unlp
    sudo ss -tnlp
}

Tuneis(){
    echo " "
    echo "Escolha uma opção:"
    echo "1. Habilitando encaminhamentos portas tuneis."
    echo "2. Criação dos tuneis."
    echo "3. Listar tuneis ativos."
    read opcao

    case $opcao in
        1)
            habilitando_ecaminhamentos_portas_tuneis
            ;;
        2)
            criacao_tuneis
            ;;
        3)
            listar_tuneis
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
}

teste_stress(){
    # Verifica se o stress-ng está instalado, caso contrário instala
    if ! command -v stress-ng &> /dev/null
    then
        echo "Instalando stress-ng..."
        sudo apt update
        sudo apt install -y stress-ng
    fi

    # Verifica se o htop está instalado, caso contrário instala
    if ! command -v htop &> /dev/null
    then
        echo "Instalando htop..."
        sudo apt install -y htop
    fi

    # Verifica se o lm-sensors está instalado, caso contrário instala
    if ! command -v sensors &> /dev/null
    then
        echo "Instalando lm-sensors..."
        sudo apt install -y lm-sensors
        sudo sensors-detect --auto
    fi

    echo " "
    echo "Escolha uma opção:"
    echo "1. Teste combinado de CPU, memória e disco..."
    echo "2. Teste de Memoria."
    echo "3. Teste de HD/SSD."
    echo "4. Teste de CPU."
    echo "5. Visualiza sensores de temperatura"
    read opcao

    case $opcao in
        1)  
            stress-ng --cpu 2 --vm 1 --vm-bytes 256M --hdd 1 --timeout 60s
            ;;
        2)
            stress-ng --vm 2 --vm-bytes 512M --timeout 60s
            ;;
        3)
            stress-ng --hdd 1 --timeout 60s
            ;;
        4)
            stress-ng --cpu 4 --timeout 60s
            ;;
        5)
            watch -n 2 sensors
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
}

configure_external_app() {
    echo " "
    # Função para adicionar ou modificar a configuração do servidor externo
    echo "Configurando External App..."
    if grep -q "extprocessor.*$EXTERNAL_APP_NAME" "$OPENLITESPEED_CONF"; then
        echo "Servidor Externo já configurado. Atualizando..."
        sed -i "/extprocessor.*$EXTERNAL_APP_NAME/{n;s/address.*/address                 $EXTERNAL_APP_ADDRESS/;}" "$OPENLITESPEED_CONF"
    else
        echo "Adicionando novo Servidor Externo..."
        cat <<EOL >> "$OPENLITESPEED_CONF"
extprocessor $EXTERNAL_APP_NAME {
    type                    proxy
    address                 $EXTERNAL_APP_ADDRESS
    maxConns                100
    pcKeepAliveTimeout      60
    initTimeout             60
    retryTimeout            0
    respBuffer              0
}
EOL
        fi
}

configure_proxy_context() {
    echo "Configurando Contexto de Proxy..."
    if grep -q "context / {" "$DOMAIN_CONF_FILE"; then
        echo "Contexto de Proxy já configurado. Atualizando..."
        sed -i "/context \/ {/,/}/ s/handler.*/handler                 $EXTERNAL_APP_NAME/" "$DOMAIN_CONF_FILE"
    else
        echo "Adicionando novo Contexto de Proxy..."
        cat <<EOL >> "$DOMAIN_CONF_FILE"

context / {
    type                    proxy
    handler                 $EXTERNAL_APP_NAME
    addDefaultCharset       off
}
EOL
    fi
}

configurar_proxy_reverso(){
    # Solicitar o nome do domínio e o IP/porta de redirecionamento
    echo " "
    read -p "Digite o nome do domínio: " NOME_DOMINIO
    read -p "Digite o IP de redirecionamento: " IP
    read -p "Digite a porta de redirecionamento: " PORTA

    # Variáveis
    DOMAIN_CONF_DIR="/usr/local/lsws/conf/vhosts/$NOME_DOMINIO"
    DOMAIN_CONF_FILE="$DOMAIN_CONF_DIR/vhost.conf"
    EXTERNAL_APP_NAME="$NOME_DOMINIO"
    EXTERNAL_APP_ADDRESS="$IP:$PORTA"
    OPENLITESPEED_CONF="/usr/local/lsws/conf/httpd_config.conf"
    
    # Verificar se o diretório de configuração do Virtual Host existe
    if [ -d "$DOMAIN_CONF_DIR" ]; then
        # Verificar se o arquivo de configuração do Virtual Host existe
        if [ -f "$DOMAIN_CONF_FILE" ]; then
            configure_external_app
            configure_proxy_context

            # Reiniciar o OpenLiteSpeed para aplicar as alterações
            echo "Reiniciando OpenLiteSpeed..."
            sudo /usr/local/lsws/bin/lswsctrl restart
            echo "Configuração concluída com sucesso."
        else
            echo "Arquivo de configuração do Virtual Host não encontrado: $DOMAIN_CONF_FILE"
            exit 1
        fi
    else
        echo "Diretório de configuração do Virtual Host não encontrado: $DOMAIN_CONF_DIR"
        exit 1
    fi
}

Github_conf(){
    echo " "
    echo "Atualizando git..."
    sudo apt-get update -y > /dev/null 2>&1
    sudo apt-get install -y git > /dev/null 2>&1
    
    echo " "
    echo "Escolha uma opção:"
    echo "1. Atualizar repositorio atual"
    echo "2. Clonar novo repositorio"
    read opcao

    case $opcao in
        1)
            echo " "
            git pull origin main
            echo "Reiniciando o container..."
            docker restart node_container
            echo "Lembre-se de estar na pasta onde o projeto git encontra-se!"
            echo " "
            ;;
        2)
            echo " "
            echo "--------------------------------------------------------------------------------------"
            echo "Siga esses passos:"
            echo "docker stop node_container"
            echo "sudo rm -rf /install_principal/app/"
            echo "mkdir /install_principal/app/"
            echo "git clone https://token@github.com/mauriciowebme/SISUM.git /install_principal/app/"
            echo "docker start node_container"
            echo "--------------------------------------------------------------------------------------"
            echo " "
            ;;
        *)
            echo "Opção inválida!"
            ;;
    esac
}

padrao_ubuntu(){
    apt update && apt upgrade -y
    sudo apt install -y ubuntu-standard
    sudo apt install -y openssh-server
    sudo apt install -y curl wget net-tools htop nano ufw git
}

vscode_server(){
    echo "Iniciando instalação vscode_server:"
    echo " "
    read -p "Configure uma senha para acessar a interface: " SENHA
    docker rm -f vscode_server
    echo "Escolha a opção de instalação:"
    # Definição do diretório padrão
    DATA_DIR_vscode_server="${DIR_Principal}/vscode_server"
    options=("Local padrão ($DATA_DIR_vscode_server)" "Especificar local manualmente" "Voltar ao menu principal")
    select opt in "${options[@]}"; do
        case $opt in
            "Local padrão ($DATA_DIR_vscode_server)")
                # Diretório já definido
                break
                ;;
            "Especificar local manualmente")
                read -p "Informe o diretório de instalação: " DATA_DIR_vscode_server
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done
    rm -r $DATA_DIR_vscode_server
    mkdir $DATA_DIR_vscode_server
    chmod 777 $DATA_DIR_vscode_server
    docker run -d --name vscode_server --restart always -p 8081:8080 -v "$DATA_DIR_vscode_server:/home/coder" -e PASSWORD="$SENHA" codercom/code-server:latest
    sleep 30
    docker exec -it --user root vscode_server /bin/bash -c "apt-get update && apt-get upgrade -y && apt-get install -y python3 python3-pip nodejs npm lsof"
    docker restart vscode_server
    echo "IPs possíveis para acesso:"
    hostname -I | tr ' ' '\n'
    echo "Porta: 8081"
    echo "Senha: $SENHA"
}

tarefas_cron(){
    echo " "
    # Exibe os comandos já existentes no crontab do usuário (ou informa que não há comandos)
    echo "Comandos atuais no crontab:"
    crontab -l || echo "No crontab for the current user."
    echo " "

    # Pergunta se deseja editar o crontab atual manualmente
    read -p "Você deseja editar o crontab atual manualmente antes de adicionar um novo comando? (s/n): " edit_manual_choice

    if [[ "$edit_manual_choice" == "s" || "$edit_manual_choice" == "S" ]]; then
    crontab -e
    fi

    # Pergunta se deseja continuar ou abortar
    read -p "Você deseja continuar a adicionar um novo comando ao crontab? (s/n): " continue_choice

    if [[ "$continue_choice" != "s" && "$continue_choice" != "S" ]]; then
    echo "Operação abortada pelo usuário."
    exit 0
    fi

    # Exemplos de crontab

    echo " "
    echo "Exemplos de uso do crontab:"
    echo "1. Comando simples a cada minuto:"
    echo "* * * * * echo \"Cron está funcionando\" >> /var/log/meu_cron.log 2>&1"
    echo "2. Desligar o sistema a cada hora no minuto 1:"
    echo "1 * * * * /sbin/poweroff >> /var/log/meu_cron.log 2>&1"
    echo "3. Executar um script a cada 15 minutos:"
    echo "*/15 * * * * /usr/local/bin/meu_script.sh >> /var/log/meu_script.log 2>&1"
    echo " "

    # Solicita os comandos que o usuário deseja adicionar ao cron
    read -p "Digite os comandos que você deseja adicionar ao cron (separados por '&&' se houver mais de um): " user_commands

    # Solicita as configurações de tempo para o cron
    echo "Digite as configurações de tempo para o cron (use '*' para representar qualquer valor):"
    read -p "Minuto (0-59 ou *): " minute
    read -p "Hora (0-23 ou *): " hour
    read -p "Dia do mês (1-31 ou *): " day_of_month
    read -p "Mês (1-12 ou *): " month
    read -p "Dia da semana (0-7, 0 e 7 representam domingo, ou *): " day_of_week
    echo " "

    # Solicita o caminho do arquivo de log
    read -p "Digite o caminho para o arquivo de log (por exemplo, /var/log/meu_cron.log): " log_file
    echo " "

    # Cria o diretório para o arquivo de log, caso não exista
    log_dir=$(dirname "$log_file")
    if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
    echo "Diretório $log_dir criado."
    fi

    # Cria a linha do cron com as configurações fornecidas
    cron_line="$minute $hour $day_of_month $month $day_of_week $user_commands >> $log_file 2>&1"

    # Adiciona a linha ao crontab
    (crontab -l 2>/dev/null; echo "$cron_line") | crontab -

    echo "Comando adicionado ao crontab com sucesso!"
    echo " "

    # Exibe o novo crontab para verificação
    echo "Novo crontab:"
    crontab -l
    echo " "

    # Pergunta se deseja editar o crontab atual ou continuar
    read -p "Você deseja editar o crontab atual ou continuar? (e para editar, c para continuar): " final_edit_choice

    if [[ "$final_edit_choice" == "e" || "$final_edit_choice" == "E" ]]; then
    crontab -e
    else
    echo "Operação concluída."
    fi
}

main_menu(){
    # constantes
    echo " "
    DIR_Principal="/install_principal"
    echo "Opções: "
    PS3='Digite sua opção: '
    options=(
    "Sair"
    "Atualizações"
    "Verificar status do sistema"
    "Testes de stress"
    "Docker"
    "Tarefas Cron"
    "Menu swap"
    "Cria pasta compartilhada"
    "Teste de velocidade"
    "Monitor de rede"
    "Pritunel"
    "Instala serviço no inicializar"
    "Instala CyberPanel"
    "Instala webmin"
    "Verificador de portas"
    "Reseta senha OpenLiteSpeed"
    "Limpeza de sistema"
    "Copiar arquivos"
    "Verifica tamanho da pasta atual"
    "Configuração de firewall"
    "Configurar proxy reverso com Openlitespeed"
    "Github"
    "Tuneis"
    "Intala padrão UBUNTU"
    )
    select opt in "${options[@]}"
    do
        case $opt in
            "Tarefas Cron")
                tarefas_cron
                break
                ;;
            "Intala padrão UBUNTU")
                padrao_ubuntu
                break
                ;;
            "Github")
                Github_conf
                break
                ;;
            "Configurar proxy reverso com Openlitespeed")
                configurar_proxy_reverso
                break
                ;;
            "Tuneis")
                Tuneis
                break
                ;;
            "Configuração de firewall")
                firewall_configuracao
                break
                ;;
            "Verifica tamanho da pasta atual")
                du -ah --max-depth=1 | sort -hr
                break
                ;;
            "Copiar arquivos")
                echo " 
Exemplos:

Copiar um Arquivo do Computador Local para um Servidor Remoto:
scp /caminho/para/o/arquivo usuario@servidor_remoto:/caminho/para/destino

Copiar um Arquivo de um Servidor Remoto para o Computador Local:
scp usuario@servidor_remoto:/caminho/para/o/arquivo /caminho/para/destino

Copiar um Diretório Inteiro Recursivamente:
Para copiar um diretório inteiro e seu conteúdo, use a opção -r:
scp -r /caminho/para/o/diretorio usuario@servidor_remoto:/caminho/para/destino

Especificar uma Porta SSH Diferente:
Se o servidor remoto estiver utilizando uma porta SSH diferente da padrão (22), você pode especificar a porta com a opção -P:
scp -P 2222 /caminho/para/o/arquivo usuario@servidor_remoto:/caminho/para/destino

Exemplo Prático:
Copiar um arquivo chamado relatorio.pdf do diretório local /home/usuario/documentos para o diretório /home/usuario/remotos em um servidor remoto servidor.com com o usuário usuario_remoto:
scp /home/usuario/documentos/relatorio.pdf usuario_remoto@servidor.com:/home/usuario/remotos

                "
                break
                ;;
            "Limpeza de sistema")
                sudo apt update && sudo apt upgrade -y
                sudo apt autoremove
                sudo apt clean
                sudo apt autoclean
                dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge
                sudo journalctl --vacuum-size=100M

                break
                ;;
            "Atualizações")
                atualizacoes
                break
                ;;
            "Verificar status do sistema")
                echo "Verificando status do sistema..."
                echo " "
                ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1
                echo " "
                uptime
                echo " "
                df -h
                echo " "
                break
                ;;
            "Docker")
                docker_options
                break
                ;;
            "Cria pasta compartilhada")
                cria_pasta_compartilhada
                break
                ;;
            "Pritunel")
                pritunel
                break
                ;;
            "Instala serviço no inicializar")
                criar_servico_inicializar
                break
                ;;
            "Teste de velocidade")
                teste_velocidade
                break
                ;;
            "Monitor de rede")
                monitor_rede
                break
                ;;
            "Menu swap")
                menu_swap
                break
                ;;
            "Instala webmin")
                instala_webmin
                break
                ;;
            "Instala CyberPanel")
                instala_cyberpanel
                break
                ;;
            "Verificador de portas")
                read -p "Informe a porta: " PORTA
                sudo netstat -tuln | grep $PORTA
                sudo lsof -i :$PORTA
                break
                ;;
            "Reseta senha OpenLiteSpeed")
                sudo /usr/local/lsws/admin/misc/admpass.sh
                break
                ;;
            "Testes de stress")
                teste_stress
                break
                ;;
            "Sair")
                echo "Saindo..."
                rm -- "$0"
                exit 0
                ;;
            *) echo "Opção inválida";;
        esac
    done
}

# Loop principal para garantir retorno ao menu após ações
while true; do
    main_menu
done

echo " "
echo "Arquivo install_master.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
