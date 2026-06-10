import subprocess

from install_master.core.docker_base import DockerBase


class MixinWindowsKVM(DockerBase):

    def instala_windows_KVM_docker(self,):
        # link do projeto: https://github.com/dockur/windows
        
         # Verifica suporte à virtualização
        print("Verificando suporte à virtualização...")
        try:
            comandos_virtualizacao = ["egrep -c '(vmx|svm)' /proc/cpuinfo"]
            resultado_virtualizacao = self.executar_comandos(comandos_virtualizacao)
            # Captura a saída do comando
            virtualizacao_output = resultado_virtualizacao.get(comandos_virtualizacao[0], [])
            if not virtualizacao_output or "Erro:True" in virtualizacao_output:
                print("Erro ao executar o comando para verificar suporte à virtualização.")
                return
            # Converte a saída para inteiro
            virtualizacao = int(virtualizacao_output[0].strip())
            if virtualizacao == 0:
                print("Erro: Sua máquina não suporta virtualização. Ative o suporte na BIOS antes de continuar.")
                return
        except (KeyError, ValueError, IndexError) as e:
            print(f"Erro ao verificar suporte à virtualização: {e}")
            return

        # Verifica dispositivo KVM
        print("Verificando dispositivo KVM...")
        try:
            comandos_kvm = ["ls -l /dev/kvm"]
            resultado_kvm = self.executar_comandos(comandos_kvm)
            # Captura a saída do comando
            kvm_output = resultado_kvm.get(comandos_kvm[0], [])
            if not kvm_output or "No such file or directory" in kvm_output[0]:
                print("Erro: O dispositivo KVM não está disponível. Instale e configure KVM antes de continuar.")
                return
        except (KeyError, IndexError) as e:
            print(f"Erro ao verificar o dispositivo KVM: {e}")
            return
        print('\nIniciando instalação do container Windows.')
        local_install = input('\nDigite o local onde deseja instalar sem o / no final: ')
        nome_container = input('Digite o nome para o container Windows: ')
        senha = input('Digite a senha para acessar o Windows(o usuario sempre sera admin_win): ')
        memoria = input('Digite a quantidade de memoria GB(apenas numeros): ')
        cpu = input('Digite a quantidade de CPUs (apenas numeros): ')
        disco = input('Digite tamanho do disco GB(apenas numeros): ')
        print('\n')
        portas = self.escolher_porta_disponivel(quantidade=2)
        self.remove_container(f'windows_{nome_container}')

        comandos = [
            f"""sudo docker run -d \
                    --name windows_{nome_container} \
                    --restart=unless-stopped \
                    -p {portas[0]}:3389/tcp \
                    -p {portas[0]}:3389/udp \
                    -p {portas[1]}:8006 \
                    --device=/dev/kvm \
                    --cap-add=NET_ADMIN \
                    -e RAM_SIZE="{memoria}G" \
                    -e CPU_CORES="{cpu}" \
                    -e DISK_SIZE="{disco}G" \
                    -e LANGUAGE="pt-BR" \
                    -e USERNAME="admin_win" \
                    -e PASSWORD="{senha}" \
                    -e LANGUAGE="pt-BR" \
                    -v {local_install}/windows_{nome_container}/win:/storage \
                    -v {local_install}/windows_{nome_container}/data:/data \
                    dockurr/windows:latest
                """
        ]
        resultados = self.executar_comandos(comandos)

        print('\nIPs possíveis para acesso:')
        comandos = [
            f"hostname -I | tr ' ' '\n'",
        ]
        resultados = self.executar_comandos(comandos)
        print('Portas de acesso:')
        print(' - Usuario: admin_win')
        print(f' - Porta Web: {portas[1]}, desative no painel do portainer depois de usar apenas localmente!')
        print(f' - Porta RDP: {portas[0]}')
