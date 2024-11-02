#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py
import subprocess

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.0
===========================================================================
===========================================================================
""")

def atualizar_sistema():
    """Executa o comando para atualizar o sistema."""
    print("Atualizando o sistema...")
    result = subprocess.run("sudo apt-get update", shell=True, capture_output=True, text=True)
    print(result.stdout)

def instalar_pacote():
    """Instala um pacote especificado pelo usuário."""
    pacote = input("Digite o nome do pacote que deseja instalar: ")
    print(f"Instalando o pacote {pacote}...")
    subprocess.run(f"sudo apt-get install -y {pacote}", shell=True)

def sair():
    """Sai do programa."""
    print("Saindo...")
    exit()

def mostrar_menu():
    """Mostra o menu de opções para o usuário."""
    print("\nMenu de Opções:")
    print("1. Atualizar o sistema")
    print("2. Instalar um pacote")
    print("3. Sair")

def main():
    """Função principal que controla o menu."""
    while True:
        mostrar_menu()
        escolha = input("Selecione uma opção: ")

        if escolha == "1":
            atualizar_sistema()
        elif escolha == "2":
            instalar_pacote()
        elif escolha == "3":
            sair()
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()