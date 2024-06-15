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
echo "Versão 1.43"
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

instala_mongdb_docker(){
    echo "Instalando o MongoDB Docker..."
    container_name="mongodb"
    if [ $(docker ps -q -f name=^/${container_name}$) ]; then
        echo "O container $container_name já está em execução."
    else
        DATA_DIR_MONGODB="/mongodb"

        echo "Escolha a opção de instalação:"
        echo "1 - Local padrão ($DATA_DIR_MONGODB) (default)"
        echo "2 - Especificar local manualmente"
        read -p "Digite sua opção (1 ou 2): " user_choice

        if [ "$user_choice" = "2" ]; then
            read -p "Informe o diretório de instalação: " DATA_DIR_MONGODB
        fi

        # Cria a estrutura de diretórios e arquivos necessários
        echo "Instalação: ${DATA_DIR_MONGODB}"
        mkdir -p ${DATA_DIR_MONGODB}
        chmod 777 ${DATA_DIR_MONGODB}  # Considere usar permissões mais restritivas

        # Cria e inicia o container MongoDB
        docker run \
            -d \
            --name mongodb \
            -p 27017:27017 \
            --network rede_docker \
            -v ${DATA_DIR_MONGODB}:/data/db \
            mongo:latest
    fi
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
    echo "instalando pritunel docker..."

    # Documentação
    # https://github.com/jippi/docker-pritunl

    # Definição do diretório padrão
    DATA_DIR_pritunl="/pritunl"
    # Solicita ao usuário para escolher entre o local padrão ou um customizado
    echo "Escolha a opção de instalação:"
    echo "1 - Local padrão ($DATA_DIR_pritunl) (default)"
    echo "2 - Especificar local manualmente"
    read -p "Digite sua opção (1 ou 2): " user_choice
    if [ "$user_choice" = "2" ]; then
        read -p "Informe o diretório de instalação: " DATA_DIR_pritunl
    fi

    verifica_instalacao_docker

    # instala_mongdb_docker
    
    rm -r ${DATA_DIR_pritunl}
    # Cria a estrutura de diretórios e arquivos necessários
    echo "Instalação: ${DATA_DIR_pritunl}"
    mkdir -p ${DATA_DIR_pritunl}/pritunl ${DATA_DIR_pritunl}/mongodb
    touch ${DATA_DIR_pritunl}/pritunl.conf
    # Tenta remover o container se existir
    docker rm -f pritunl
    # Executa o container Docker
    #--dns 127.0.0.1 \
    docker run \
        --name pritunl \
        --privileged \
        --publish 80:80 \
        --publish 443:443 \
        --publish 27017:27017 \
        --publish 1194:1194 \
        --publish 1194:1194/udp \
        --restart=unless-stopped \
        --detach \
        --volume ${DATA_DIR_pritunl}/pritunl.conf:/etc/pritunl.conf \
        --volume ${DATA_DIR_pritunl}/pritunl:/var/lib/pritunl \
        --volume ${DATA_DIR_pritunl}/mongodb:/var/lib/mongodb \
        ghcr.io/jippi/docker-pritunl
    # Espera um pouco para o container iniciar
    sleep 20
    # docker exec -it pritunl bash -c "apt update && apt install nano -y"
    echo " "
    # Redefine a senha do Pritunl
    docker exec pritunl pritunl reset-password
    echo "Possiveis ip para acesso"
    hostname -I | tr ' ' '\n'
    echo " "
    echo "Acesse o container com:"
    echo "docker exec -it pritunl /bin/bash"

}

instala_postgres_docker(){
    echo "Instalando postgres docker..."

    verifica_instalacao_docker
        
    # Remover container existente se houver
    docker rm -f postgres

    # Rodar novo container PostgreSQL com configurações de log
    docker run -d \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_USER=postgres \
    --name postgres \
    -p 5432:5432 \
    -v /mnt/cephfs/postgres:/var/lib/postgresql/data \
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

cria_pasta_compartilhada(){
    echo "Criando pasta compartilhada..."
    
    # Atualiza os repositórios e instala o Samba
    sudo apt-get update
    sudo apt-get install samba -y

    # Cria uma pasta compartilhada
    sudo mkdir -p /compartilhado
    sudo chmod 777 /compartilhado

    # Adiciona configuração ao smb.conf
    echo "
    [Compartilhado]
        comment = Pasta Compartilhada
        path = /compartilhado
        browsable = yes
        guest ok = yes
        read only = no
    " | sudo tee -a /etc/samba/smb.conf

    # Reinicia o serviço Samba para aplicar as configurações
    sudo systemctl restart smbd
}

limpa_containers_imagens_docker(){
    verifica_instalacao_docker
    echo "Escolha a opção de limpeza:"
    echo "1 - Limpeza apenas de containers (default)"
    echo "2 - Limpeza completa"
    read -p "Digite sua opção (1 ou 2): " user_choice
    echo " "
    echo "Iniciando limpeza..."
    echo " "

    if [ "$user_choice" = "2" ]; then
        docker stop $(docker ps -q)
        docker rm $(docker ps -aq)
        docker rmi $(docker images -q)
    else
        docker stop $(docker ps -q)
        docker rm $(docker ps -aq)
    fi
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
    # Nome do container
    CONTAINER_NAME=node_container

    # Cria o diretório app se não existir
    mkdir -p $(pwd)/app

    # Cria o arquivo index.js dentro do diretório app
    cat > $(pwd)/app/index.js <<EOF
    const express = require('express');
    const app = express();
    const port = 3000;

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
      -p 3000:3000 \
      -v $(pwd)/app:/usr/src/app \
      -w /usr/src/app \
      node:latest \
      bash -c "npm init -y && npm install express && node index.js"

    # Esperar um pouco para o container iniciar
    sleep 10
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

atualizações(){
    echo "Escolha a opção:"
    echo "Pressione enter para sair (default)"
    echo " "
    echo "1 - Atualização completa sem reinicialização"
    echo "2 - Atualização completa com reinicialização"
    echo "3 - Atualização mínima sem reinicialização"
    echo " "
    read -p "Digite sua opção: " user_choice
    echo " "
    case "$user_choice" in
      1)
        echo "Atualizando o sistema..."
        apt update && apt upgrade -y
        ;;
      2)
        echo "Atualizando e reiniciando o sistema..."
        apt update && apt upgrade -y
        reboot
        ;;
      3)
        echo "Realizando atualização mínima..."
        apt update && apt upgrade --with-new-pkgs -y
        ;;
      *)
        echo "Nada executado!"
        ;;
    esac
}

docker(){
    echo "Escolha a opção:"
    echo "Pressione enter para sair (default)"
    echo " "
    echo "1 - Instala docker"
    echo "2 - Instala mongodb docker"
    echo "3 - Instala pritunel docker"
    echo "4 - Instala postgres docker"
    echo "5 - Realiza limpezar do docker"
    echo "6 - Instala NodeJS docker"
    echo " "
    read -p "Digite sua opção: " user_choice
    echo " "
    case "$user_choice" in
      1)
        instala_docker
        ;;
      2)
        instala_mongdb_docker
        ;;
      3)
        instala_pritunel_docker
        ;;
      4)
        instala_postgres_docker
        ;;
      5)
        limpa_containers_imagens_docker
        ;;
      6)
        instala_node_docker
        ;;
      *)
        echo "Nada executado!"
        ;;
    esac
}

echo "Escolha a opção:"
echo "Pressione enter para sair (default)"
echo " "
echo "1 - Atualizações"
echo "2 - Verificar status do sistema"
echo "3 - Docker"
echo "4 - Cria pasta compartilhada"
echo "5 - Instala pritunel normal"
echo "6 - Instala serviço no inicializar"
echo " "
read -p "Digite sua opção: " user_choice
echo " "

case "$user_choice" in
  1)
    atualizações
    ;;
  2)
    echo "Verificando status do sistema..."
    echo "Uptime do sistema:"
    uptime
    echo "Espaço em disco:"
    df -h
    ;;
  3)
    docker
    ;;
  4)
    cria_pasta_compartilhada
    ;;
  5)
    instala_pritunel
    ;;
  6)
    criar_servico_inicializar
    ;;
  *)
    echo "Nada executado!"
    ;;
esac

echo " "
echo "Arquivo install_master.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
