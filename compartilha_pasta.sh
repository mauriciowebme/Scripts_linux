#!/bin/bash

echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
echo "Arquivo compartilha_pasta.sh iniciado!"
echo " "
echo "Versão 1.00"
echo " "

# Atualiza os repositórios e instala o Samba
sudo apt-get update
sudo apt-get install samba -y

# Cria uma pasta compartilhada
sudo mkdir -p /compartilhado
sudo chmod 777 /compartilhado

# Adiciona configuração ao smb.conf
echo "
[Compartilhado]
    comment = Pasta Compartilhada
    path = /compartilhado
    browsable = yes
    guest ok = yes
    read only = no
" | sudo tee -a /etc/samba/smb.conf

# Reinicia o serviço Samba para aplicar as configurações
sudo systemctl restart smbd

echo " "
echo "Arquivo compartilha_pasta.sh terminado com sucesso!"
echo " "
echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
echo " "
