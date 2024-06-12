#!/bin/bash

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo install_master.sh iniciado!"
echo " "
echo "Versão 1.03"
echo " "

echo "Escolha a opção:"
echo "1 - Atualização completa sem reinicialização (default)"
echo "2 - Atualização completa com reinicialização"
echo "3 - Atualização mínima sem reinicialização"
echo "4 - Verificar status do sistema"
read -p "Digite sua opção (1, 2, 3 ou 4): " user_choice

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
  *)
    echo "Realizando atualização completa sem reiniciar..."
    apt update && apt upgrade -y
    ;;
esac

echo " "
echo "Arquivo install_master.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
