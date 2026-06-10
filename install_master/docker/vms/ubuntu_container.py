import os
import subprocess
import textwrap

from install_master.core.docker_base import DockerBase


class MixinUbuntuContainer(DockerBase):

    def ubuntu(self):
        """Instala e executa o ubuntu."""
        print("Iniciando instalação ubuntu:")

        nome = "teste"
        senha = "teste"
        # nome = input("Digite um nome para o container: ")
        # senha = input("Configure uma senha para acessar: ")
        
        os.makedirs(f"{self.install_principal}/ubuntu_{nome}", exist_ok=True)
        os.chmod(f"{self.install_principal}/ubuntu_{nome}", 0o777)
        self.remove_container(f"ubuntu_{nome}")
        porta = self.escolher_porta_disponivel()[0]

        dockerfile = textwrap.dedent(f"""\
        FROM ubuntu:22.04

        ENV DEBIAN_FRONTEND=noninteractive
        ENV container=docker

        # instala o servidor
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            openssh-server \
            sudo \
            systemd systemd-sysv dbus \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # Instala os pacotes básicos
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            wget \
            gdebi \
            python3 \
            python3-pip \
            htop \
            unzip p7zip-full unrar \
            xarchiver thunar-archive-plugin \
            && apt-get clean && rm -rf /var/lib/apt/lists/*

        # cria usuário não-root
        ARG USER=master
        ARG UID=1000
        RUN useradd -m -u $UID -s /bin/bash $USER \
            && echo "$USER:{senha}" | chpasswd \
            && usermod -aG sudo $USER \
            && echo "$USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

        # habilita login por chave SSH
        RUN mkdir -p /home/$USER/.ssh && chown $USER:$USER /home/$USER/.ssh

        # prepara o diretório do daemon
        RUN mkdir /var/run/sshd
        
        # habilita o serviço SSH para subir junto com o systemd
        RUN systemctl enable ssh
        EXPOSE 22
        
        # --- GUI ---
        RUN apt-get update && \
            apt-get install -y xfce4 xfce4-goodies xrdp && \
            systemctl enable xrdp \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        EXPOSE 3389
            
        # ----- Instala o chrome -----
        # Instala dpendencias do chrome
        RUN apt-get update && apt-get upgrade -y \
            && apt-get install -y \
            libxss1 \
            libappindicator3-1 \
            libindicator7 \
            fonts-liberation \
            libatk-bridge2.0-0 \
            libgtk-3-0 \
            xdg-utils \
            libgbm-dev \
            dbus-x11 \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # Instala o Google Chrome
        RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
            | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg && \
            echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] \
            http://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list && \
            apt-get update && \
            apt-get install -y --no-install-recommends google-chrome-stable \
            && apt-get clean && rm -rf /var/lib/apt/lists/*
            
        # Instala atalho Google Chrome
        # Cria o wrapper sem here-doc
        RUN mkdir -p /usr/local/bin && \
            echo '#!/bin/bash' > /usr/local/bin/chrome-wrapper.sh && \
            echo 'exec /usr/bin/google-chrome-stable --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu "$@"' \
            >> /usr/local/bin/chrome-wrapper.sh && \
            chmod +x /usr/local/bin/chrome-wrapper.sh

        # Cria o atalho do Chrome no menu apontando pro wrapper
        RUN mkdir -p /usr/share/applications && \
            echo '[Desktop Entry]'                                       > /usr/share/applications/google-chrome.desktop && \
            echo 'Name=Google Chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Comment=Navegador Web'                                >> /usr/share/applications/google-chrome.desktop && \
            echo 'Exec=/usr/local/bin/chrome-wrapper.sh %U'             >> /usr/share/applications/google-chrome.desktop && \
            echo 'Terminal=false'                                       >> /usr/share/applications/google-chrome.desktop && \
            echo 'Type=Application'                                     >> /usr/share/applications/google-chrome.desktop && \
            echo 'Icon=google-chrome'                                   >> /usr/share/applications/google-chrome.desktop && \
            echo 'Categories=Network;WebBrowser'                        >> /usr/share/applications/google-chrome.desktop && \
            echo 'StartupNotify=true'                                   >> /usr/share/applications/google-chrome.desktop && \
            chmod +x /usr/share/applications/google-chrome.desktop
        # ----- termina instalação do chrome -----
        
        VOLUME [ "/sys/fs/cgroup" ]
        
        STOPSIGNAL SIGRTMIN+3
        CMD ["/sbin/init"]
        """)

        run_args = [
            "--name", f"ubuntu_{nome}",
            "-p", "2222:22",
            "-p", "3389:3389",
            "--cgroupns=host",
            "--privileged",
            "-v", "/sys/fs/cgroup:/sys/fs/cgroup:rw",
            "-d"
        ]

        self.executar_comandos_run_OrAnd_dockerfile(
            dockerfile_str=dockerfile,
            run_cmd=run_args
        )

        print("\nInstalação do ubuntu concluída.")
