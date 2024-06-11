echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo atualizador.sh iniciado!"
echo " "
echo "Verssão 1.03"
echo " "

echo "Escolha a opção de limpeza:"
echo "1 - Atualização completa sem reinicialização"
echo "2 - Atualização completa com reinicialização"
read -p "Digite sua opção (1 ou 2): " user_choice

if [ "$user_choice" = "2" ]; then
  apt update
  apt upgrade -y
  reboot
else
  apt update
  apt upgrade -y
fi

echo " "
echo "Arquivo atualizador.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "