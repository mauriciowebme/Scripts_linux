import os
import subprocess

from install_master.core.docker_base import DockerBase


class MixinSistemaCISO(DockerBase):

    def instala_sistema_CISO_docker(self,):
        print("Iniciando instalação do container sistema_CISO.")

        nome = input("Digite o nome do container: ")
        nome = nome.replace('.', '_')
        
        caminho_dados = f"{self.install_principal}/sistema_CISO_{nome}/dados"
        caminho_isos = f"{self.install_principal}/sistema_CISO_{nome}/isos"
        os.makedirs(caminho_dados, exist_ok=True)
        os.makedirs(caminho_isos, exist_ok=True)
        os.chmod(caminho_dados, 0o777)
        os.chmod(caminho_isos, 0o777)
        
        if os.path.exists(f"{caminho_isos}/data.img"):
            resposta = input("A imagem data.img já existe. Deseja sobrescrever? (s/n): ")
            if resposta.lower() == 's':
                os.remove(f"{caminho_isos}/data.img")
            else:
                print("Instalação cancelada.")
                return

        while True:
            if os.path.exists(f"{caminho_isos}/image.iso"):
                break
            else:
                print(f"Coloque a imagem ISO do sistema na pasta {caminho_isos} e pressione ENTER para continuar.")
                input()
                if os.path.exists(f"{caminho_isos}/image.iso"):
                    break
                else:
                    print("A imagem ISO não foi encontrada. Tente novamente.")
        
        run_args = [
            "--name", f"sistema_CISO_{nome}",
            "--restart", "unless-stopped",
            "-e", "BOOT_MODE=legacy",
            "-e", "DISK_SIZE=50G",
            "-e", "BOOT=/boot.iso",
        ]
        # checa suporte KVM
        kvm = subprocess.run("lsmod | grep -q kvm", shell=True).returncode == 0
        if kvm:
            print("Suporte KVM detectado, usando aceleração KVM.")
            net  = "-netdev user,id=net0,hostfwd=tcp::3389-:3389 "
            net += "-device virtio-net-pci,netdev=net0"
            run_args += [
                "-e", 'DISK_TYPE=virtio-blk',
                "-e", f"ARGUMENTS={net} -cpu host -m 4G -smp 2 -vga std",
                # "-e", 'ARGUMENTS=-cpu host -m 4G -smp 2 -vga std',
                "--device", "/dev/kvm",
            ]
        else:
            print("Sem KVM, caindo para TCG (mais lento).")
            net  = "-netdev user,id=net0,hostfwd=tcp::3389-:3389 "
            net += "-device e1000,netdev=net0"
            run_args += [
                "-e", "DISK_TYPE=ide",
                "-e", 'KVM=N',
                "-e", f"ARGUMENTS={net} -accel tcg,thread=multi -cpu Westmere -m 2G -smp 2 -vga std"
                # "-e", 'ARGUMENTS=-accel tcg,thread=multi -cpu Westmere -m 2G -smp 2 -vga std',
            ]
        self.portas_disponiveis = self.escolher_porta_disponivel(quantidade=2)
        run_args += [
            "-p", f"{self.portas_disponiveis[0]}:8006",
            "-p", f"{self.portas_disponiveis[1]}:3389",
            "--cap-add", "NET_ADMIN",
            "--device", "/dev/net/tun",
            "-v", f"{caminho_isos}/image.iso:/boot.iso:ro",
            "-v", f"{caminho_dados}:/storage",
            "--stop-timeout", "120",
            "-d",
            "qemux/qemu",
        ]

        self.remove_container(f"sistema_CISO_{nome}")
        self.executar_comandos_run_OrAnd_dockerfile(
            run_cmd=run_args
        )

        print("\nInstalação do sistema_CISO concluída.\n")
        print("IPs possíveis para acesso:")
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        resultados = self.executar_comandos(comandos)
        print("Portas de acesso:")
        print(f" - Porta Web: {self.portas_disponiveis[0]}")
        print(f" - Porta RDP: {self.portas_disponiveis[1]}")
