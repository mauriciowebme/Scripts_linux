from install_master.core.docker_base import DockerBase


class MixinSelenium(DockerBase):
    def instala_selenium_firefox(self):
        print("Iniciando instalação selenium_firefox:")
        # senha = input("Configure uma senha para acessar: ")
        container = f"""docker run -d \
                --name selenium-firefox \
                --restart=unless-stopped \
                -e SE_NODE_MAX_SESSIONS=2 \
                -e SE_NODE_SESSION_TIMEOUT=20 \
                -p 4444:4444 \
                -p 7900:7900 \
                --shm-size=2g \
                selenium/standalone-firefox:latest
                """
        comandos = [container]
        self.remove_container('selenium-firefox')
        resultados = self.executar_comandos(comandos,)
        print("Instalação do selenium_firefox concluída.")
        print("")
        print("Porta de acesso: 7900 - VNC")
        print("Porta de acesso: 4444 - Selenium")
        print("Aponte seus testes do WebDriver para http://servidor:4444")
        print("")
