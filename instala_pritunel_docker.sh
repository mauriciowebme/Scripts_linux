#!/bin/bash
 
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_pritunel_docker.sh iniciado!"
echo " "
echo "Versão 1.15"
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
  DATA_DIR=$DEFAULT_DATA_DIR
fi

rm -rf ${DATA_DIR}

# Cria a estrutura de diretórios e arquivos necessários
echo "Instalação: ${DATA_DIR}"
mkdir -p ${DATA_DIR}
touch ${DATA_DIR}/pritunl.conf

# Tenta remover o container se existir
docker rm -f pritunl mongodb

# Criar o Dockerfile
cat > ${DATA_DIR}/Dockerfile <<EOF
FROM ubuntu:22.04

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

# Criar o arquivo docker-compose.yml
cat > ${DATA_DIR}/docker-compose.yml <<EOF
version: '3.8'

services:
  pritunl:
    build: .
    image: pritunl_custom
    volumes:
      - ${DATA_DIR}/pritunl.conf:/etc/pritunl.conf
      - ${DATA_DIR}/pritunl:/var/lib/pritunl
      - ${DATA_DIR}/mongodb:/var/lib/mongodb
    ports:
      - "9700:9700"
      - "1194:1194"
      - "1194:1194/udp"
    environment:
      - PRITUNL_MONGODB_URI=mongodb://mongodb:27017/pritunl
    depends_on:
      - mongodb
    restart: unless-stopped

  mongodb:
    image: mongo:latest
    volumes:
      - ${DATA_DIR}/mongodb:/data/db
    restart: unless-stopped

EOF

# Construir e executar containers com Docker Compose
cd ${DATA_DIR}/
docker-compose up -d

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
