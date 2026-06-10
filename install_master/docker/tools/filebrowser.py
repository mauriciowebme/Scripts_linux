import os
import time
import subprocess

from install_master.core.docker_base import DockerBase


class MixinFileBrowser(DockerBase):
    def instala_filebrowser(self,):
        portas = self.escolher_porta_disponivel()
        container = f"""docker run -d \
                    --name filebrowser \
                    --restart=unless-stopped \
                    --memory=256m \
                    --cpus=1 \
                    --user 0:0 \
                    -p {portas[0]}:80 \
                    -v /:/srv \
                    -v {self.install_principal}/filebrowser/database.db:/database.db \
                    filebrowser/filebrowser
                """
        
        comandos = [
            # f"rm -r {self.install_principal}/filebrowser",
            f"mkdir -p {self.install_principal}/filebrowser",
            f"touch {self.install_principal}/filebrowser/database.db",
            container,
            ]
        self.remove_container('filebrowser')
        resultados = self.executar_comandos(comandos)
        
        # Aguarda e captura a senha gerada automaticamente
        print("Aguardando senha ser gerada...")
        time.sleep(15)
        
        senha_padrao = None
        try:
            result = subprocess.run(
                "docker logs filebrowser".split(),
                capture_output=True,
                text=True
            )
            
            # Busca pela senha nos logs
            for linha in result.stderr.splitlines():
                if "randomly generated password:" in linha:
                    senha_padrao = linha.split("randomly generated password:")[1].strip()
                    break
                
        except Exception as e:
            print(f"Erro: {e}")
        
        print(f"Possiveis ip's para acesso:")
        comandos = [
            "ip addr show | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1",
        ]
        self.executar_comandos(comandos, exibir_executando=False)
        print(f'Porta para uso local: {portas[0]}')
        print(f'Usuario padrão: admin')
        
        if senha_padrao:
            print(f'Senha gerada automaticamente: {senha_padrao}')
        else:
            print(f'📌 IMPORTANTE: Verifique os logs para obter a senha inicial!')
            print(f'Execute: docker logs filebrowser')
            print(f'Procure pela linha com "randomly generated password:"')
