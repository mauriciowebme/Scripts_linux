echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Docuemntação: https://github.com/jippi/docker-pritunl"
echo " "
echo "Verssão 1.00"
echo " "

data_dir=$(pwd)/data

mkdir -p $(data_dir)/pritunl $(data_dir)/mongodb
touch $(data_dir)/pritunl.conf

docker run \
    --name pritunl \
    --privileged \
    --network=host \
    --dns 127.0.0.1 \
    --restart=unless-stopped \
    --detach \
    --volume $(data_dir)/pritunl.conf:/etc/pritunl.conf \
    --volume $(data_dir)/pritunl:/var/lib/pritunl \
    --volume $(data_dir)/mongodb:/var/lib/mongodb \
    ghcr.io/jippi/docker-pritunl

# Esperar um pouco para o container iniciar
sleep 10

docker exec -it pritunl pritunl default-password

echo " "
echo "Arquivo instala_pritunel_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "

