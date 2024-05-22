echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo limpa_containers_imagens_docker.sh iniciado!"
echo " "
echo "Verssão 1.02"
echo " "

docker stop $(docker ps -q)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)

echo " "
echo "Arquivo limpa_containers_imagens_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "