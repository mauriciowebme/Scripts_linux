#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.sh https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.sh && sudo bash install_master.sh

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo install_master.sh iniciado!"
echo " "
echo "Versão 1.10"
echo " "

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
read -p "Digite sua opção: " user_choice
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
    echo "instalando o docker mongo..."
    docker run \
        --name mongodb \
        -d mongo
    ;;
  7)
    echo "instalando pritunel docker..."

    if ! command -v docker &> /dev/null; then
        echo "Docker não está instalado."
        instala_docker
    else
        # Definição do diretório padrão
        DEFAULT_DIR="/pritunl"

        # Solicita ao usuário para escolher entre o local padrão ou um customizado
        echo "Escolha a opção de instalação:"
        echo "1 - Local padrão ($DEFAULT_DIR) (default)"
        echo "2 - Especificar local manualmente"
        read -p "Digite sua opção (1 ou 2): " user_choice

        if [ "$user_choice" = "2" ]; then
            read -p "Informe o diretório de instalação: " DATA_DIR
        else
            DATA_DIR=$DEFAULT_DIR
        fi

        rm -r ${DATA_DIR}

        # Cria a estrutura de diretórios e arquivos necessários
        echo "Instalação: ${DATA_DIR}"
        mkdir -p ${DATA_DIR}/pritunl ${DATA_DIR}/mongodb
        touch ${DATA_DIR}/pritunl.conf

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
            --volume $(data_dir)/pritunl.conf:/etc/pritunl.conf \
            --volume $(data_dir)/pritunl:/var/lib/pritunl \
            --env PRITUNL_MONGODB_URI=mongodb://127.0.0.1:27017/pritunl \
            ghcr.io/jippi/docker-pritunl

        # Espera um pouco para o container iniciar
        sleep 20
        echo " "

        # Redefine a senha do Pritunl
        docker exec pritunl pritunl reset-password
        echo "Possiveis ip para acesso"
        hostname -I | tr ' ' '\n'
    fi
    ;;
  8)
    echo "Instalando postgres docker..."
        
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
        ;;
    *)
        echo "Nada foi execudato!"

    ;;
esac

echo " "
echo "Arquivo install_master.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
