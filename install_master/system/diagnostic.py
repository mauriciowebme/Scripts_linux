import os
import select
import subprocess
import sys
import time

from install_master.core.docker_base import DockerBase


class MixinDiagnostic(DockerBase):

    def submenu_diagnostico(self):
        opcoes = [
            ("🌡️  Verificar Temperatura", self.verifica_temperatura),
            ("🌐  Teste de Velocidade Internet", self.verifica_velocidade),
            ("💾  Ver Uso de Espaço", self.ver_uso_espaco_pasta),
            ("📊  Status do Sistema (Glances)", self.verificando_status_sistema),
            ("↩️  Voltar", None)
        ]
        self.mostrar_menu_paginado(opcoes, titulo="🔍 DIAGNÓSTICO DO SISTEMA", itens_por_pagina=10)

    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        print('\n')

        if not self.verificar_instalacao("glances"):
            comandos = [
                "sudo apt update",
                "sudo apt install glances -y",
            ]
            self.executar_comandos(comandos, comando_direto=True)

        print('Pressione H para ver as opções de ajuda')
        print('Pressione Q para sair')

        print("Para ver o modo web digite 'w' ou 'Outra tecla' para o modo normal. (w / Outra tecla)")
        print("(Aguardando 4 segundos, padrão: terminal)...")

        i, o, e = select.select([sys.stdin], [], [], 4)

        if i:
            resposta = sys.stdin.readline().strip()
        else:
            print("\nTempo esgotado! Iniciando modo terminal...")
            resposta = ""
        if resposta.lower() == "w":
            print("Iniciando o modo web do glances...")
            comandos = [
                "/usr/local/bin/glances -w",
            ]
        else:
            print("Iniciando o modo terminal do glances...")
            comandos = [
                "glances",
            ]
        self.executar_comandos(comandos, comando_direto=True)

    def verifica_temperatura(self):
        if not self.verificar_instalacao("lm-sensors"):
            comandos = [
                "sudo apt update",
                "sudo apt install -y lm-sensors",
                "yes | sudo sensors-detect",
            ]
            self.executar_comandos(comandos)
        self.executar_comandos(["sensors"])

    def verifica_velocidade(self):
        if not self.verificar_instalacao("speedtest"):
            print("Instalando Speedtest oficial...")
            if os.path.exists("/etc/apt/sources.list.d/ookla_speedtest-cli.list"):
                 self.executar_comandos(["sudo rm /etc/apt/sources.list.d/ookla_speedtest-cli.list"], exibir_executando=False, exibir_resultados=False)

            cmds_install = [
                "sudo apt install -y curl",
                "curl -L https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz -o /tmp/speedtest.tgz",
                "tar -xzf /tmp/speedtest.tgz -C /tmp speedtest",
                "sudo mv /tmp/speedtest /usr/bin/speedtest",
                "sudo chmod +x /usr/bin/speedtest",
                "rm -f /tmp/speedtest.tgz"
            ]
            self.executar_comandos(cmds_install, exibir_executando=False)

        self.executar_comandos(["speedtest --accept-license --accept-gdpr"], comando_direto=True)

    def vnstat(self):
        """
        Instala e configura o vnstat, caso ainda não esteja instalado.
        Em seguida, exibe as estatísticas mensais de uso de rede.
        """
        if not self.verificar_instalacao("vnstat"):
            print("Instalando o vnstat...")
            comandos = [
                "sudo apt update",
                "sudo apt install -y vnstat",
                "sudo systemctl enable vnstat",
                "sudo systemctl start vnstat",
            ]
            self.executar_comandos(comandos, comando_direto=True)
            print("vnstat instalado e iniciado com sucesso.")
            print("Aguarde alguns minutos para que o vnstat colete dados de uso de rede.")
        else:
            print("\nExibindo estatísticas mensais de uso de rede:")
            self.executar_comandos(["vnstat -m"], comando_direto=True)
