echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Docuemntação: https://github.com/jippi/docker-pritunl"
echo " "
echo "Verssão 1.01"
echo " "

DATA_DIR=${pwd}/data

mkdir -p ${DATA_DIR}/pritunl ${DATA_DIR}/mongodb
touch ${DATA_DIR}/pritunl.conf

docker run \
    --name pritunl \
    --privileged \
    --network=host \
    --dns 127.0.0.1 \
    --restart=unless-stopped \
    --detach \
    --volume ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf \
    --volume ${DATA_DIR}/pritunl:/var/lib/pritunl \
    --volume ${DATA_DIR}/mongodb:/var/lib/mongodb \
    ghcr.io/jippi/docker-pritunl

# Esperar um pouco para o container iniciar
sleep 10

docker exec -it pritunl pritunl default-password

echo " "
echo "Arquivo instala_pritunel_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "

