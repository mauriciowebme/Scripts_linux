#!/bin/bash
#Execute com:
#wget --no-cache -O install_master.py https://raw.githubusercontent.com/mauriciowebme/Scripts_linux/main/install_master.py && python3 install_master.py

import subprocess
import tempfile

print("""
===========================================================================
===========================================================================
Arquivo install_master.py iniciado!
Versão 1.27
===========================================================================
===========================================================================
""")

class Sistema():
    def __init__(self):
        pass
    
    def mostrar_menu(self, opcoes_menu, principal=False):
        """Mostra o menu de opções para o usuário de forma dinâmica."""
        opcoes_menu.insert(0, ("Sair", self.sair))
        while True:
            print("\nMenu de Opções:")
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
        comandos = [
            f"echo 'Teste ok!'"
        ]
        resultado = self.executar_comandos(comandos)
        
    def executar_comandos(self, comandos:list=[], ignorar_erros=False):
        # for comando in comandos:
        #     processo = subprocess.Popen(comando, shell=True)
        #     processo.wait()
        resultados = {}
        for comando in comandos:
            print("\n" + "*" * 40)
            print(" " * 5 + "---> Executando comando: <---")
            print(" " * 5 + f"{comando}")
            print("*" * 40 + "\n")
            processo = subprocess.Popen(
                comando, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )

            # Lê e exibe cada linha da saída conforme é produzida
            resultados[comando] = []
            for linha in processo.stdout:
                resultados[comando] += [linha]
                print(linha, end="")

            # Espera o processo terminar e captura possíveis erros
            processo.wait()
            if processo.returncode != 0:
                print(f"\nErro ao executar comando: {comando}\n")
                for linha in processo.stderr:
                    print(linha, end="")
                if not ignorar_erros:
                    print("Saindo...")
                    exit()
                    
        return resultados
    
    def adicionar_ao_fstab(self, dispositivo, ponto_montagem):
        try:
            # Verifica se o dispositivo ou ponto de montagem já está no /etc/fstab
            with open("/etc/fstab", "r") as fstab:
                conteudo_fstab = fstab.read()
                if dispositivo in conteudo_fstab or ponto_montagem in conteudo_fstab:
                    print(f"A partição {dispositivo} já está presente no /etc/fstab.")
                    return
            
            # Se não estiver, adiciona ao /etc/fstab
            linha_fstab = f"{dispositivo} {ponto_montagem} ext4 defaults 0 0\n"
            with open("/etc/fstab", "a") as fstab:
                fstab.write(linha_fstab)
            print(f"Partição {dispositivo} adicionada ao /etc/fstab para montagem automática em {ponto_montagem}.")
        except PermissionError:
            print("Erro: Permissões insuficientes para modificar /etc/fstab. Execute o script com sudo.")
    
    def cria_particao(self,):
        # Solicita o nome do disco ao usuário
        disco = input("Digite o nome do disco (ex: sdb) onde deseja criar a partição: ")
        ponto_montagem = input("Digite o local onde deseja montar a partição (ex: /mnt/dados): ")
        
        print(f"Criando nova partição em /dev/{disco}...")
        
        # Tenta desmonatr as partições existentes no disco
        comandos = [
            f"sudo umount /dev/{disco}*",
        ]
        # Executa os comandos
        resultado = self.executar_comandos(comandos, ignorar_erros=True)
        
        comandos = [
            f"sudo mkdir -p {ponto_montagem}",
            f"sudo parted -s /dev/{disco} mklabel gpt",                              # Define o tipo de tabela de partição como GPT
            f"sudo parted -s -a opt /dev/{disco} mkpart primary ext4 0% 100%",       # Cria a partição ocupando todo o disco
            f"sudo mkfs.ext4 /dev/{disco}1"                                       # Formata a nova partição como ext4
        ]
        
        # Executa os comandos
        resultado = self.executar_comandos(comandos)
        
        print(f"Partição criada, formatada e montada com sucesso em {ponto_montagem}.")
            
        # Opcional: Adicionar ao /etc/fstab para montagem automática
        adicionar_fstab = input("Deseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.adicionar_ao_fstab(f"/dev/{disco}1", ponto_montagem)
    
    def exibir_menu_completo(self):
        print("\nBem-vindo ao Gerenciador LVM\n")
        print("Listando discos disponiveis:")
        comandos = [
            "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep -E 'disk|part|lvm'",
        ]
        resultado = self.executar_comandos(comandos)
        
        """Menu de opções"""
        opcoes_menu = [
            ("cria_particao", self.cria_particao),
        ]
        self.mostrar_menu(opcoes_menu)
    
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
        """Menu de opções"""
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