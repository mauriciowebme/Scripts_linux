#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.sh https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.sh && sudo bash install_master.sh

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo install_master.sh iniciado!"
echo " "
echo "Versão 1.05"
echo " "

echo "Escolha a opção:"
echo "Pressione enter para sair (default)"
echo "1 - Atualização completa sem reinicialização"
echo "2 - Atualização completa com reinicialização"
echo "3 - Atualização mínima sem reinicialização"
echo "4 - Verificar status do sistema"
echo "5 - Instala docker"
read -p "Digite sua opção (1, 2, 3 ou 4): " user_choice
echo " "

case "$user_choice" in
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
