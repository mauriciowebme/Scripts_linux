import os
import shutil
import subprocess
import textwrap

from install_master.core.docker_base import DockerBase


class MixinWebtop(DockerBase):

    def desktop_ubuntu_webtop(self):
        """Instala e executa o Webtop."""
        print("Iniciando instalação webtop:")

        dockerfile = textwrap.dedent("""\
        FROM linuxserver/webtop:ubuntu-xfce

        RUN echo 'Executa como root e evita prompts interativos'
        USER root
        ENV DEBIAN_FRONTEND=noninteractive

        RUN echo 'Atualiza o sistema'
        RUN apt-get update && \
            apt-get upgrade -y
        
        RUN echo 'Instala os pacotes básicos'
        #--no-install-recommends
        RUN apt-get install -y \
            wget \
            curl \
            gdebi \
            python3 \
            python3-pip \
            htop \
            unzip p7zip-full unrar \
            file-roller xarchiver thunar-archive-plugin
            
        RUN echo 'Instala dpendencias do chrome'
        RUN apt-get install -y \
            libxss1 \
            libappindicator3-1 \
            libindicator7 \
            fonts-liberation \
            libatk-bridge2.0-0 \
            libgtk-3-0 \
            xdg-utils \
            libgbm-dev \
            dbus-x11
        
        RUN echo 'Instala o Google Chrome'
        RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
            | gpg --dearmor > /etc/apt/keyrings/google-chrome.gpg && \
            echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] \
            http://dl.google.com/linux/chrome/deb/ stable main" \
            > /etc/apt/sources.list.d/google-chrome.list && \
            apt-get update && \
            apt-get install -y --no-install-recommends google-chrome-stable && \
            apt-get clean && rm -rf /var/lib/apt/lists/*
            
        RUN echo 'Instala atalho Google Chrome'
        RUN echo 'Cria o wrapper sem here-doc'
        RUN mkdir -p /usr/local/bin && \
            echo '#!/bin/bash' > /usr/local/bin/chrome-wrapper.sh && \
            echo 'exec /usr/bin/google-chrome-stable --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage --disable-gpu "$@"' \
            >> /usr/local/bin/chrome-wrapper.sh && \
            chmod +x /usr/local/bin/chrome-wrapper.sh

        RUN echo 'Cria o atalho do Chrome no menu apontando pro wrapper'
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

        RUN apt-mark hold google-chrome-stable
        
        RUN echo 'Habilita universe'
        RUN apt-get update \
            && apt-get install -y --no-install-recommends software-properties-common \
            && add-apt-repository universe \
            && rm -rf /var/lib/apt/lists/*
        
        RUN echo 'Instala suporte a pt_BR e IBus para XFCE'
        RUN apt-get update \
            && apt-get install -y --no-install-recommends \
            locales \
            language-pack-pt-base \
            hunspell-pt-br \
            ibus \
            ibus-gtk \
            ibus-gtk3 

        RUN echo 'Gera e define o locale pt_BR.UTF-8'
        RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
            && locale-gen pt_BR.UTF-8 \
            && update-locale LANG=pt_BR.UTF-8 LANGUAGE=pt_BR:pt LC_ALL=pt_BR.UTF-8

        RUN echo 'Define como default para todo o container'
        ENV LANG=pt_BR.UTF-8 \
            LANGUAGE=pt_BR:pt \
            LC_ALL=pt_BR.UTF-8
            
        RUN echo 'Adiciona ABNT2 ao iniciar o XFCE'
        RUN echo "setxkbmap -layout br -variant abnt2" >> /etc/xdg/xfce4/xinitrc
        
        RUN curl https://rclone.org/install.sh | sudo bash
        
        RUN echo 'Realiza limpeza'
        RUN apt-get clean && rm -rf /var/lib/apt/lists/*
        
        # # volta ao usuário "abc" (ou UID/GID correto)
        # USER abc
        """)
        
        nome = input("Digite um nome para o container: ")
        self.remove_container(f"webtop_{nome}")
        
        senha = ''
        caminho_principal = f"{self.install_principal}/webtop_{nome}"
        # Verificar se o caminho já existe
        if os.path.exists(caminho_principal):
            resposta = input(f"O caminho {caminho_principal} já existe. Deseja apagá-lo? (s/n): ")
            if resposta.lower() == 's':
                print(f"Removendo diretório existente: {caminho_principal}")
                try:
                    os.chmod(caminho_principal, 0o777)
                    shutil.rmtree(caminho_principal)
                    print(f"Diretório {caminho_principal} removido com sucesso.")
                except Exception as e:
                    print(f"Erro ao remover diretório: {e}")
                    return
                senha = input("Configure uma senha para acessar o webtop: ")
            else:
                print("Mantendo diretório existente.")
        else:
            senha = input("Configure uma senha para acessar o webtop: ")
            print(f"Criando novo diretório: {caminho_principal}")
        
        # Criar o diretório para o container
        os.makedirs(caminho_principal, exist_ok=True)
        os.chmod(caminho_principal, 0o777)
        
        porta = self.escolher_porta_disponivel()[0]
        run_args = [
            "--name", f"webtop_{nome}",
            "--restart=unless-stopped",
            "-e", "PUID=1000",
            "-e", "PGID=1000",
            "-e", "TZ=America/Sao_Paulo",
            "-e", "CUSTOM_USER=master",
            "-e", f"PASSWORD={senha}",
            "-p", f"{porta}:3000",
            "--shm-size", f"2g",
            "-v", f"{self.install_principal}/webtop_{nome}/config:/config",
            "-d"
        ]
        
        self.executar_comandos_run_OrAnd_dockerfile(
            dockerfile_str=dockerfile,
            run_cmd=run_args
        )

        print("\nInstalação do Webtop concluída.")
        print(f"Acesse: http://<seu_servidor>:{porta}")
        print("Usuário: master")
        print(f"Senha: {senha}")
