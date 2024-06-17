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
echo "Versão 1.61"
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

    DATA_DIR_MONGODB="/mongodb"
    options=("Local padrão ($DATA =DIR_MONGODB)" "Especificar local manualmente" "Voltar ao menu principal")
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
    echo "Instalando Pritunel via Docker..."
    echo "Escolha a opção de instalação:"

    # Definição do diretório padrão
    DATA_DIR_pritunl="/pritunl"
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
        --network=host \
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

atualizacoes(){
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

instala_openvpn_cliente(){
    # Atualizar o sistema
    echo "Atualizando o sistema..."
    sudo apt update
    sudo apt upgrade -y

    # Instalar o OpenVPN
    echo "Instalando o OpenVPN..."
    sudo apt install openvpn -y
}

importa_perfil_pritunel(){
    # Solicitar localização do perfil
    read -p "Digite o caminho para o arquivo de perfil (.tar): " perfil_caminho

    # Limpa antigos
    sudo pritunl-client list | awk '/Disconnected/ {print $2}' | xargs -I {} sudo pritunl-client remove {}

    # adiciona perfil
    sudo pritunl-client add "$perfil_caminho"

    # pegando ID
    perfil_id=$(sudo pritunl-client list | awk 'NR==4 {print $2}')

    # Iniciar o perfil
    echo "Conectando ao servidor Pritunl..."
    sudo pritunl-client start "$perfil_id"

    # Verificar a conexão (opcional)
    sleep 20
    # Verificar a conexão VPN
    if ip a | grep -E '^[0-9]+: tun'; then
        echo "A conexão VPN foi estabelecida com sucesso."
    else
        echo "Falha ao estabelecer a conexão VPN."
    fi

    sudo pritunl-client list

    echo "Configuração concluída!"
}

importa_perfil_openvpn(){
    # Solicitar localização do perfil
    read -p "Digite o caminho para o arquivo de perfil (.ovpn): " perfil_caminho

#     # Criar uma cópia temporária do perfil
#     perfil_temp="/tmp/temp_perfil.ovpn"
#     cp "$perfil_caminho" "$perfil_temp"

#     # Adicionar configurações de reconexão automática ao perfil temporário
#     echo "Adicionando configurações de reconexão automática ao perfil temporário..."
#     echo "
# # Configurações de reconexão automática
# persist-tun 
# persist-key 
# keepalive 2 10
# " | sudo tee -a "$perfil_temp"

    # Iniciar o OpenVPN com o perfil temporário em segundo plano
    echo "Conectando ao servidor OpenVPN..."
    sudo openvpn --config "$perfil_caminho" --daemon

    echo "Conexão VPN iniciada em segundo plano!"

    # Verificar a conexão (opcional)
    sleep 5
    # Verificar a conexão VPN
    if ip a | grep -E '^[0-9]+: tun'; then
        echo "A conexão VPN foi estabelecida com sucesso."
    else
        echo "Falha ao estabelecer a conexão VPN."
    fi

    echo "Configuração concluída!"
}

pritunel(){
    echo "Escolha uma opção:"
    options=("Instala pritunel" "Instala cliente pritunel" "importa perfil pritunel" "Instala cliente openvpn" "importa perfil openvpn")
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
            "importa perfil pritunel")
                importa_perfil_pritunel
                break
                ;;
            "Instala cliente openvpn")
                instala_openvpn_cliente
                break
                ;;
            "importa perfil openvpn")
                importa_perfil_openvpn
                break
                ;;
            "Voltar ao menu principal")
                return
                ;;
            *) echo "Opção inválida. Tente novamente.";;
        esac
    done
}

docker_options(){
    PS3='Digite sua opção: '
    options=("Instala docker" "Instala mongodb docker" "Instala pritunel docker" "Instala postgres docker" "Realiza limpeza do docker" "Instala NodeJS docker" "Voltar ao menu principal")
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

main_menu(){
    echo " "
    PS3='Digite sua opção: '
    options=("Atualizações" "Verificar status do sistema" "Docker" "Cria pasta compartilhada" "Pritunel" "Instala serviço no inicializar" "Sair")
    select opt in "${options[@]}"
    do
        case $opt in
            "Atualizações")
                atualizacoes
                break
                ;;
            "Verificar status do sistema")
                echo "Verificando status do sistema..."
                uptime
                df -h
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
            "Sair")
                echo "Saindo..."
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
