#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import subprocess
import tempfile

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.17
===========================================================================
===========================================================================
""")


class LVMManager:
    def __init__(self):
        pass

    # Método para executar comandos do sistema e capturar a saída
    def executar_comando(self, comando):
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return resultado.stdout.strip()

    # Método para listar discos disponíveis para uso no LVM
    def listar_dispositivos_disponiveis(self):
        print("Dispositivos disponíveis (discos não LVM):")
        dispositivos = self.executar_comando("lsblk -d -o NAME,SIZE,TYPE | grep 'disk'")
        print(dispositivos)
        print()

    # Método para preparar uma partição ou disco como volume físico (PV)
    def criar_volume_fisico(self):
        self.listar_dispositivos_disponiveis()
        dispositivo = input("Digite o nome do dispositivo que deseja preparar como PV (ex: sdb): ")
        confirmacao = input(f"Você está prestes a preparar /dev/{dispositivo} como volume físico. Deseja continuar? (s/n): ")
        if confirmacao.lower() == "s":
            resultado = self.executar_comando(f"pvcreate /dev/{dispositivo}")
            if resultado == "":
                print(f"Volume físico (PV) /dev/{dispositivo} criado com sucesso.")
            else:
                print(f"Erro ao criar volume físico (PV) em /dev/{dispositivo}.")
        else:
            print("Operação cancelada.")

    # Método para criar um grupo de volume (VG)
    def criar_grupo_de_volume(self):
        self.listar_dispositivos_disponiveis()
        dispositivo = input("Digite o nome do dispositivo que deseja adicionar ao VG (ex: sdb): ")
        vg_name = input("Digite o nome do novo Grupo de Volume (VG): ")
        resultado = self.executar_comando(f"vgcreate {vg_name} /dev/{dispositivo}")
        if resultado == "":
            print(f"Grupo de volume {vg_name} criado com sucesso usando /dev/{dispositivo}.")
        else:
            print(f"Erro ao criar o grupo de volume {vg_name}.")

    # Método para criar um volume lógico (LV)
    def criar_volume_logico(self):
        self.listar_grupos_de_volumes()
        vg_name = input("Digite o nome do Grupo de Volume (VG) onde deseja criar o Volume Lógico: ")
        lv_name = input("Digite o nome do novo Volume Lógico (LV): ")
        lv_size = input("Digite o tamanho do Volume Lógico (ex: 10G): ")
        resultado = self.executar_comando(f"lvcreate -L {lv_size} -n {lv_name} {vg_name}")
        if resultado == "":
            print(f"Volume lógico {lv_name} de tamanho {lv_size} criado com sucesso em {vg_name}.")
        else:
            print(f"Erro ao criar o volume lógico {lv_name}.")

    # Método para listar grupos de volumes (VG)
    def listar_grupos_de_volumes(self):
        print("Grupos de Volumes (VG) disponíveis:")
        vgs = self.executar_comando("vgs --noheadings -o vg_name,vg_size,vg_free")
        print(vgs)
        print()

    # Método para listar volumes lógicos (LV) em um grupo de volume específico
    def listar_volumes_logicos(self, vg_name):
        print(f"Volumes Lógicos (LV) no grupo de volume {vg_name}:")
        lvs = self.executar_comando(f"lvs --noheadings -o lv_name,lv_size,lv_attr,vg_name --select vg_name={vg_name}")
        print(lvs)
        print()

    # Método para exibir o menu e realizar as operações
    def menu(self):
        while True:
            print("\nOpções de Gerenciamento LVM:")
            print("1) Preparar uma partição/disco para LVM (criar PV)")
            print("2) Criar um novo Grupo de Volume (VG)")
            print("3) Criar um Volume Lógico (LV) em um VG existente")
            print("4) Listar Grupos de Volume (VG)")
            print("5) Listar Volumes Lógicos (LV) em um VG")
            print("6) Sair")

            opcao = input("Escolha uma opção: ")

            if opcao == "1":
                self.criar_volume_fisico()
            elif opcao == "2":
                self.criar_grupo_de_volume()
            elif opcao == "3":
                self.criar_volume_logico()
            elif opcao == "4":
                self.listar_grupos_de_volumes()
            elif opcao == "5":
                vg_name = input("Digite o nome do Grupo de Volume (VG) para listar os volumes lógicos: ")
                self.listar_volumes_logicos(vg_name)
            elif opcao == "6":
                print("Saindo do gerenciador de LVM.")
                break
            else:
                print("Opção inválida. Tente novamente.")

class Sistema(LVMManager):
    def __init__(self):
        super().__init__()
    
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
        
        for comando in comandos:
            processo = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )

            # Lê e exibe cada linha da saída conforme é produzida
            resultado = []
            for linha in processo.stdout:
                resultado += [linha]
                print(linha, end="")

            # Espera o processo terminar e captura possíveis erros
            processo.wait()
            if processo.returncode != 0:
                print(f"\nErro ao executar comando: {comando}\n")
                for linha in processo.stderr:
                    print(linha, end="")
            else:
                return resultado
            
    def exibir_menu_completo(self):
        print("Bem-vindo ao Gerenciador LVM Completo")
        self.menu()
    
    def verificando_status_sistema(self,):
        print("Verificando status do sistema...")
        comandos = [
            "echo ' '",
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
            "echo ' '",
            "echo 'Tempo em execução'",
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
        ("Menu LVM", servicos.exibir_menu_completo),
    ]
    servicos.mostrar_menu(opcoes_menu, principal=True)

if __name__ == "__main__":
    main()