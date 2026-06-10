from install_master.core.docker_base import DockerBase


class MixinRedis(DockerBase):
    def instala_redis_docker(self):
        print("Iniciando instalação redis:")
        senha = input("Configure uma senha para acessar: ")
        container = f"""docker run -d \
                        --name redis \
                        --restart=unless-stopped \
                        --memory=256m \
                        --cpus=1 \
                        -p 6379:6379 \
                        redis redis-server --requirepass "{senha}"
                    """
        comandos = [container]
        self.remove_container('redis')
        resultados = self.executar_comandos(comandos)
        print("Instalação do Redis concluída.")
        print("")
        print("Porta de acesso: 6379")
        print("")
        print("Realize testes assim:")
        print("docker exec -it redis redis-cli")
        print("")
        print("AUTH sua_senha_aqui")
        print('set meu-teste "funcionando"')
        print("get meu-teste")
        print("info memory")
        print("")
