import json
import os
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

from install_master.core.docker_base import DockerBase


class MixinTunnels(DockerBase):

    def gerenciar_tuneis_ssh(self):
        """Menu principal do gerenciador de túneis SSH"""
        diretorio_tuneis = f"{self.install_principal}/tuneis"
        os.makedirs(diretorio_tuneis, exist_ok=True)
        os.makedirs(f"{diretorio_tuneis}/scripts", exist_ok=True)
        os.makedirs(f"{diretorio_tuneis}/logs", exist_ok=True)

        while True:
            print("\n" + "=" * 55)
            print("🔗 GERENCIADOR DE CLIENTES SSH")
            print("=" * 55)

            tuneis = self._carregar_tuneis()
            ativos = self._tuneis_ativos()

            print(f"\n📊 Clientes configurados: {len(tuneis)}")
            print(f"🟢 Clientes ativos: {len(ativos)}")

            if tuneis:
                print("\n📋 Resumo rápido:")
                for nome, info in tuneis.items():
                    status = "🟢 ATIVO" if nome in ativos else "🔴 INATIVO"
                    print(f"  {status} | {nome} → porta {info['porta_remota']} ({info['tipo']})")

            print("\n" + "-" * 55)
            print("[1] ➕  Adicionar cliente")
            print("[2] ️  Editar cliente")
            print("[3] 🗑️  Excluir cliente")
            print("[4] 📋  Clientes conectados")
            print("[5] 📜  Script cliente")
            print("[6] 🔓  Abrir/Fechar portas")
            print("[0] ↩️  Voltar")
            print("=" * 55)

            opcao = input("\nEscolha: ").strip()

            if opcao == "1":
                self._adicionar_cliente()
            elif opcao == "2":
                self._editar_tunel()
            elif opcao == "3":
                self._excluir_tunel()
            elif opcao == "4":
                self._visualizar_tuneis()
            elif opcao == "5":
                self._script_cliente()
            elif opcao == "6":
                self._gerenciar_portas()
            elif opcao == "0":
                break
            else:
                print("❌ Opção inválida.")

    def _carregar_tuneis(self):
        """Carrega túneis do JSON"""
        caminho = f"{self.install_principal}/tuneis/tuneis.json"
        if os.path.exists(caminho):
            try:
                with open(caminho, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _salvar_tuneis(self, tuneis):
        """Salva túneis no JSON"""
        caminho = f"{self.install_principal}/tuneis/tuneis.json"
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w") as f:
            json.dump(tuneis, f, indent=2, ensure_ascii=False)

    def _log_tunel(self, nome, mensagem):
        """Registra evento de túnel no log"""
        log_dir = f"{self.install_principal}/tuneis/logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{nome}.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] {mensagem}\n")
        except Exception:
            pass

    def _tuneis_ativos(self):
        """Retorna set de nomes de túneis ativos baseado em portas listening no sshd"""
        ativos = set()
        try:
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True, text=True
            )
            tuneis = self._carregar_tuneis()
            for linha in result.stdout.splitlines():
                if "sshd" not in linha:
                    continue
                for nome, info in tuneis.items():
                    if f":{info['porta_remota']} " in linha or f":{info['porta_remota']}\t" in linha:
                        ativos.add(nome)
        except Exception:
            pass
        return ativos

    def _escolher_tunel(self, titulo="Escolha o túnel", tuneis=None):
        """Exibe lista numerada e retorna o nome do túnel escolhido"""
        if tuneis is None:
            tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n⚪ Nenhum túnel configurado.")
            return None

        print(f"\n{titulo}:")
        for i, nome in enumerate(tuneis.keys(), 1):
            info = tuneis[nome]
            print(f"  [{i}] {nome} → porta {info['porta_remota']} ({info['tipo']})")

        escolha = input("\nNúmero (0 para cancelar): ").strip()
        if escolha == "0" or not escolha:
            return None

        try:
            idx = int(escolha) - 1
            nomes = list(tuneis.keys())
            if 0 <= idx < len(nomes):
                return nomes[idx]
        except ValueError:
            pass

        print("❌ Número inválido.")
        return None

    def _abrir_porta_firewall(self, porta):
        """Abre porta no firewall local (UFW + iptables). Retorna True se ok."""
        sucesso = False

        try:
            check_result = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                capture_output=True
            )
            if check_result.returncode == 0:
                print(f"  ✅ Porta {porta} JÁ está liberada no iptables")
                return True
        except Exception:
            pass

        try:
            ufw_check = subprocess.run(
                ["sudo", "ufw", "status"],
                capture_output=True, text=True
            )
            if "active" in ufw_check.stdout.lower():
                subprocess.run(
                    ["sudo", "ufw", "allow", str(porta), "tcp"],
                    check=True
                )
                print(f"  ✅ Porta {porta} liberada no UFW")
                sucesso = True
        except Exception as e:
            print(f"  ⚠️ UFW não disponível: {e}")

        try:
            subprocess.run(
                ["sudo", "iptables", "-I", "INPUT", "1", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                check=True
            )
            print(f"  ✅ Porta {porta} liberada no iptables")

            if shutil.which("netfilter-persistent"):
                subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)
                print(f"  💾 Regras salvas (netfilter-persistent)")
            elif shutil.which("iptables-save"):
                subprocess.run(
                    ["sudo", "sh", "-c", "iptables-save > /etc/iptables/rules.v4"],
                    check=False
                )
                print(f"  💾 Regras salvas (/etc/iptables/rules.v4)")
            return True
        except Exception as e:
            print(f"  ❌ Falha ao configurar iptables: {e}")
            return sucesso

    def _fechar_porta_firewall(self, porta):
        """Remove regra de firewall. Retorna True se ok."""
        try:
            check_result = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                capture_output=True
            )

            if check_result.returncode == 0:
                subprocess.run(
                    ["sudo", "iptables", "-D", "INPUT", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                    check=True
                )
                print(f"  ✅ Porta {porta} fechada no iptables")
            else:
                print(f"  ℹ️ Porta {porta} já estava fechada no iptables")

            subprocess.run(
                ["sudo", "ufw", "delete", "allow", str(porta), "tcp"],
                capture_output=True
            )

            if shutil.which("netfilter-persistent"):
                subprocess.run(["sudo", "netfilter-persistent", "save"], check=False)
                print(f"  💾 Regras salvas (netfilter-persistent)")
            elif shutil.which("iptables-save"):
                subprocess.run(
                    ["sudo", "sh", "-c", "iptables-save > /etc/iptables/rules.v4"],
                    check=False
                )
                print(f"  💾 Regras salvas (/etc/iptables/rules.v4)")

            print(f"  ✅ Regra de firewall removida para porta {porta}")
            return True
        except Exception as e:
            print(f"  ⚠️ Falha ao remover regra: {e}")
            return False

    def _gerar_scripts_tunel(self, nome):
        """Gera scripts .bat e .sh para um túnel com chave embutida"""
        tuneis = self._carregar_tuneis()
        if nome not in tuneis:
            print(f"❌ Túnel '{nome}' não encontrado.")
            return

        info = tuneis[nome]
        chave_privada = info.get('chave_privada', os.path.expanduser(f"~/.ssh/id_ed25519_{nome}"))

        if not os.path.exists(chave_privada):
            print(f"❌ Chave privada não encontrada: {chave_privada}")
            print("   Regenerando chave...")
            ssh_dir = os.path.expanduser("~/.ssh")
            os.makedirs(ssh_dir, exist_ok=True)
            result = subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", chave_privada,
                 "-C", f"tunel-{nome}@{info['servidor']}"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"❌ Falha ao gerar chave: {result.stderr.strip()}")
                return
            print("✅ Nova chave gerada!")

            auth_keys = os.path.join(ssh_dir, "authorized_keys")
            try:
                with open(f"{chave_privada}.pub", 'r') as f:
                    chave_pub_content = f.read().strip()
                existente = False
                if os.path.exists(auth_keys):
                    with open(auth_keys, 'r') as f:
                        existente = chave_pub_content in f.read()
                if not existente:
                    with open(auth_keys, 'a') as f:
                        f.write(chave_pub_content + "\n")
                    print("✅ Chave pública adicionada ao authorized_keys")
            except Exception as e:
                print(f"⚠️ Falha ao adicionar chave pública: {e}")

            info['chave_privada'] = chave_privada
            self._salvar_tuneis(tuneis)

        self._gerar_script_completo(nome, chave_privada)

    def _atualizar_ssh_config_silencioso(self):
        """Atualiza aliases SSH sem interação com usuário"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            return

        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        config_path = os.path.join(ssh_dir, "config")

        marca_inicio = "# === TUNEIS SSH - GERADO AUTOMATICAMENTE ==="
        marca_fim = "# === FIM TUNEIS SSH ==="

        conteudo_existente = ""
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                conteudo_existente = f.read()

        if marca_inicio in conteudo_existente:
            inicio = conteudo_existente.index(marca_inicio)
            try:
                fim = conteudo_existente.index(marca_fim) + len(marca_fim)
                conteudo_novo = conteudo_existente[:inicio] + conteudo_existente[fim + 1:]
            except ValueError:
                conteudo_novo = conteudo_existente[:inicio]
        else:
            conteudo_novo = conteudo_existente

        bloco_tuneis = f"\n{marca_inicio}\n"
        for nome, info in tuneis.items():
            bloco_tuneis += f"""
Host {nome}
    HostName {info['servidor']}
    Port 22
    User {info['usuario']}
    StrictHostKeyChecking no
"""
        bloco_tuneis += f"{marca_fim}\n"

        with open(config_path, "w") as f:
            f.write(conteudo_novo + bloco_tuneis)

        os.chmod(config_path, 0o600)

    def _ler_ssh_config(self):
        """Lê ~/.ssh/config e retorna lista de hosts configurados"""
        hosts = []
        ssh_config = os.path.expanduser("~/.ssh/config")
        if os.path.exists(ssh_config):
            try:
                with open(ssh_config, 'r') as f:
                    for linha in f:
                        if linha.strip().startswith('Host '):
                            host = linha.split()[1]
                            if '*' not in host:
                                hosts.append(host)
            except Exception:
                pass
        return hosts

    def _adicionar_cliente(self):
        """Adiciona novo cliente com geração automática de chaves e script"""
        print("\n" + "=" * 55)
        print("➕ ADICIONAR NOVO CLIENTE")
        print("=" * 55)

        tuneis_existentes = self._carregar_tuneis()

        contador = len(tuneis_existentes) + 1
        nome_sugerido = f"cliente_{contador}"
        nome = input(f"\n📝 Nome do cliente (Enter para '{nome_sugerido}'): ").strip().lower().replace(" ", "_") or nome_sugerido

        if nome in tuneis_existentes:
            print(f"\u274c Cliente '{nome}' já existe!")
            return

        if not re.match(r'^[a-zA-Z0-9_-]+$', nome):
            print("\u274c Nome inválido. Use apenas letras, números, _ ou -.")
            return

        servidor_detectado = self.exibe_ip()
        servidor = input(f"\n🌐 IP do servidor [{servidor_detectado}]: ").strip() or servidor_detectado

        print("\n🔍 Buscando porta livre na faixa 40450-40500...")
        portas_em_uso_json = {info['porta_remota'] for info in tuneis_existentes.values()}
        porta_remota = None

        for porta_teste in range(40450, 40501):
            if porta_teste in portas_em_uso_json:
                continue

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(('localhost', porta_teste)) == 0:
                        continue
            except Exception:
                pass

            porta_remota = porta_teste
            break

        if porta_remota is None:
            print("❌ Nenhuma porta livre encontrada na faixa 40450-40500.")
            return

        print(f"✅ Porta {porta_remota} encontrada e disponível!")

        print(f"\n🔓 Configurando firewall na porta {porta_remota}...")
        self._abrir_porta_firewall(porta_remota)

        porta_local = input("🏠 Porta local da máquina remota (Enter para 22): ").strip() or "22"
        if not porta_local.isdigit():
            print("❌ Porta local inválida.")
            return

        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        chave_privada = os.path.join(ssh_dir, f"id_ed25519_{nome}")
        chave_publica = f"{chave_privada}.pub"

        if os.path.exists(chave_privada):
            os.remove(chave_privada)
        if os.path.exists(chave_publica):
            os.remove(chave_publica)

        print(f"\n Gerando par de chaves único para '{nome}'...")
        result = subprocess.run(
            ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", chave_privada,
             "-C", f"tunel-{nome}@{servidor}"],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Falha ao gerar chave: {result.stderr.strip()}")
            return

        print("✅ Chaves geradas com sucesso!")

        auth_keys = os.path.join(ssh_dir, "authorized_keys")
        try:
            with open(chave_publica, 'r') as f:
                chave_pub_content = f.read().strip()

            existente = False
            if os.path.exists(auth_keys):
                with open(auth_keys, 'r') as f:
                    existente = chave_pub_content in f.read()

            if not existente:
                with open(auth_keys, 'a') as f:
                    f.write(chave_pub_content + "\n")
                print("✅ Chave pública adicionada ao authorized_keys")
            else:
                print("  Chave já está no authorized_keys")
        except Exception as e:
            print(f"⚠️ Falha ao adicionar chave pública: {e}")

        print("\n Tipo da máquina remota:")
        print("[1] 🪟  Windows")
        print("[2] 🐧  Linux")
        tipo_choice = input("Escolha (Enter para Linux): ").strip()
        if tipo_choice == "1":
            tipo = "windows"
        else:
            tipo = "linux"

        usuario = "root"

        tuneis_existentes[nome] = {
            "porta_remota": porta_remota,
            "porta_local": int(porta_local),
            "usuario": usuario,
            "servidor": servidor,
            "tipo": tipo,
            "chave_privada": chave_privada,
            "criado_em": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self._salvar_tuneis(tuneis_existentes)
        self._log_tunel(nome, f"Cliente adicionado: porta {porta_remota} -> {porta_local}")

        if len(tuneis_existentes) == 1:
            print("\n🔧 Configurando servidor SSH para túneis reversos...")
            if self._configurar_ssh_server_silencioso():
                print("✅ Servidor SSH configurado para túneis.")
            else:
                print("⚠️ Falha ao configurar servidor SSH. Verifique manualmente.")

        print("\n🔄 Gerando script cliente...")
        self._gerar_script_completo(nome, chave_privada)

        tipo_label = "Windows" if tipo == "windows" else "Linux"
        print(f"\n{'=' * 55}")
        print(f"✅ Cliente '{nome}' criado com sucesso!")
        print(f"\n Resumo:")
        print(f"   Nome: {nome}")
        print(f"   IP do servidor: {servidor}")
        print(f"   Porta remota: {porta_remota}")
        print(f"   Porta local: {porta_local}")
        print(f"   Tipo: {tipo_label}")
        print(f"\n Scripts gerados em: tuneis/scripts/{nome}.sh")
        if tipo == "windows":
            print(f"📄 Scripts gerados em: tuneis/scripts/{nome}.bat")
        print(f"\n{'=' * 55}")
        print(f"INSTRUÇÕES:")
        print(f"1. Copie o script para a máquina remota")
        if tipo == "linux":
            print(f"2. Execute: bash {nome}.sh")
        else:
            print(f"2. Execute: {nome}.bat")
        print(f"3. O túnel será configurado automaticamente")
        print(f"{'=' * 55}")

    def _gerar_script_completo(self, nome, chave_privada_path):
        """Gera script cliente com chave privada embutida e autodetecção de OS"""
        tuneis = self._carregar_tuneis()
        if nome not in tuneis:
            print(f"❌ Cliente '{nome}' não encontrado.")
            return

        info = tuneis[nome]

        if not os.path.exists(chave_privada_path):
            print(f"❌ Chave privada não encontrada: {chave_privada_path}")
            return

        with open(chave_privada_path, 'r') as f:
            chave_privada_content = f.read()

        diretorio = f"{self.install_principal}/tuneis/scripts"
        os.makedirs(diretorio, exist_ok=True)
        caminho = f"{diretorio}/{nome}.sh"

        conteudo = f'''#!/bin/bash
# ============================================
# Script de Tunel SSH - Cliente: {nome}
# Gerado automaticamente pelo servidor
# ============================================

# Configuracoes do servidor
SERVIDOR="{info['servidor']}"
PORTA_REMOTA={info['porta_remota']}
PORTA_LOCAL={info['porta_local']}
USUARIO="{info['usuario']}"

# Chave privada embutida
CHAVE_PRIVADA_DIR="$HOME/.ssh/tunel_{nome}"
CHAVE_PRIVADA_FILE="$CHAVE_PRIVADA_DIR/id_ed25519"

echo ""
echo "========================================"
echo "   TUNEL SSH: {nome}"
echo "   Servidor: $SERVIDOR:$PORTA_REMOTA"
echo "   Local: 127.0.0.1:$PORTA_LOCAL"
echo "========================================"
echo ""

# Detectar sistema operacional
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
fi

echo "Sistema detectado: $OS"
echo ""

# Criar diretorio para chave privada
mkdir -p "$CHAVE_PRIVADA_DIR"
chmod 700 "$CHAVE_PRIVADA_DIR"

# Escrever chave privada
cat > "$CHAVE_PRIVADA_FILE" << 'CHAVE_EOF'
{chave_privada_content}CHAVE_EOF

chmod 600 "$CHAVE_PRIVADA_FILE"
echo "✅ Chave privada configurada"

# Verificar se ssh esta instalado
if ! command -v ssh &> /dev/null; then
    echo "SSH nao esta instalado!"
    if [[ "$OS" == "linux" ]]; then
        echo "   Instale com: sudo apt-get install openssh-client"
    elif [[ "$OS" == "windows" ]]; then
        echo "   Instale o OpenSSH do Windows"
    fi
    exit 1
fi

# Verificar se autossh esta instalado (opcional, mas recomendado)
if command -v autossh &> /dev/null; then
    echo "✅ autossh encontrado - usando modo persistente"
    SSH_CMD="autossh -M 0 --"
else
    echo "️ autossh nao encontrado - usando ssh puro (sem auto-reconexao)"
    echo "   Recomendação: instale autossh para reconexao automatica"
    SSH_CMD=""
fi

echo ""
echo "Conectando ao tunel..."
echo "Pressione Ctrl+C para desconectar"
echo ""

# Loop de conexao com autossh ou ssh
if [[ -n "$SSH_CMD" ]]; then
    # Modo autossh (persistente)
    exec $SSH_CMD ssh -o StrictHostKeyChecking=no \\
        -o BatchMode=yes \\
        -o ServerAliveInterval=30 \\
        -o ServerAliveCountMax=3 \\
        -i "$CHAVE_PRIVADA_FILE" \\
        -R $PORTA_REMOTA:127.0.0.1:$PORTA_LOCAL \\
        $USUARIO@$SERVIDOR -N
else
    # Modo ssh puro com loop
    while true; do
        echo "Conectado ao tunel..."
        ssh -o StrictHostKeyChecking=no \\
            -o BatchMode=yes \\
            -o ServerAliveInterval=30 \\
            -o ServerAliveCountMax=3 \\
            -i "$CHAVE_PRIVADA_FILE" \\
            -R $PORTA_REMOTA:127.0.0.1:$PORTA_LOCAL \\
            $USUARIO@$SERVIDOR -N

        echo ""
        echo "========================================"
        echo "   ATENCAO: Conexao caiu!"
        echo "========================================"
        echo "Reconectando em 5 segundos..."
        sleep 5
    done
fi
'''

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)

        os.chmod(caminho, 0o755)

        if info.get('tipo') == 'windows':
            caminho_bat = f"{diretorio}/{nome}.bat"

            chave_b64 = subprocess.run(
                ["base64", "-w0", chave_privada_path],
                capture_output=True, text=True
            ).stdout.strip()

            conteudo_bat = f'''@echo off
REM ============================================
REM Script de Tunel SSH - Cliente: {nome}
REM Gerado automaticamente pelo servidor
REM ============================================

set SERVIDOR={info['servidor']}
set PORTA_REMOTA={info['porta_remota']}
set PORTA_LOCAL={info['porta_local']}
set USUARIO={info['usuario']}

echo.
echo ========================================
echo    TUNEL SSH: {nome}
echo    Servidor: %SERVIDOR%:%PORTA_REMOTA%
echo    Local: 127.0.0.1:%PORTA_LOCAL%
echo ========================================
echo.

REM Criar diretorio para chave
if not exist "%USERPROFILE%\\.ssh\\tunel_{nome}" mkdir "%USERPROFILE%\\.ssh\\tunel_{nome}"

REM Escrever chave privada (base64 decodificado via PowerShell)
set "CHAVE_FILE=%USERPROFILE%\\.ssh\\tunel_{nome}\\id_ed25519"
powershell -NoProfile -Command "[IO.File]::WriteAllBytes($env:CHAVE_FILE, [Convert]::FromBase64String('{chave_b64}'))"

echo Chave privada configurada
echo.
echo Conectando...
echo Pressione Ctrl+C para desconectar
echo.

:conectar
echo Conectado ao tunel...
ssh -o StrictHostKeyChecking=no ^
    -o BatchMode=yes ^
    -o ServerAliveInterval=30 ^
    -o ServerAliveCountMax=3 ^
    -i "%USERPROFILE%\\.ssh\\tunel_{nome}\\id_ed25519" ^
    -R %PORTA_REMOTA%:127.0.0.1:%PORTA_LOCAL% ^
    %USUARIO%@%SERVIDOR% -N

echo.
echo ========================================
echo    ATENCAO: Conexao caiu!
echo ========================================
echo Reconectando em 5 segundos...
timeout /t 5 /nobreak >nul
goto conectar
'''
            with open(caminho_bat, "w", encoding="utf-8") as f:
                f.write(conteudo_bat)

        print(f"✅ Script gerado: {caminho}")
        if info.get('tipo') == 'windows':
            print(f"✅ Script Windows gerado: {caminho_bat}")

    def _editar_tunel(self):
        """Edita um cliente existente"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n⚪ Nenhum cliente configurado.")
            return

        nome = self._escolher_tunel("✏️ Editar cliente", tuneis)
        if not nome:
            return

        info = tuneis[nome]
        print(f"\nEditando cliente: {nome}")
        print(f"  IP do servidor: {info['servidor']}")
        print(f"  Porta remota atual: {info['porta_remota']}")
        print(f"  Porta local atual: {info['porta_local']}")
        print(f"  Tipo: {info['tipo']}")

        info_original = dict(info)

        servidor_input = input(f"\n🌐 IP do servidor [{info['servidor']}] (Enter para manter): ").strip()
        if servidor_input:
            info['servidor'] = servidor_input
            print(f"   ✅ Alterado: {servidor_input}")
        else:
            print(f"   ✅ Mantido: {info['servidor']}")

        porta_remota_antiga = info['porta_remota']
        porta_local_antiga = info['porta_local']
        tipo_antigo = info['tipo']

        porta_remota_input = input(f"\n Porta remota [{info['porta_remota']}] (Enter para manter, 'auto' para automático): ").strip()
        if porta_remota_input:
            if porta_remota_input.lower() == 'auto':
                print("\n Buscando porta livre na faixa 40450-40500...")
                tuneis_todos = self._carregar_tuneis()
                portas_em_uso_json = {v['porta_remota'] for k, v in tuneis_todos.items() if k != nome}
                nova_porta = None

                for porta_teste in range(40450, 40501):
                    if porta_teste in portas_em_uso_json:
                        continue
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            if s.connect_ex(('localhost', porta_teste)) == 0:
                                continue
                    except Exception:
                        pass
                    nova_porta = porta_teste
                    break

                if nova_porta is None:
                    print("❌ Nenhuma porta livre encontrada na faixa 40450-40500.")
                    return

                info['porta_remota'] = nova_porta
                print(f"✅ Porta {nova_porta} encontrada!")
            elif porta_remota_input.isdigit():
                info['porta_remota'] = int(porta_remota_input)
                print(f"   ✅ Alterado: {porta_remota_input}")
        else:
            print(f"   ✅ Mantido: {info['porta_remota']}")

        porta_local_input = input(f"\n🏠 Porta local [{info['porta_local']}] (Enter para manter): ").strip()
        if porta_local_input:
            if not porta_local_input.isdigit():
                print("❌ Porta local inválida.")
                return
            info['porta_local'] = int(porta_local_input)
            print(f"   ✅ Alterado: {porta_local_input}")
        else:
            print(f"   ✅ Mantido: {info['porta_local']}")

        print(f"\n🖥️ Tipo da máquina remota:")
        print(f"  [1] Windows (atual: {info['tipo']})")
        print(f"  [2] Linux")
        tipo_choice = input("  Escolha (Enter para manter): ").strip()
        if tipo_choice == "2":
            info['tipo'] = "linux"
            print(f"   ✅ Alterado: linux")
        elif tipo_choice == "1":
            info['tipo'] = "windows"
            print(f"   ✅ Alterado: windows")
        else:
            print(f"   ✅ Mantido: {info['tipo']}")

        tuneis[nome] = info
        self._salvar_tuneis(tuneis)
        self._log_tunel(nome, f"Cliente editado: porta {info['porta_remota']} -> {info['porta_local']} ({info['tipo']})")

        if info['porta_remota'] != porta_remota_antiga:
            print(f"\n Abrindo firewall na porta {info['porta_remota']}...")
            self._abrir_porta_firewall(info['porta_remota'])
            print(f" Fechando firewall na porta {porta_remota_antiga}...")
            self._fechar_porta_firewall(porta_remota_antiga)

        algo_mudou = (
            info['porta_remota'] != porta_remota_antiga or
            info['porta_local'] != porta_local_antiga or
            info['servidor'] != info_original['servidor'] or
            info['tipo'] != tipo_antigo or
            info.get('chave_privada')
        )
        if algo_mudou:
            print("\n Regenerando scripts...")
            self._gerar_scripts_tunel(nome)

        print(f"\n✅ Cliente '{nome}' editado com sucesso!")

    def _excluir_tunel(self):
        """Remove um cliente e todos os arquivos associados"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n Nenhum cliente configurado.")
            return

        nome = self._escolher_tunel(" Excluir cliente", tuneis)
        if not nome:
            return

        confirmar = input(f"\n Tem certeza que deseja excluir '{nome}'? (s/n): ").strip().lower()
        if confirmar != "s":
            print("Operação cancelada.")
            return

        info = tuneis.get(nome, {})
        chave_path = info.get('chave_privada')
        if chave_path and os.path.exists(chave_path):
            os.remove(chave_path)
            print(f"  Chave privada removida: {chave_path}")
        if chave_path and os.path.exists(f"{chave_path}.pub"):
            os.remove(f"{chave_path}.pub")

        del tuneis[nome]
        self._salvar_tuneis(tuneis)

        script_path = f"{self.install_principal}/tuneis/scripts/{nome}.bat"
        script_path_sh = f"{self.install_principal}/tuneis/scripts/{nome}.sh"
        if os.path.exists(script_path):
            os.remove(script_path)
        if os.path.exists(script_path_sh):
            os.remove(script_path_sh)

        log_file = f"{self.install_principal}/tuneis/logs/{nome}.log"
        if os.path.exists(log_file):
            os.remove(log_file)

        if chave_path:
            chave_pub_path = f"{chave_path}.pub"
            if os.path.exists(chave_pub_path):
                try:
                    with open(chave_pub_path, 'r') as f:
                        chave_pub = f.read().strip()
                    auth_keys = os.path.expanduser("~/.ssh/authorized_keys")
                    if os.path.exists(auth_keys):
                        with open(auth_keys, 'r') as f:
                            lines = f.readlines()
                        with open(auth_keys, 'w') as f:
                            for line in lines:
                                if chave_pub not in line:
                                    f.write(line)
                        print("  Chave pública removida do authorized_keys")
                except Exception:
                    pass

        self._log_tunel(nome, "Cliente excluído")

        porta_excluida = info.get('porta_remota')
        if porta_excluida:
            print(f"\n🔒 Removendo firewall da porta {porta_excluida}...")
            self._fechar_porta_firewall(porta_excluida)

        print(f"\n Cliente '{nome}' excluído com sucesso!")

    def _visualizar_tuneis(self):
        """Visualiza todos os clientes com detalhes completos"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n Nenhum cliente configurado.")
            return

        ativos = self._tuneis_ativos()

        print("\n" + "=" * 65)
        print("📋 CLIENTES CONFIGURADOS")
        print("=" * 65)

        for nome, info in tuneis.items():
            status = "🟢 ATIVO" if nome in ativos else "🔴 INATIVO"
            print(f"\n  {status} | {nome}")
            print(f"    Porta remota: {info['porta_remota']}")
            print(f"    Porta local:  {info['porta_local']}")
            print(f"    Usuário:      {info['usuario']}")
            print(f"    Servidor:     {info['servidor']}")
            print(f"    Tipo:         {info['tipo']}")
            print(f"    Criado em:    {info.get('criado_em', 'N/A')}")

            bat = f"{self.install_principal}/tuneis/scripts/{nome}.bat"
            sh = f"{self.install_principal}/tuneis/scripts/{nome}.sh"
            scripts = []
            if os.path.exists(bat):
                scripts.append("🪟 .bat")
            if os.path.exists(sh):
                scripts.append("🐧 .sh")
            if scripts:
                print(f"    Scripts:      {', '.join(scripts)}")
            else:
                print(f"    Scripts:      ⚪ Nenhum gerado")

        print(f"\n📊 Total: {len(tuneis)} configurados, {len(ativos)} ativos")

    def _script_cliente(self):
        """Gera e exibe o script na tela"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n⚪ Nenhum túnel configurado. Crie um primeiro.")
            return

        nome = self._escolher_tunel("Gerar/Visualizar script", tuneis)
        if not nome:
            return

        info = tuneis[nome]
        chave_privada = info.get('chave_privada', os.path.expanduser(f"~/.ssh/id_ed25519_{nome}"))

        if not os.path.exists(chave_privada):
            print(f"\n❌ Chave privada não encontrada: {chave_privada}")
            print("   Regenerando chave...")
            ssh_dir = os.path.expanduser("~/.ssh")
            os.makedirs(ssh_dir, exist_ok=True)
            result = subprocess.run(
                ["ssh-keygen", "-t", "ed25519", "-N", "", "-f", chave_privada,
                 "-C", f"tunel-{nome}@{info['servidor']}"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"❌ Falha ao gerar chave: {result.stderr.strip()}")
                return
            print("✅ Nova chave gerada!")

            auth_keys = os.path.join(ssh_dir, "authorized_keys")
            try:
                with open(f"{chave_privada}.pub", 'r') as f:
                    chave_pub_content = f.read().strip()
                existente = False
                if os.path.exists(auth_keys):
                    with open(auth_keys, 'r') as f:
                        existente = chave_pub_content in f.read()
                if not existente:
                    with open(auth_keys, 'a') as f:
                        f.write(chave_pub_content + "\n")
                    print("✅ Chave pública adicionada ao authorized_keys")
            except Exception as e:
                print(f"⚠️ Falha ao adicionar chave pública: {e}")

            info['chave_privada'] = chave_privada
            self._salvar_tuneis(tuneis)

        self._gerar_script_completo(nome, chave_privada)

        scripts_dir = f"{self.install_principal}/tuneis/scripts"
        scripts = []
        if os.path.exists(f"{scripts_dir}/{nome}.sh"):
            scripts.append(f"{nome}.sh")
        if os.path.exists(f"{scripts_dir}/{nome}.bat"):
            scripts.append(f"{nome}.bat")

        if not scripts:
            print("\n Nenhum script foi gerado.")
            return

        print("\n📋 Scripts gerados:")
        for i, script in enumerate(scripts, 1):
            tipo = "🪟 Windows" if script.endswith('.bat') else "🐧 Linux"
            print(f"  [{i}] {script} ({tipo})")

        escolha = input("\nNúmero do script para visualizar (0 para cancelar): ").strip()
        if escolha == "0" or not escolha:
            return

        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(scripts):
                caminho = os.path.join(scripts_dir, scripts[idx])
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                print("\n" + "=" * 55)
                print(f"📄 {scripts[idx]}")
                print("=" * 55)
                print(conteudo)
                print("=" * 55)
            else:
                print("❌ Número inválido.")
        except ValueError:
            print("❌ Entrada inválida.")

        input("\nPressione Enter para continuar...")

    def _gerenciar_portas(self):
        """Gerencia abertura/fechamento de portas dos túneis no firewall"""
        tuneis = self._carregar_tuneis()
        if not tuneis:
            print("\n⚪ Nenhum túnel configurado.")
            return

        print("\n" + "=" * 55)
        print("🔓 GERENCIAR PORTAS DOS TÚNEIS")
        print("=" * 55)

        print("\n Status atual das portas:\n")

        lista_nomes = list(tuneis.keys())
        portas_abertas = []

        for i, nome in enumerate(lista_nomes, 1):
            info = tuneis[nome]
            porta = info['porta_remota']

            check_result = subprocess.run(
                ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                capture_output=True
            )

            if check_result.returncode == 0:
                status = "✅ ABERTA"
                portas_abertas.append(nome)
            else:
                status = "🔒 FECHADA"

            tipo = "🪟 Windows" if info.get('tipo') == 'windows' else "🐧 Linux"
            print(f"  [{i}] {nome} - Porta {porta} - {status} ({tipo})")

        print("\n" + "-" * 55)
        print("[1-{}] Escolher cliente para alterar".format(len(lista_nomes)))
        print("[A] Abrir TODAS as portas")
        print("[F] Fechar TODAS as portas")
        print("[0] Voltar")
        print("=" * 55)

        escolha = input("\nEscolha: ").strip().lower()

        if escolha == "0":
            return

        if escolha == "a":
            print("\n🔓 Abrindo TODAS as portas...\n")
            for nome in lista_nomes:
                info = tuneis[nome]
                print(f"  {nome} (porta {info['porta_remota']}):")
                self._abrir_porta_firewall(info['porta_remota'])
                print()
            print("✅ Todas as portas foram abertas!")
            self._log_tunel("sistema", "Todas as portas abertas via gerenciador")
            input("\nPressione Enter para continuar...")
            return

        if escolha == "f":
            print("\n Fechando TODAS as portas...\n")
            for nome in lista_nomes:
                info = tuneis[nome]
                print(f"  {nome} (porta {info['porta_remota']}):")
                self._fechar_porta_firewall(info['porta_remota'])
                print()
            print("✅ Todas as portas foram fechadas!")
            self._log_tunel("sistema", "Todas as portas fechadas via gerenciador")
            input("\nPressione Enter para continuar...")
            return

        try:
            idx = int(escolha) - 1
            if 0 <= idx < len(lista_nomes):
                nome = lista_nomes[idx]
                info = tuneis[nome]
                porta = info['porta_remota']

                check_result = subprocess.run(
                    ["sudo", "iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(porta), "-j", "ACCEPT"],
                    capture_output=True
                )
                esta_aberta = check_result.returncode == 0

                print(f"\n📋 Cliente: {nome}")
                print(f"   Porta: {porta}")
                print(f"   Status: {'✅ ABERTA' if esta_aberta else ' FECHADA'}")

                if esta_aberta:
                    confirmar = input(f"\nDeseja FECHAR a porta {porta}? (s/n): ").strip().lower()
                    if confirmar == "s":
                        print(f"\n🔒 Fechando porta {porta}...")
                        self._fechar_porta_firewall(porta)
                        print(f"\n✅ Porta {porta} fechada com sucesso!")
                        self._log_tunel(nome, f"Porta {porta} fechada via gerenciador")
                else:
                    confirmar = input(f"\nDeseja ABRIR a porta {porta}? (s/n): ").strip().lower()
                    if confirmar == "s":
                        print(f"\n🔓 Abrindo porta {porta}...")
                        self._abrir_porta_firewall(porta)
                        print(f"\n✅ Porta {porta} aberta com sucesso!")
                        self._log_tunel(nome, f"Porta {porta} aberta via gerenciador")
            else:
                print("❌ Número inválido.")
        except ValueError:
            print("❌ Entrada inválida.")

        input("\nPressione Enter para continuar...")

    def _configurar_ssh_server_silencioso(self):
        """Configura sshd_config para aceitar túneis reversos (GatewayPorts).
        Retorna True se configurado com sucesso, False caso contrário."""
        sshd = "/etc/ssh/sshd_config"

        check = subprocess.run(
            "grep -q '^GatewayPorts yes' " + sshd,
            shell=True, capture_output=True
        )
        if check.returncode == 0:
            return True

        subprocess.run(
            ["sudo", "cp", sshd, sshd + ".bak.tuneis"],
            capture_output=True
        )

        subprocess.run(
            r"sudo sed -i 's/^#\?GatewayPorts.*/GatewayPorts yes/' " + sshd,
            shell=True, capture_output=True
        )

        check2 = subprocess.run(
            "grep -q '^GatewayPorts' " + sshd,
            shell=True, capture_output=True
        )
        if check2.returncode != 0:
            subprocess.run(
                "echo 'GatewayPorts yes' | sudo tee -a " + sshd,
                shell=True, capture_output=True
            )

        validacao = subprocess.run(
            "sudo sshd -t", shell=True, capture_output=True, text=True
        )
        if validacao.returncode != 0:
            subprocess.run(
                ["sudo", "cp", sshd + ".bak.tuneis", sshd],
                capture_output=True
            )
            return False

        reiniciado = False
        for servico in ["ssh", "sshd"]:
            r = subprocess.run(
                ["sudo", "systemctl", "restart", servico],
                capture_output=True
            )
            if r.returncode == 0:
                reiniciado = True
                break

        return reiniciado
