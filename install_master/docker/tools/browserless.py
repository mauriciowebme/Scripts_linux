import os
import textwrap

from install_master.core.docker_base import DockerBase


class MixinBrowserless(DockerBase):
    def instala_browserless(self):
        print("Iniciando instalacao do Browserless (Chromium headless).")

        base_dir = f"{self.install_principal}/browserless"

        porta = self.escolher_porta_disponivel()[0]
        max_sessions = "2"
        timeout_ms = "15000"
        token_input = input("TOKEN de acesso (Enter gera automaticamente): ").strip()
        token = token_input or self.generate_password(24)
        if not token_input:
            print(f"TOKEN gerado automaticamente: {token}")

        self.remove_container("browserless_central")

        compose_yml = textwrap.dedent(f"""
        version: '3'
        services:
          browserless:
            image: ghcr.io/browserless/chromium:latest
            container_name: browserless_central
            restart: always
            ports:
              - "{porta}:3000"
            environment:
              - MAX_CONCURRENT_SESSIONS={max_sessions}
              - TOKEN={token}
              - CONNECTION_TIMEOUT={timeout_ms}
            deploy:
              resources:
                limits:
                  cpus: "1"
                  memory: "512m"
            shm_size: "512m"
        """).strip() + "\n"

        self.aplicar_compose(compose_yml=compose_yml)

        print("\nBrowserless disponivel.")
        print(f"- URL: http://<ip-servidor>:{porta}")
        print("- Use o TOKEN configurado para autenticar as requisicoes.")
