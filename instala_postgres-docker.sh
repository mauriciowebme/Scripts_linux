echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_postgres-docker.sh iniciado!"
echo " "
echo "Verssão 1.02"
echo " "

docker run -d \
  -e POSTGRES_PASSWORD=postgres\
  -e POSTGRES_USER=postgres\
  --name postgres \
  -p 5432:5432\
  -v /mnt/cephfs/postgres:/var/lib/postgresql/data \
  -m 512M \
  postgres 

echo " "
echo "Arquivo instala_postgres-docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "