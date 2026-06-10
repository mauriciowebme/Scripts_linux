import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinUpdates(DockerBase):

    def menu_atualizacoes(self,):
        """Menu de atualizações do sistema"""
        opcoes_menu = [
            ("🔄  Atualizar Lista de Pacotes (apt update)", self.atualizar_sistema_simples),
            ("⬆️ Atualização Rápida (update + upgrade)", self.atualizar_sistema_rapida),
            ("🚀  Atualização Completa (update + upgrade + full-upgrade + limpeza)", self.atualizar_sistema_completa),
            ("🔁  Atualização Completa + Reiniciar", self.atualizar_sistema_completa_reiniciar),
            ("🧹  Limpeza de Pacotes (autoremove + autoclean)", self.limpar_pacotes)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="🔄 ATUALIZAÇÕES DO SISTEMA", itens_por_pagina=10)

    def atualizar_sistema_simples(self,):
        """Atualiza apenas a lista de pacotes disponíveis."""
        print("\n📦 Atualizando lista de pacotes...")
        self.executar_comandos(['sudo apt update'], comando_direto=True)
        print("\n✅ Lista de pacotes atualizada!")

    def atualizar_sistema_rapida(self,):
        """Atualização rápida: update + upgrade."""
        print("\n⬆️ Iniciando atualização rápida...")
        self.executar_comandos(['sudo apt update'], comando_direto=True)
        self.executar_comandos(['sudo apt upgrade -y'], comando_direto=True)
        print("\n✅ Atualização rápida concluída!")

    def atualizar_sistema_completa(self,):
        """Atualização completa: update + upgrade + full-upgrade + limpeza."""
        print("\n🚀 Iniciando atualização completa do sistema...")
        print("\n📦 [1/5] Atualizando lista de pacotes...")
        self.executar_comandos(['sudo apt update'], comando_direto=True)
        print("\n⬆️ [2/5] Atualizando pacotes (upgrade)...")
        self.executar_comandos(['sudo apt upgrade -y'], comando_direto=True)
        print("\n🔄 [3/5] Atualizando pacotes com dependências (full-upgrade)...")
        self.executar_comandos(['sudo apt full-upgrade -y'], comando_direto=True)
        print("\n🗑️ [4/5] Removendo pacotes órfãos (autoremove)...")
        self.executar_comandos(['sudo apt autoremove -y'], comando_direto=True)
        print("\n🧹 [5/5] Limpando cache de pacotes (autoclean)...")
        self.executar_comandos(['sudo apt autoclean'], comando_direto=True)
        print("\n✅ Atualização completa finalizada!")

    def atualizar_sistema_completa_reiniciar(self,):
        """Atualização completa + reinicialização do sistema."""
        self.atualizar_sistema_completa()
        print("\n🔁 Reiniciando o sistema em 5 segundos...")
        time.sleep(5)
        self.executar_comandos(['sudo reboot'], comando_direto=True)

    def limpar_pacotes(self,):
        """Remove pacotes órfãos e limpa cache."""
        print("\n🧹 Iniciando limpeza de pacotes...")
        print("\n🗑️ [1/2] Removendo pacotes órfãos...")
        self.executar_comandos(['sudo apt autoremove -y'], comando_direto=True)
        print("\n🧹 [2/2] Limpando cache de pacotes...")
        self.executar_comandos(['sudo apt autoclean'], comando_direto=True)
        print("\n✅ Limpeza concluída!")
