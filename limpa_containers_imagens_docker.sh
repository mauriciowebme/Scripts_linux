echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo limpa_containers_imagens_docker.sh iniciado!"
echo " "
echo "Verssão 1.05"
echo " "

echo "Escolha a opção de limpeza:"
echo "1 - Limpeza apenas de containers (default)"
echo "2 - Limpeza completa"
read -p "Digite sua opção (1 ou 2): " user_choice

if [ "$user_choice" = "2" ]; then
  docker stop $(docker ps -q)
  docker rm $(docker ps -aq)
  docker rmi $(docker images -q)
else
  docker stop $(docker ps -q)
  docker rm $(docker ps -aq)
fi

echo " "
echo "Arquivo limpa_containers_imagens_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "