echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo atualizador.sh iniciado!"
echo " "
echo "Verssão 1.02"
echo " "

docker stop $(docker ps -q)
docker rm $(docker ps -aq)
docker rmi $(docker images -q)

echo " "
echo "Arquivo atualizador.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "