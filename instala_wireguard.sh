#!/bin/bash
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo instala_wireguard.sh iniciado!"
echo " "
echo "Verssão 1.0"
echo " "

# Instalar o WireGuard
sudo apt update
sudo apt install -y wireguard

# Escolha um diretório para guardar as configurações do WireGuard
WG_DIR=/wireguard
mkdir -p ${WG_DIR}

# Gerar chaves privada e pública para o servidor
wg genkey | tee ${WG_DIR}/server_private_key | wg pubkey > ${WG_DIR}/server_public_key

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

# Adicionar configurações para cada cliente
for i in {1..5}
do
  # Gerar chaves para cada cliente (isto é apenas para exemplo; na prática, cada cliente deve gerar suas próprias chaves)
  wg genkey | tee ${WG_DIR}/client${i}_private_key | wg pubkey > ${WG_DIR}/client${i}_public_key

  cat >> ${WG_DIR}/wg0.conf << EOF
[Peer]
# PublicKey do cliente ${i}
PublicKey = $(cat ${WG_DIR}/client${i}_public_key)
AllowedIPs = 10.0.0.$((i+1))/32
EOF
done

# Ativar e iniciar o serviço WireGuard
systemctl enable wg-quick@wg0.service
systemctl start wg-quick@wg0.service


echo " "
echo "Arquivo instala_wireguard.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "