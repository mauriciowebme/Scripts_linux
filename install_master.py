#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import subprocess
import tempfile

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.10
===========================================================================
===========================================================================
""")

class Sistema():
    def __init__(self):
        pass
    
    def mostrar_menu(self, opcoes_menu, principal=False):
        """Mostra o menu de opções para o usuário de forma dinâmica."""
        print("\nMenu de Opções:")
        opcoes_menu.insert(0, ("Sair", self.sair))
        while True:
            print('===========================================================================')
            for chave, detalhes in enumerate(opcoes_menu):
                print(f"{chave}. {detalhes[0]}")
            print('===========================================================================')
            escolha = input("\nSelecione uma opção: ")

            if int(escolha) >= 0 and int(escolha) <= (len(opcoes_menu)-1):
                for chave, detalhes in enumerate(opcoes_menu):
                    if escolha == str(chave):
                        detalhes[1]()
                        if principal:
                            break
                        else:
                            return
                        
            else:
                print("\nOpção inválida. Tente novamente.\n")
    
    def testes(self,):
        print('Testes ok.')
        
    def executar_comandos(self, comandos:list=[]):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        # Cria um arquivo temporário para capturar a saída
        for comando in comandos:
            with tempfile.NamedTemporaryFile(mode="w+", delete=True) as temp_file:
                # Envia o comando diretamente para o terminal e redireciona a saída para o arquivo temporário
                processo = subprocess.Popen(comando, shell=True, stdout=temp_file, stderr=temp_file)
                
                # Aguarda o término do comando antes de prosseguir para o próximo
                processo.wait()
                
                # Move o ponteiro para o início do arquivo temporário para leitura
                temp_file.seek(0)
                # Lê a saída completa do comando
                saida_comando = temp_file.read()
    
    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        comandos = [
            "echo 'Verificando status do sistema...'",
            "echo ' '",
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
            "echo ' '",
            "uptime",
            "echo ' '",
            "df -h",
            "echo ' '"
        ]
        self.executar_comandos(comandos)
    
    def menu_atualizacoes(self,):
        """Menu de atualizações."""
        opcoes_menu = [
            ("atualizar_sistema_simples", self.atualizar_sistema_simples),
            ("atualizar_sistema_completa", self.atualizar_sistema_completa),
            ("atualizar_sistema_completa_reiniciar", self.atualizar_sistema_completa_reiniciar),
        ]
        self.mostrar_menu(opcoes_menu)
        
    def atualizar_sistema_simples(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema com update...")
        self.executar_comandos(['sudo apt-get update'])
        
    def atualizar_sistema_completa(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema com upgrade...")
        self.atualizar_sistema_simples()
        self.executar_comandos(['sudo apt-get upgrade -y'])
        
    def atualizar_sistema_completa_reiniciar(self,):
        """Executa o comando para atualizar o sistema."""
        print("Reiniciando o sistema...")
        self.atualizar_sistema_simples()
        self.atualizar_sistema_completa()
        self.executar_comandos(['reboot'])

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()

def main():
    """Função principal que controla o menu."""
    servicos = Sistema()
    opcoes_menu = [
        ("Testes", servicos.testes),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("verificando status do sistema", servicos.verificando_status_sistema),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()