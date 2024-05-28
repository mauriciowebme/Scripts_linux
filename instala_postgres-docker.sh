#!/bin/bash

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_postgres-docker.sh iniciado!"
echo " "
echo "Versão 1.04"
echo " "

# Remover container existente se houver
docker rm -f postgres

# Rodar novo container PostgreSQL com configurações de log
docker run -d \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  --name postgres \
  -p 5432:5432 \
  -v /mnt/cephfs/postgres:/var/lib/postgresql/data \
  -m 512M \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  postgres:15.3

# Esperar um pouco para o container iniciar
sleep 10

# Ajustar configuração de logs dentro do container
docker exec postgres bash -c "echo \"log_min_messages = warning\" >> /var/lib/postgresql/data/postgresql.conf"
docker exec postgres bash -c "echo \"log_statement = 'none'\" >> /var/lib/postgresql/data/postgresql.conf"

# Reiniciar o PostgreSQL para aplicar configurações
docker restart postgres

echo " "
echo "Arquivo instala_postgres-docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
