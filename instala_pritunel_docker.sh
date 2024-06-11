#!/bin/bash

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Documentação: https://github.com/jippi/docker-pritunl"
echo " "
echo "Versão 1.12"
echo " "

# Definição do diretório padrão
DEFAULT_DIR="/pritunl"

# Solicita ao usuário para escolher entre o local padrão ou um customizado
echo "Escolha a opção de instalação:"
echo "1 - Local padrão ($DEFAULT_DIR) (default)"
echo "2 - Especificar local manualmente"
read -p "Digite sua opção (1 ou 2): " user_choice

if [ "$user_choice" = "2" ]; then
  read -p "Informe o diretório de instalação: " DATA_DIR
else
  DATA_DIR=$DEFAULT_DIR
fi

rm -rf ${DATA_DIR}

# Cria a estrutura de diretórios e arquivos necessários
echo "Instalação: ${DATA_DIR}"
mkdir -p ${DATA_DIR}
touch ${DATA_DIR}/pritunl.conf

# Tenta remover o container se existir
docker ps -a | grep 'pritunl' && docker rm -f pritunl
docker ps -a | grep 'mongodb' && docker rm -f mongodb

# Prepara Dockerfile do Pritunl
cat > ${DATA_DIR}/Dockerfile <<EOF
FROM ubuntu:22.04

# Evita que a instalação faça perguntas
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências necessárias
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common

# Adiciona o repositório do Pritunl
RUN echo "deb http://repo.pritunl.com/stable/apt jammy main" > /etc/apt/sources.list.d/pritunl.list && \
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7568D9BB55FF9E5287D586017AE645C0CF8E292A

# Instala o Pritunl
RUN apt-get update && \
    apt-get install -y pritunl

# Configura o ponto de entrada
CMD ["/usr/bin/pritunl", "start"]
EOF

# Construir a imagem Docker para Pritunl
docker build -t pritunl_custom ${DATA_DIR}/

# Iniciar o container MongoDB
docker run -d \
  --name mongodb \
  --volume ${DATA_DIR}/mongodb:/data/db \
  mongo:latest

# Iniciar o container Pritunl
docker run -d \
  --name pritunl \
  --network host \
  --volume ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf \
  --volume ${DATA_DIR}/pritunl:/var/lib/pritunl \
  --volume ${DATA_DIR}/mongodb:/var/lib/mongodb \
  -e PRITUNL_MONGODB_URI="mongodb://localhost:27017/pritunl" \
  pritunl_custom

# Espera um pouco para o container iniciar
sleep 20

# Redefine a senha do Pritunl
docker exec pritunl pritunl reset-password

echo "Possíveis IPs para acesso"
hostname -I | tr ' ' '\n'

echo " "
echo "Arquivo instala_pritunel_docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
