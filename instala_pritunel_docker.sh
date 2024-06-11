echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Documentação: https://github.com/jippi/docker-pritunl"
echo " "
echo "Versão 1.13"
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

# Definir o endereço do host MongoDB
MONGODB_URI="mongodb://localhost:27017/pritunl"

# Criar o Dockerfile
cat > ${DATA_DIR}/Dockerfile <<EOF
FROM ubuntu:20.04

# Evita que a instalação faça perguntas
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências necessárias
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common

# Adiciona o repositório do Pritunl
RUN echo "deb http://repo.pritunl.com/stable/apt focal main" > /etc/apt/sources.list.d/pritunl.list && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A

# Instala o Pritunl
RUN apt-get update && \
    apt-get install -y pritunl

# Configura o ponto de entrada
CMD ["/usr/bin/pritunl", "start"]
EOF

# Construir a imagem Docker
cd ${DATA_DIR}/
docker build -t pritunl_custom .

# Executar o contêiner do Docker
docker run -d \
  --name pritunl \
  --network="host" \
  --volume ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf \
  --volume ${DATA_DIR}/pritunl:/var/lib/pritunl \
  --volume ${DATA_DIR}/mongodb:/var/lib/mongodb \
  -e PRITUNL_MONGODB_URI="$MONGODB_URI" \
  pritunl_custom

# Executa o container Docker
# docker run \
#     --name pritunl \
#     --privileged \
#     --publish 80:80 \
#     --publish 443:443 \
#     --publish 1194:1194 \
#     --publish 1194:1194/udp \
#     --dns 127.0.0.1 \
#     --restart=unless-stopped \
#     --detach \
#     --volume ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf \
#     --volume ${DATA_DIR}/pritunl:/var/lib/pritunl \
#     --volume ${DATA_DIR}/mongodb:/var/lib/mongodb \
#     ghcr.io/jippi/docker-pritunl

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
