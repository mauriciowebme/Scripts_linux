import os
import re
import subprocess
import time

from install_master.core.docker_base import DockerBase


class MixinPartitions(DockerBase):

    def formata_cria_particao(self,):
        self.listar_particoes()
        print("O disco sera formatado e montado.")
        disco = input("Digite o nome do disco (ex: sdb) onde deseja criar a partição: ")
        ponto_montagem = input("Digite o local onde deseja montar a partição (ex: /mnt/dados): ")

        print(f"Criando nova partição em /dev/{disco}...")

        comandos = [
            f"sudo umount /dev/{disco}*",
        ]
        resultado = self.executar_comandos(comandos, ignorar_erros=True)

        comandos = [
            f"sudo mkdir -p {ponto_montagem}",
            f"sudo parted -s /dev/{disco} mklabel gpt",
            f"sudo parted -s -a opt /dev/{disco} mkpart primary ext4 0% 100%",
            f"sudo mkfs.ext4 /dev/{disco}1",
            f"sudo mount /dev/{disco}1 {ponto_montagem}",
        ]

        resultado = self.executar_comandos(comandos)

        print(f"Partição criada, formatada e montada com sucesso em {ponto_montagem}.")

        adicionar_fstab = input("Deseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.gerenciar_fstab(dispositivo=f"/dev/{disco}1", ponto_montagem=ponto_montagem)

    def estado_raid(self, tempo_real=True):
        """Exibe o estado atual do RAID e suas configurações."""
        print('Exibindo o estado atual do RAID:')
        if tempo_real:
            comandos = [
                "watch cat /proc/mdstat"
            ]
        else:
            comandos = [
                "cat /proc/mdstat"
            ]
        resultado = self.executar_comandos(comandos, comando_direto=True)

    def formatar_criar_particao_raid(self):
        """Formata um disco e adiciona ao RAID"""
        self.listar_particoes()

        self.estado_raid(tempo_real=False)

        print("Inicializando a formatação e adição de disco ao RAID...")
        print("\n⚠️ O disco será formatado e adicionado ao RAID!")
        disco_input = input("Digite o nome do disco (ex: sdb): ").strip()
        disco = disco_input if disco_input.startswith("/dev/") else f"/dev/{disco_input}"
        raid_device_input = input("Digite o nome do dispositivo RAID (ex: md0): ").strip()
        raid_device = raid_device_input if raid_device_input.startswith("/dev/") else f"/dev/{raid_device_input}"

        boot_mode = self.verificar_boot_mode()
        print(f"\n🖥️ Sistema detectado como: {boot_mode}")

        if not os.path.exists(disco):
            print(f"❌ ERRO: O disco {disco} não foi encontrado!")
            return

        confirm = input(f"⚠️ Tem certeza que deseja apagar TODAS as partições de {disco}? (sim/não): ").strip().lower()
        if confirm != "sim":
            print("❌ Operação cancelada!")
            return

        print(f"\n💾 Atualiza a tabela de partições {disco}...")

        comandos_lipeza = [
            f"sudo umount {disco}*",
            f"sudo mdadm --stop /dev/md127",
            f"sudo mdadm --zero-superblock {disco}",
            f"sudo wipefs -a {disco}",
            f"sudo partprobe {disco}",
            f"sudo partx -u {disco}",
            f"sudo udevadm settle",
        ]
        self.executar_comandos(comandos_lipeza, intervalo=5, ignorar_erros=True)
        self.executar_comandos(comandos_lipeza, intervalo=5, ignorar_erros=True)

        comandos = [
            f"sudo parted -s {disco} mklabel gpt",
            f"sudo partprobe {disco}",
            f"sudo udevadm settle",
        ]
        self.executar_comandos(comandos, intervalo=1)

        comandos = []
        if boot_mode == "BIOS":
            print("\n📝 Criando partições para BIOS (Legacy)")
            comandos += [
                f"sudo parted -s {disco} mkpart bios_grub 1MiB 2MiB",
                f"sudo parted -s {disco} set 1 bios_grub on",
                f"sudo parted -s {disco} mkpart primary 2MiB 100%",
                f"sudo parted -s {disco} set 2 raid on",
            ]

        elif boot_mode == "UEFI":
            print("\n📝 Criando partições para UEFI")
            comandos += [
                f"sudo parted -s {disco} mkpart ESP fat32 1MiB 512MiB",
                f"sudo parted -s {disco} set 1 boot on",
                f"sudo parted -s {disco} mkpart primary 512MiB 100%",
                f"sudo parted -s {disco} set 2 raid on",
            ]
        self.executar_comandos(comandos, intervalo=1)

        print(f"\n🔗 Adicionando {disco}2 ao RAID {raid_device}...")
        comandos = [
            f"sudo mdadm --add {raid_device} {disco}2"
        ]
        self.executar_comandos(comandos, intervalo=5)

        print(f"\n⚙️ Instalando o GRUB em {disco}...")
        if boot_mode == "BIOS":
            comandos = [
                f"sudo grub-install --target=i386-pc --recheck {disco}",
                "sudo update-grub"
            ]
        elif boot_mode == "UEFI":
            comandos = [
                f"sudo grub-install --target=x86_64-efi --efi-directory=/boot/efi --recheck {disco}",
                "sudo update-grub"
            ]
        self.executar_comandos(comandos)

        self.estado_raid(tempo_real=True)

    def gerenciar_raid(self):
        """
        Automatiza a expansão ou redução do RAID com base na escolha do usuário via input.
        """

        print("\n📌 Controle de tamanho do RAID.")

        self.listar_particoes()
        self.estado_raid(tempo_real=False)

        raid_device = "/dev/" + input("\nDigite o dispositivo RAID (ex: md0): ").strip()
        particao = input("Digite o número da partição a ser ajustada (ex: 2): ").strip()
        particao_completa = f"{raid_device}p{particao}"

        print("\n🔹 Escolha uma opção:")
        print("[1] 📈  Aumentar o tamanho do RAID")
        print("[2] 📉️  Diminuir o tamanho do RAID")
        escolha = input("\nDigite 1 para aumentar ou 2 para diminuir: ").strip()

        if escolha == "1":
            acao = "aumentar"
            print("\n📌 Você deseja definir um novo tamanho ou usar o máximo disponível?")
            print("[1] 📏️  Definir um tamanho específico")
            print("[2] 📐️  Usar o tamanho máximo disponível (padrão)")
            escolha_tamanho = input("\nDigite 1 para definir um tamanho ou 2 para usar o máximo: ").strip()

            if escolha_tamanho == "1":
                try:
                    novo_tamanho = int(input("\nDigite o novo tamanho desejado (em GB): ").strip())
                    novo_tamanho = f"{novo_tamanho}G"
                except ValueError:
                    print("❌ ERRO: O tamanho deve ser um número inteiro.")
                    return
            else:
                novo_tamanho = "max"

        elif escolha == "2":
            acao = "diminuir"
            try:
                novo_tamanho = int(input("\nDigite o novo tamanho desejado (em GB): ").strip())
                novo_tamanho = f"{novo_tamanho}G"
            except ValueError:
                print("❌ ERRO: O tamanho deve ser um número inteiro.")
                return
        else:
            print("❌ Opção inválida.")
            return

        print("\n🔍 Obtendo o tamanho atual do RAID...")
        resultado_tamanho = self.executar_comandos([f"sudo mdadm --detail {raid_device}"])
        resultado_tamanho_str = "".join(resultado_tamanho.get(f"sudo mdadm --detail {raid_device}", []))

        match = re.search(r"Array Size\s*:\s*(\d+)", resultado_tamanho_str)
        tamanho_atual = int(match.group(1)) // (1024 ** 2) if match else None

        if not tamanho_atual:
            print("❌ ERRO: Não foi possível determinar o tamanho atual do RAID.")
            return

        print(f"📌 Tamanho atual do RAID: {tamanho_atual} GB")

        if acao == "aumentar" and novo_tamanho != "max":
            if int(novo_tamanho.replace("G", "")) <= tamanho_atual:
                print(f"❌ ERRO: O novo tamanho ({novo_tamanho}) deve ser maior que o tamanho atual ({tamanho_atual} GB).")
                return

        if acao == "diminuir":
            if int(novo_tamanho.replace("G", "")) >= tamanho_atual:
                print(f"❌ ERRO: O novo tamanho ({novo_tamanho}) deve ser **menor** que o tamanho atual ({tamanho_atual} GB).")
                return

        print("\n📌 Expandindo a partição GPT...")
        self.executar_comandos([f"sudo parted --script {raid_device} print fix"], comando_direto=True)
        self.executar_comandos([f"sudo parted --script {raid_device} resizepart {particao} {'100%' if novo_tamanho == 'max' else novo_tamanho}"], comando_direto=True)

        print("\n🔍 Verificando o sistema de arquivos...")
        resultado = self.executar_comandos([f"sudo blkid {particao_completa}"])
        resultado_str = "".join(resultado.get(f"sudo blkid {particao_completa}", []))
        tipo_fs = re.search(r'TYPE="(\w+)"', resultado_str)
        tipo_fs = tipo_fs.group(1) if tipo_fs else None

        if not tipo_fs:
            print(f"❌ ERRO: Não foi possível determinar o tipo de sistema de arquivos. Saída:\n{resultado_str}")
            return

        print(f"\n📌 Sistema de arquivos detectado: {tipo_fs}")

        if tipo_fs == "ext4":
            fs_comando = f"sudo resize2fs {particao_completa}"
        elif tipo_fs == "xfs":
            fs_comando = f"sudo xfs_growfs /"
        else:
            print(f"❌ Sistema de arquivos desconhecido: {tipo_fs}. Operação cancelada.")
            return

        print("\n📌 Expandindo o sistema de arquivos...")
        if not self.executar_comandos([fs_comando]):
            print("❌ Falha ao expandir o sistema de arquivos. Abortando!")
            return

        print(f"\n✅ Operação de {'expansão' if acao == 'aumentar' else 'redução'} do RAID concluída com sucesso!")

    def menu_raid(self):
        """Menu de opções"""
        opcoes_menu = [
            ("📊  Exibe o estado atual da raid", self.estado_raid),
            ("💾  Formata o disco para usar em raid existente", self.formatar_criar_particao_raid),
            ("📐  Controle de tamanho do raid", self.gerenciar_raid)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="💾 GERENCIAMENTO DE RAID", itens_por_pagina=10)

    def monta_particao(self,):
        self.listar_particoes()
        particao = input('\nDigite a partição que deseja monta (sda1): ')
        print('\nO ponto de montagem sera criado com 777 caso não exista!')
        ponto_montagem = input('Digite o ponto de montagem (/mnt/dados): ')
        self.gerenciar_permissoes_pasta(ponto_montagem, '777')
        comandos = [
            f"sudo mount /dev/{particao} {ponto_montagem}",
        ]
        resultado = self.executar_comandos(comandos)
        self.listar_particoes()
        adicionar_fstab = input("\nDeseja adicionar essa partição ao /etc/fstab para montagem automática? (s/n): ")
        if adicionar_fstab.lower() == "s":
            self.gerenciar_fstab(dispositivo=f"/dev/{particao}", ponto_montagem=ponto_montagem)

    def desmontar_particao(self,):
        self.listar_particoes()
        ponto_montagem = input('Digite o ponto de montagem para desmontar (/mnt/dados): ')
        comandos = [
            f"sudo umount /mnt/sdc1",
        ]
        resultado = self.executar_comandos(comandos)
        self.listar_particoes()

        self.gerenciar_fstab(ponto_montagem=ponto_montagem, acao='desmontar')

    def menu_particoes(self):
        """Menu de opções"""
        opcoes_menu = [
            (" Menu RAID", self.menu_raid),
            ("📋  Listar particoes", self.listar_particoes),
            ("📄  Listar particoes detalhadas", self.listar_particoes_detalhadas),
            ("💾  Monta particao", self.monta_particao),
            ("💾  Desmontar particao", self.desmontar_particao),
            ("💾  Formata o disco e cria partição e monta", self.formata_cria_particao)
        ]
        self.mostrar_menu_paginado(opcoes_menu, titulo="💿 GERENCIAMENTO DE PARTIÇÕES", itens_por_pagina=10)

    def ver_uso_espaco_pasta(self):
        pasta = input('Digite o caminho absoluto da pasta que deseja ver o tamanho: ')
        if not pasta.startswith('/'):
            pasta = '/' + pasta

        if not os.path.exists(pasta):
            print(f"O caminho '{pasta}' não existe.")
            return

        comandos = [
            f"du -h --max-depth=1 {pasta} | sort -hr",
            ]
        resultados = self.executar_comandos(comandos)
