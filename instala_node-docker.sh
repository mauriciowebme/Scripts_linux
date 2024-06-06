#!/bin/bash

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_node-docker.sh iniciado!"
echo " "
echo "Versão 1.3"
echo " "

# Nome do container
CONTAINER_NAME=node_container

# Cria o diretório app se não existir
mkdir -p $(pwd)/app

# Cria o arquivo index.js dentro do diretório app
cat > $(pwd)/app/index.js <<EOF
const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send('Node rodando!');
});

app.listen(port, () => {
  console.log(\`Servidor rodando em http://localhost:\${port}\`);
});
EOF

# Remover container existente se houver
docker rm -f $CONTAINER_NAME

# Rodar novo container Node.js com mapeamento de porta e volume
docker run -d \
  --name $CONTAINER_NAME \
  --restart always \
  -p 3000:3000 \
  -v $(pwd)/app:/usr/src/app \
  -w /usr/src/app \
  node:latest \
  bash -c "npm init -y && npm install express && node index.js"

# Esperar um pouco para o container iniciar
sleep 10

echo " "
echo "Arquivo instala_node-docker.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
