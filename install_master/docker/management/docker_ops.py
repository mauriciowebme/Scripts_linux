import subprocess
import time
import json

from install_master.core.docker_base import DockerBase


class MixinDockerOps(DockerBase):

    def listar_containers_docker(self):
        """Lista todos os containers Docker (rodando e parados)"""
        print("\n=== CONTAINERS DOCKER ===\n")
        
        try:
            # Listar containers rodando
            print("CONTAINERS RODANDO:")
            cmd_running = ["docker", "ps", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"]
            subprocess.run(cmd_running, check=False)
            
            # Listar containers parados
            print("\nCONTAINERS PARADOS:")
            cmd_stopped = ["docker", "ps", "-a", "--filter", "status=exited", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}"]
            subprocess.run(cmd_stopped, check=False)
            
        except Exception as e:
            print(f"❌ Erro ao listar containers: {e}")
    
    def parar_container_docker(self):
        """Para um container Docker"""
        print("\n=== PARAR CONTAINER DOCKER ===\n")
        
        # Listar containers rodando
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container rodando encontrado.")
            return
        
        print("Containers rodando:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para PARAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nParando container '{container}'...")
            subprocess.run(["docker", "stop", container], check=True)
            print(f"Container '{container}' parado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao parar container: {e}")
    
    def iniciar_container_docker(self):
        """Inicia um container Docker parado"""
        print("\n=== INICIAR CONTAINER DOCKER ===\n")
        
        # Listar containers parados
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "status=exited", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container parado encontrado.")
            return
        
        print("Containers parados:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para INICIAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nIniciando container '{container}'...")
            subprocess.run(["docker", "start", container], check=True)
            print(f"Container '{container}' iniciado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar container: {e}")
    
    def reiniciar_container_docker(self):
        """Reinicia um container Docker"""
        print("\n=== REINICIAR CONTAINER DOCKER ===\n")
        
        # Listar containers rodando
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container rodando encontrado.")
            return
        
        print("Containers rodando:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para REINICIAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nReiniciando container '{container}'...")
            subprocess.run(["docker", "restart", container], check=True)
            print(f"Container '{container}' reiniciado com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao reiniciar container: {e}")
    
    def excluir_container_docker(self):
        """Exclui um container Docker (parado ou rodando)"""
        print("\n=== EXCLUIR CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True
        )
        
        linhas = [l.strip() for l in result.stdout.split('\n') if l.strip()]
        
        if not linhas:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        containers = []
        for i, linha in enumerate(linhas, 1):
            parts = linha.split('\t')
            if len(parts) >= 2:
                nome = parts[0]
                status = parts[1]
                containers.append(nome)
                print(f"[{i}] {nome} - {status}")
        
        escolha = input("\nEscolha o container para EXCLUIR (numero ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            confirmacao = input(f"\nATENCAO: Deseja realmente EXCLUIR o container '{container}'? (s/N): ").strip().lower()
            
            if confirmacao != 's':
                print("Operacao cancelada.")
                return
            
            # Parar container se estiver rodando
            subprocess.run(["docker", "stop", container], check=False, capture_output=True)
            
            # Excluir container
            print(f"\nExcluindo container '{container}'...")
            subprocess.run(["docker", "rm", container], check=True)
            print(f"Container '{container}' excluido com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao excluir container: {e}")
    
    def ver_logs_container_docker(self):
        """Visualiza os logs de um container Docker"""
        print("\n=== LOGS DO CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para ver LOGS (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nOpcoes de logs:")
            print("[1] 📜  Ultimas 50 linhas")
            print("[2] 📜  Ultimas 100 linhas")
            print("[3] 📜  Ultimas 500 linhas")
            print("[4] 📄  Todos os logs")
            print("[5] ️  Seguir logs (tempo real)")
            
            opcao_log = input("\nEscolha uma opcao: ").strip()
            
            print(f"\nLogs do container '{container}':\n")
            print("=" * 80)
            
            if opcao_log == "1":
                subprocess.run(["docker", "logs", "--tail", "50", container])
            elif opcao_log == "2":
                subprocess.run(["docker", "logs", "--tail", "100", container])
            elif opcao_log == "3":
                subprocess.run(["docker", "logs", "--tail", "500", container])
            elif opcao_log == "4":
                subprocess.run(["docker", "logs", container])
            elif opcao_log == "5":
                print("Pressione Ctrl+C para sair...\n")
                subprocess.run(["docker", "logs", "-f", container])
            else:
                print("❌ Opção inválida.")
                return
            
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("\n\nVisualizacao de logs interrompida.")
        except Exception as e:
            print(f"❌ Erro ao ver logs: {e}")
    
    def inspecionar_container_docker(self):
        """Inspeciona detalhes de um container Docker"""
        print("\n=== INSPECIONAR CONTAINER DOCKER ===\n")
        
        # Listar todos os containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]
        
        if not containers:
            print("❌ Nenhum container encontrado.")
            return
        
        print("Containers disponíveis:")
        for i, container in enumerate(containers, 1):
            print(f"[{i}] {container}")
        
        escolha = input("\nEscolha o container para INSPECIONAR (número ou nome): ").strip()
        
        try:
            # Tenta converter para índice
            if escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(containers):
                    container = containers[idx]
                else:
                    print("❌ Número inválido.")
                    return
            else:
                container = escolha
            
            print(f"\nDetalhes do container '{container}':\n")
            print("=" * 80)
            
            # Informações básicas
            subprocess.run([
                "docker", "inspect", 
                "--format", "ID: {{.Id}}\nNome: {{.Name}}\nImagem: {{.Config.Image}}\nStatus: {{.State.Status}}\nCriado em: {{.Created}}\nIP: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}\nPortas: {{range $p, $conf := .NetworkSettings.Ports}}{{$p}} -> {{(index $conf 0).HostPort}} {{end}}",
                container
            ])
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Erro ao inspecionar container: {e}")
    
    def limpar_recursos_docker(self):
        """Limpa recursos não utilizados do Docker (containers parados, imagens órfãs, volumes, etc)"""
        print("\n=== LIMPAR RECURSOS DOCKER ===\n")
        
        print("ATENCAO: Esta operacao ira remover:")
        print("  - Containers parados")
        print("  - Redes nao utilizadas")
        print("  - Imagens orfas (dangling)")
        print("  - Cache de build")
        
        confirmacao = input("\nDeseja continuar? (s/N): ").strip().lower()
        
        if confirmacao != 's':
            print("Operacao cancelada.")
            return
        
        try:
            print("\nLimpando recursos nao utilizados...\n")
            subprocess.run(["docker", "system", "prune", "-f"], check=True)
            print("\nRecursos limpos com sucesso!")
            
            # Mostrar espaço liberado
            print("\nEspaco em disco Docker:")
            subprocess.run(["docker", "system", "df"])
            
        except Exception as e:
            print(f"❌ Erro ao limpar recursos: {e}")
    
    def menu_gerenciamento_docker(self):
        """Menu de gerenciamento de containers Docker"""
        opcoes_gerenciamento = [
            ("📋  Listar Containers", self.listar_containers_docker),
            ("▶️  Iniciar Container", self.iniciar_container_docker),
            ("⏹️  Parar Container", self.parar_container_docker),
            ("🔄  Reiniciar Container", self.reiniciar_container_docker),
            ("🗑️  Excluir Container", self.excluir_container_docker),
            ("📄  Ver Logs de Container", self.ver_logs_container_docker),
            ("🔍  Inspecionar Container", self.inspecionar_container_docker),
            ("  Limpar Recursos Nao Utilizados", self.limpar_recursos_docker),
            ("↩️  Voltar ao Menu Docker", None)
        ]
        
        self.mostrar_menu_paginado(opcoes_gerenciamento, titulo="📦 GERENCIAMENTO DE CONTAINERS", itens_por_pagina=10)
