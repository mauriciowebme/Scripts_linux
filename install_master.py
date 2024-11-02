#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py
import subprocess

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.1
===========================================================================
===========================================================================
""")

class Sistema():
    def __init__(self):
        pass
    
    def mostrar_menu(self, opcoes_menu, principal=False):
        """Mostra o menu de opções para o usuário de forma dinâmica."""
        print("\nMenu de Opções:")
        for chave, detalhes in enumerate(opcoes_menu):
            print(f"{chave}. {detalhes[0]}")
        while True:
            escolha = input("\nSelecione uma opção: ")

            for chave, detalhes in enumerate(opcoes_menu):
                if escolha == str(chave):
                    detalhes[1]()
                    if principal:
                        return
            else:
                print("Opção inválida. Tente novamente.")
    
    def testes(sef,):
        print('Testes ok.')
    
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
        print("Atualizando o sistema...")
        result = subprocess.run("sudo apt-get update", shell=True, capture_output=True, text=True)
        print(result.stdout)
        
    def atualizar_sistema_completa(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema...")
        self.atualizar_sistema_simples()
        result = subprocess.run("sudo apt-get upgrade -y", shell=True, capture_output=True, text=True)
        print(result.stdout)
        
    def atualizar_sistema_completa_reiniciar(self,):
        """Executa o comando para atualizar o sistema."""
        print("Atualizando o sistema...")
        self.atualizar_sistema_simples()
        self.atualizar_sistema_completa()
        result = subprocess.run("reboot", shell=True, capture_output=True, text=True)
        print(result.stdout)

    def instalar_pacote(self,):
        """Instala um pacote especificado pelo usuário."""
        pacote = input("Digite o nome do pacote que deseja instalar: ")
        print(f"Instalando o pacote {pacote}...")
        subprocess.run(f"sudo apt-get install -y {pacote}", shell=True)

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()

def main():
    """Função principal que controla o menu."""
    servicos = Sistema()
    opcoes_menu = [
        ("Sair", servicos.sair),
        ("Testes", servicos.testes),
        ("Atualizar o sistema", servicos.menu_atualizacoes),
        ("Instalar um pacote", servicos.instalar_pacote),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()