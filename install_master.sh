#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.sh https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.sh && sudo bash install_master.sh

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo install_master.sh iniciado!"
echo " "
echo "Versão 1.22"
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
}

verifica_instalacao_docker(){
    if ! command -v docker &> /dev/null; then
        echo "Docker não está instalado. Instalando agora..."
        instala_docker
    else
        echo "Docker instalado ok."
    fi
}

instala_mongdb_docker(){
    echo "instalando o docker mongo..."
    DATA_DIR_MONGODB="/mongodb"
    # Solicita ao usuário para escolher entre o local padrão ou um customizado
    echo "Escolha a opção de instalação:"
    echo "1 - Local padrão ($DATA_DIR_MONGODB) (default)"
    echo "2 - Especificar local manualmente"
    read -p "Digite sua opção (1 ou 2): " user_choice
    if [ "$user_choice" = "2" ]; then
        read -p "Informe o diretório de instalação: " DATA_DIR
    fi
    rm -r ${DATA_DIR_MONGODB}
    # Cria a estrutura de diretórios e arquivos necessários
    echo "Instalação: ${DATA_DIR_MONGODB}"
    mkdir -p ${DATA_DIR_MONGODB}
    chmod 777 ${DATA_DIR_MONGODB}
    docker run \
        --name mongodb \
        -d \
        -v ${DATA_DIR_MONGODB}:/data/db \
        -p 27017:27017 \
        mongo:latest
}

instala_pritunel_docker(){
    echo "instalando pritunel docker..."

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

    container_name="mongodb"
    if [ $(docker ps -q -f name=^/${container_name}$) ]; then
        echo "O container $container_name já está em execução."
    else
        echo "O container $container_name não existe ou não está em execução..."
        # Comando para criar e iniciar o container MongoDB
        instala_mongdb_docker
        echo "Container $container_name criado e iniciado com sucesso."
    fi
    
    rm -r ${DATA_DIR_pritunl}
    # Cria a estrutura de diretórios e arquivos necessários
    echo "Instalação: ${DATA_DIR_pritunl}"
    mkdir -p ${DATA_DIR_pritunl}/pritunl ${DATA_DIR_pritunl}/mongodb
    touch ${DATA_DIR_pritunl}/pritunl.conf
    # Tenta remover o container se existir
    docker rm -f pritunl
    # Executa o container Docker
    docker run \
        --name pritunl \
        --privileged \
        --publish 80:80 \
        --publish 443:443 \
        --publish 1194:1194 \
        --publish 1194:1194/udp \
        --dns 127.0.0.1 \
        --restart=unless-stopped \
        --detach \
        --volume ${DATA_DIR_pritunl}/pritunl.conf:/etc/pritunl.conf \
        --volume ${DATA_DIR_pritunl}/pritunl:/var/lib/pritunl \
        --env PRITUNL_MONGODB_URI=mongodb://127.0.0.1:27017/pritunl \
        ghcr.io/jippi/docker-pritunl
    # Espera um pouco para o container iniciar
    sleep 20
    echo " "
    # Redefine a senha do Pritunl
    docker exec pritunl pritunl reset-password
    echo "Possiveis ip para acesso"
    hostname -I | tr ' ' '\n'
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

echo "Escolha a opção:"
echo "Pressione enter para sair (default)"
echo "1 - Atualização completa sem reinicialização"
echo "2 - Atualização completa com reinicialização"
echo "3 - Atualização mínima sem reinicialização"
echo "4 - Verificar status do sistema"
echo "5 - Instala docker"
echo "6 - Instala mongodb docker"
echo "7 - Instala pritunel docker"
echo "8 - Instala postgres docker"
echo "9 - Cria pasta compartilhada"
echo "10 - Realiza limpezar do docker"
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
  4)
    echo "Verificando status do sistema..."
    echo "Uptime do sistema:"
    uptime
    echo "Espaço em disco:"
    df -h
    ;;
  5)
    instala_docker
    ;;
  6)
    instala_mongdb_docker
    ;;
  7)
    instala_pritunel_docker
    ;;
  8)
    instala_postgres_docker
    ;;
  9)
    cria_pasta_compartilhada
    ;;
  10)
    limpa_containers_imagens_docker
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
