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
echo "Versão 1.99"
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

    sudo docker run --name hello hello-world
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
    sudo docker run \
        -d \
        --name $container_name \
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
    fi
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
        --publish 445:443 \
        --publish 446:446 \
        --publish 1194:1194 \
        --publish 1194:1194/udp \
        --dns 127.0.0.1 \
        --restart=unless-stopped \
        --detach \
        --volume ${DATA_DIR_pritunl}/pritunl.conf:/etc/pritunl.conf \
        --volume ${DATA_DIR_pritunl}/pritunl:/var/lib/pritunl \
        --volume ${DATA_DIR_pritunl}/mongodb:/var/lib/mongodb \
        ghcr.io/jippi/docker-pritunl

    echo "Aguarde enquanto o container é inicializado..."
    sleep 20

    # Configuração inicial pós-instalação
    sudo docker exec pritunl pritunl reset-password
    echo "Instalação concluída. Pritunl está pronto para uso."
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

    # Criar diretório de arquivamento
    ARCHIVE_DIR="${DATA_DIR}/archive"
    mkdir -p ${ARCHIVE_DIR}
    
    # Rodar novo container PostgreSQL com configurações de log
    docker run -d \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_USER=postgres \
    --name postgres2 \
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
    options=("Limpeza apenas de containers" "Limpeza completa" "Voltar ao menu principal")
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

instala_node_docker(){
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
    mkdir -p "${DIR_Principal}/app"

    # Cria o arquivo index.js dentro do diretório app
    cat > ${DIR_Principal}/app/index.js <<EOF
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
      -v $(pwd)/app:/usr/src/app \
      -w /usr/src/app \
      node:latest \
      bash -c "npm init -y && npm install express && node index.js"

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
        sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
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

docker_options(){
    echo " "
    PS3='Digite sua opção: '
    options=("Instala docker" "Instala mongodb docker" "Instala pritunel docker" "Instala postgres docker" "Instala postgres docker primario" "Instala postgres docker secundario" "Ativa postgres docker secundario primario" "Realiza limpeza do docker" "Instala NodeJS docker" "Voltar ao menu principal")
    select opt in "${options[@]}"
    do
        case $opt in
            "Instala docker")
                instala_docker
                break
                ;;
            "Instala mongodb docker")
                instala_mongodb_docker
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
    "Teste de velocidade"
    "Monitor de rede"
    "Docker"
    "Cria pasta compartilhada"
    "Pritunel"
    "Instala serviço no inicializar"
    "Menu swap"
    "Instala CyberPanel"
    "Instala webmin"
    "Verificador de portas"
    "Reseta senha OpenLiteSpeed"
    "Limpeza de sistema"
    )
    select opt in "${options[@]}"
    do
        case $opt in
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
