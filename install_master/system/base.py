import subprocess

from install_master.core.docker_base import DockerBase


class MixinBase(DockerBase):

    def Reiniciar(self):
        comandos = [
            f"sudo reboot"
        ]
        self.executar_comandos(comandos, comando_direto=True)

    def Desligar(self):
        comandos = [
            f"sudo poweroff"
        ]
        self.executar_comandos(comandos, comando_direto=True)

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

    def mostrar_menu_paginado(self, opcoes_menu, titulo="Menu de Opções", itens_por_pagina=15, principal=False, mensagem_topo=None):
        """Mostra menu com paginação, busca e navegação melhorada."""
        opcoes_menu.insert(0, ("Sair", self.sair))

        pagina_atual = 0
        filtro = ""

        while True:
            print("\033[2J\033[H", end='')

            if filtro:
                opcoes_filtradas = [
                    (idx, opcao) for idx, opcao in enumerate(opcoes_menu)
                    if filtro.lower() in opcao[0].lower()
                ]
            else:
                opcoes_filtradas = list(enumerate(opcoes_menu))

            total_opcoes = len(opcoes_filtradas)
            total_paginas = (total_opcoes + itens_por_pagina - 1) // itens_por_pagina

            if pagina_atual >= total_paginas:
                pagina_atual = max(0, total_paginas - 1)

            inicio = pagina_atual * itens_por_pagina
            fim = min(inicio + itens_por_pagina, total_opcoes)
            opcoes_pagina = opcoes_filtradas[inicio:fim]

            print("\033[1;36m" + "="*80 + "\033[0m")
            print(f"\033[1;37m  {titulo}\033[0m")

            if mensagem_topo:
                print("\033[1;36m" + "-"*80 + "\033[0m")
                for linha in mensagem_topo.strip().split('\n'):
                    print(f"\033[0;97m  {linha}\033[0m")
                print("\033[1;36m" + "-"*80 + "\033[0m")

            if filtro:
                print(f"\033[33m  🔍 Filtro: '{filtro}' | {total_opcoes} resultado(s)\033[0m")
            print(f"\033[90m  📄 Página {pagina_atual + 1}/{total_paginas} | Exibindo {inicio + 1}-{fim} de {total_opcoes}\033[0m")
            print("\033[1;36m" + "="*80 + "\033[0m")

            for idx_original, (texto, funcao) in opcoes_pagina:
                if idx_original == 0:
                    print(f"\033[91m  [{idx_original}] {texto}\033[0m")
                else:
                    print(f"\033[92m  [{idx_original}]\033[0m {texto}")

            print("\n" + "\033[2m" + "-"*80 + "\033[0m")
            print("\033[96m  NAVEGAÇÃO:\033[0m [n]ext | [p]rev | [número] para selecionar")
            print("\033[96m  BUSCA:\033[0m /palavra | [c]limpar filtro | [0] Sair")
            print("\033[2m" + "-"*80 + "\033[0m")

            escolha = input("\n\033[1;33m➤ Digite sua escolha:\033[0m ").strip()

            if escolha.lower() == 'n' or escolha.lower() == 'next':
                if pagina_atual < total_paginas - 1:
                    pagina_atual += 1
                else:
                    print("\n\033[93m⚠️  Você já está na última página!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")
                continue

            elif escolha.lower() == 'p' or escolha.lower() == 'prev':
                if pagina_atual > 0:
                    pagina_atual -= 1
                else:
                    print("\n\033[93m⚠️  Você já está na primeira página!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")
                continue

            elif escolha.startswith('/'):
                filtro = escolha[1:].strip()
                pagina_atual = 0
                continue

            elif escolha.lower() == 'c' or escolha.lower() == 'clear':
                filtro = ""
                pagina_atual = 0
                continue

            try:
                escolha_num = int(escolha)

                opcao_selecionada = None
                for idx_original, (texto, funcao) in opcoes_filtradas:
                    if idx_original == escolha_num:
                        opcao_selecionada = (texto, funcao)
                        break

                if opcao_selecionada:
                    print("\033[2J\033[H", end='')
                    print(f"\033[1;32m{'='*80}\033[0m")
                    print(f"\033[1;32m  ✓ Executando: {opcao_selecionada[0]}\033[0m")
                    print(f"\033[1;32m{'='*80}\033[0m\n")
                    opcao_selecionada[1]()

                    if principal:
                        break
                    else:
                        return
                else:
                    print(f"\n\033[91m❌ Opção [{escolha_num}] não encontrada!\033[0m")
                    input("\033[90mPressione Enter para continuar...\033[0m")

            except ValueError:
                print("\n\033[91m❌ Entrada inválida! Use um número, 'n', 'p', '/busca' ou 'c'\033[0m")
                input("\033[90mPressione Enter para continuar...\033[0m")

    def exibe_ip(self,):
        comandos = [
            "ip addr show | grep -vE '(docker|br-)' | grep 'inet ' | awk '{split($2, a, \"/\"); print a[1], $NF}'",
        ]
        resultados = self.executar_comandos(comandos, exibir_executando=False, exibir_resultados=False)
        ip_result = "\n".join(line.strip() for line in resultados[comandos[0]] if "127.0.0.1" not in line)
        # print(ip_result)
        return ip_result

    def sair(self,):
        """Sai do programa."""
        print("Saindo...")
        exit()
