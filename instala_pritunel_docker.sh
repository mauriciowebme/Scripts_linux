echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Documentação: https://github.com/jippi/docker-pritunl"
echo " "
echo "Versão 1.11"
echo " "

# Definição do diretório padrão
DEFAULT_DIR="/pritunl"

# Solicita ao usuário para escolher entre o local padrão ou um customizado
echo "Escolha a opção de instalação:"
echo "1 - Local padrão ($DEFAULT_DIR) (default)cd "
echo "2 - Especificar local manualmente"
read -p "Digite sua opção (1 ou 2): " user_choice

if [ "$user_choice" = "2" ]; then
  read -p "Informe o diretório de instalação: " DATA_DIR
else
  DATA_DIR=$DEFAULT_DIR
fi

rm -r ${DATA_DIR}

# Cria a estrutura de diretórios e arquivos necessários
echo "Instalação: ${DATA_DIR}"
mkdir -p ${DATA_DIR}/pritunl ${DATA_DIR}/mongodb
touch ${DATA_DIR}/pritunl.conf

# Tenta remover o container se existir
docker rm -f pritunl

# Executa o container Docker
docker run \
    --name pritunl \
    --privileged \
    --network=host \
    --network=host \
    --dns 127.0.0.1 \
    --restart=unless-stopped \
    --detach \
    --volume ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf \
    --volume ${DATA_DIR}/pritunl:/var/lib/pritunl \
    --volume ${DATA_DIR}/mongodb:/var/lib/mongodb \
    ghcr.io/jippi/docker-pritunl

# Espera um pouco para o container iniciar
sleep 20
echo " "

# Redefine a senha do Pritunl
docker exec pritunl pritunl reset-password
echo "Possiveis ip para acesso"
hostname -I | tr ' ' '\n'

echo " "
echo "Arquivo instala_pritunel_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
