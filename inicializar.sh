#!/bin/bash

# Criar o arquivo de serviço systemd
cat << 'EOF' > /etc/systemd/system/startup-script.service
[Unit]
Description=Executa o script /teste.txt 30 segundos após a inicialização
After=network.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 30
ExecStart=/bin/bash /teste.txt
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Recarregar os serviços do systemd para reconhecer o novo serviço
systemctl daemon-reload

# Habilitar o serviço para iniciar no boot
systemctl enable startup-script.service

# Iniciar o serviço imediatamente
systemctl start startup-script.service

# Mostrar o status do serviço
systemctl status startup-script.service
