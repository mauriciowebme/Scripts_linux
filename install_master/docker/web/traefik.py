import os
import re
import subprocess
import textwrap
from pathlib import Path

try:
    import yaml
except ImportError:
    pass

import time

from install_master.core.docker_base import DockerBase


class MixinTraefik(DockerBase):

    def adiciona_redirecionamento_traefik(self, container, dominio=None, porta=None):
        """
        Exemplo de uso:
        
        container = f"docker run -d \
                        --name webssh \
                        --restart=unless-stopped \
                        -p 8001:8000 \
                        liftoff/gateone
                    "
        OBS: Coloque 3 aspas no lugar de uma.
                    
        resposta = input('Deseja redirecionar com traefik?: S ou N: ')
        if resposta.lower() == 's':
            container = self.adiciona_redirecionamento_traefik(container)
        
        """
        if dominio == None:
            dominio = input('Digite o dominio:')
        if porta == None:
            porta = input('Digite a porta do container:')
        
        container = container.replace( '  ', '' ).replace( '\n', '' )
        imagem = container.split()[-1]
        container = container[:-len(imagem)].rstrip()
        
        dominio_ = dominio.replace('.', '_')
        labels = rf""" --network {self.redes_docker[0]} \
                --label traefik.enable=true \
                --label traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https \
                --label traefik.http.routers.{dominio_}.rule="Host(`{dominio}`)" \
                --label traefik.http.routers.{dominio_}.entrypoints=web,websecure \
                --label traefik.http.routers.{dominio_}.tls.certresolver=le \
                --label traefik.http.services.{dominio_}.loadbalancer.server.port={porta} \
            """
        container = container + labels.replace( '  ', '' ) + imagem
        return container

    def cria_dynamic_conf_traefik(self, email=None):
        base_dir = f"{self.install_principal}/traefik"
        dyn_dir  = f"{base_dir}/dynamic"
        le_dir   = f"{base_dir}/lets-encrypt"
        dynamic_conf = f"{dyn_dir}/dynamic_conf.yml"

        # pastas
        os.makedirs(dyn_dir, exist_ok=True)
        os.makedirs(le_dir,  exist_ok=True)

        # acme.json (perms 600)
        acme_path = f"{le_dir}/acme.json"
        if not os.path.exists(acme_path):
            with open(acme_path, "w") as _f:
                _f.write("")
            os.chmod(acme_path, 0o600)

        # cria arquivo dinâmico somente com http:{routers,services}
        if not os.path.exists(dynamic_conf):
            data = {"http": {"routers": {}, "services": {}}}
            with open(dynamic_conf, "w") as f:
                yaml.safe_dump(data, f, sort_keys=False)

        return dynamic_conf
        
    def adiciona_roteador_servico_traefik(self, dominio=None, endereco=None, porta=None):
        self.verifica_container_existe('traefik', self.instala_traefik)

        if dominio is None:
            dominio = input('Digite o dominio (sem o www): ').strip()
        if endereco is None:
            endereco = input('Coloque o endereço do container ou IP da rede que deseja apontar: ').strip()
        if porta is None:
            porta = input('Digite a porta (se for container, use a porta INTERNA): ').strip()

        # valida domínio (sem underscore)
        if "_" in dominio or not re.match(r"^[A-Za-z0-9.-]+$", dominio):
            raise ValueError(f"Domínio inválido: {dominio}. Use apenas letras, números, hífens e pontos (sem _ ).")

        # garante rede entre traefik e o container de destino (sua função existente)
        self.cria_rede_docker(associar_container_nome=endereco, numero_rede=0)

        dynamic_conf = self.cria_dynamic_conf_traefik()

        # carrega, edita e salva
        with open(dynamic_conf, 'r') as file:
            config = yaml.safe_load(file) or {}

        config.setdefault('http', {})
        config['http'].setdefault('routers', {})
        config['http'].setdefault('services', {})

        router_name  = dominio.replace('.', '_')
        service_name = f"{router_name}_service"

        # router HTTPS (websecure) — TLS via certResolver "le"
        config['http']['routers'][router_name] = {
            'rule': f"Host(`{dominio}`)",
            'entryPoints': ['websecure'],
            'service': service_name,
            'tls': {'certResolver': 'le'}
        }

        # service para o backend alvo
        config['http']['services'][service_name] = {
            'loadBalancer': {'servers': [{'url': f"http://{endereco}:{porta}"}]}
        }

        with open(dynamic_conf, 'w') as file:
            yaml.safe_dump(config, file, sort_keys=False)

        print(f"✔ Router/Service adicionados: {dominio} -> http://{endereco}:{porta}")
        print(f"Arquivo: {dynamic_conf}")
        print("Obs: cert (LE) depende do DNS A (e AAAA correto/ausente) apontando para este servidor.")

    def instala_traefik(self):
        print("Iniciando instalação do Traefik.")
        email = input('Digite um e-mail para gerar o certificado: ').strip()

        # garante estrutura dinâmica e acme.json 600
        self.cria_dynamic_conf_traefik(email=email)

        base_dir = f"{self.install_principal}/traefik"
        dyn_dir  = f"{base_dir}/dynamic"
        le_dir   = f"{base_dir}/lets-encrypt"

        self.remove_container('traefik')

        comando = f"""docker run -d \
        --name traefik \
        --restart=unless-stopped \
        --memory=256m \
        --cpus=1 \
        -p 80:80 \
        -p 443:443 \
        -p 8080:8080 \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v {le_dir}:/letsencrypt \
        -v {dyn_dir}:/etc/traefik/dynamic \
        traefik:latest \
        --log.level=INFO \
        --api.insecure=true \
        --providers.docker=true \
        --providers.docker.exposedbydefault=false \
        --providers.file.directory=/etc/traefik/dynamic \
        --providers.file.watch=true \
        --entrypoints.web.address=:80 \
        --entrypoints.web.http.redirections.entrypoint.to=websecure \
        --entrypoints.web.http.redirections.entrypoint.scheme=https \
        --entrypoints.websecure.address=:443 \
        --certificatesresolvers.le.acme.email={email} \
        --certificatesresolvers.le.acme.storage=/letsencrypt/acme.json \
        --certificatesresolvers.le.acme.httpchallenge=true \
        --certificatesresolvers.le.acme.httpchallenge.entrypoint=web
        """
        self.executar_comandos([comando])

        # conecta rede padrão do seu ambiente (como você já fazia)
        self.cria_rede_docker(associar_container_nome='traefik', numero_rede=0)

        print('\nIPs possíveis para acesso:')
        self.executar_comandos(["hostname -I | tr ' ' '\\n'"])
        print('Porta de acesso (dashboard temporária): 8080')
