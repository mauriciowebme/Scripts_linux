#!/bin/bash
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_wireguard.sh iniciado!"
echo " "
echo "Versão 1.3"
echo " "

# Instalar o WireGuard
sudo apt update 
sudo apt install -y wireguard


# Escolha um diretório para guardar as configurações do WireGuard
WG_DIR=/etc/wireguard
mkdir -p ${WG_DIR}

# Verificar se o diretório foi criado
if [ ! -d "${WG_DIR}" ]; then
    echo "Diretório ${WG_DIR} não pôde ser criado. Abortando..."
    exit 1
fi

# Gerar chaves privada e pública para o servidor
if ! wg genkey | tee ${WG_DIR}/server_private_key | wg pubkey > ${WG_DIR}/server_public_key; then
    echo "Falha ao gerar chaves para o servidor. Abortando..."
    exit 1
fi

# Ajustar permissões
chmod -R og-rwx ${WG_DIR}

# Criar arquivo de configuração do servidor WireGuard
cat > ${WG_DIR}/wg0.conf << EOF
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = $(cat ${WG_DIR}/server_private_key)
SaveConfig = true

EOF

# Ativar e iniciar o serviço WireGuard
if ! systemctl enable wg-quick@wg0.service || ! systemctl start wg-quick@wg0.service; then
    echo "Falha ao iniciar o serviço WireGuard. Abortando..."
    exit 1
fi

echo " "
echo "Arquivo instala_wireguard.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
