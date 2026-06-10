import os
import subprocess

from install_master.core.docker_base import DockerBase


class MixinIA(DockerBase):
    def instala_open_webui(self):
        caminho_ollama = f"{self.install_principal}/IA/ollama"
        caminho_open_webui = f"{self.install_principal}/IA/open_webui"
        
        comandos = [
            "docker network create ollama-network",
            f"""docker run -d \
            --name ollama \
            --network ollama-network \
            -p 11434:11434 \
            -e OLLAMA_HOST=0.0.0.0 \
            -e OLLAMA_MAX_LOADED_MODELS=1 \
            -e OLLAMA_NUM_PARALLEL=2 \
            -e OLLAMA_KEEP_ALIVE=1 \
            -v {caminho_ollama}:/root \
            ollama/ollama""",
        ]
        
        comandos += [
            """docker exec -it ollama bash -c "ollama list" """,
            f"""docker run -d \
            --name open-webui \
            --network ollama-network \
            -p 3001:8080 \
            -v {caminho_open_webui}:/app/backend/data \
            -e OLLAMA_BASE_URL=http://ollama:11434 \
            ghcr.io/open-webui/open-webui:main"""
        ]
        
        # Adiciona permissão 777 no caminho persistente do container ollama
        self.gerenciar_permissoes_pasta(caminho_ollama, '777')
        
        self.remove_container(f'open-webui')
        self.remove_container(f'ollama')
        self.executar_comandos(comandos, ignorar_erros=True)
        
        # Instruções de uso no final
        print("\n" + "="*50)
        print("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*50)
        print("\n📋 INSTRUÇÕES DE USO:")
        print("1. Acesse a interface web em: http://seu-ip:3001")
        print("2. Na primeira execução, você precisará criar uma conta de administrador")
        print("3. Conecte ao Ollama no menu 'Connections' usando a URL: http://ollama:11434")
        
        print("\n💡 MODELOS ADICIONAIS:")
        print("Você pode instalar mais modelos diretamente pela interface do Open WebUI ou usando o comando docker abaixo:")
        
        print("\n💡 COMANDOS ÚTEIS:")
        print("- Ver modelos instalados: docker exec ollama bash -c \"ollama list\"")
        print("- Instalar novo modelo:   docker exec ollama bash -c \"ollama pull qwen2.5:3b\" # Qwen 2.5 3B (32k)")
        print("- Interagir com modelo:   docker exec -it ollama bash -c \"ollama run qwen2.5:3b\"")
        print("- Reiniciar serviço:      docker restart ollama open-webui")
        
        print("\n⚠️ ATENÇÃO:")
        print("- Para modelos maiores (como llama3), verifique se seu hardware tem recursos suficientes")
