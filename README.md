# Install Master

> CLI interativo de automação e gerenciamento de servidor Linux (Ubuntu)

![Version](https://img.shields.io/badge/version-1.235-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Ubuntu](https://img.shields.io/badge/ubuntu-20.04+-orange)
![License](https://img.shields.io/badge/license-MIT-purple)

## Requisitos

- Ubuntu 20.04 ou superior
- Python 3.10+
- Acesso root/sudo

## Instalação

```bash
# Clone o repositório
git clone https://github.com/mauriciowebme/Scripts_linux.git
cd Scripts_linux

# Execute o instalador
python3 install_master.py
```

Após a primeira execução, você pode usar o comando global:

```bash
install_master
```

## Estrutura do Projeto

```
Scripts_linux/
├── install_master.py              # Ponto de entrada
├── install_master/
│   ├── __main__.py                # Classe principal Sistema e menus
│   ├── config.py                  # Configurações globais
│   ├── core/                      # Núcleo do sistema
│   │   ├── docker_base.py         # Operações Docker base
│   │   ├── shell.py               # Execução de comandos shell
│   │   ├── system_utils.py        # Utilitários do sistema
│   │   └── deps.py                # Gerenciamento de dependências
│   ├── docker/                    # Módulos Docker
│   │   ├── databases/             # PostgreSQL, MySQL
│   │   ├── tools/                 # 19 ferramentas (n8n, Portainer, Redis, etc.)
│   │   ├── vms/                   # VMs (Windows KVM, Ubuntu, Webtop, Nextcloud)
│   │   ├── web/                   # Traefik, WordPress, OpenLiteSpeed, NodeJS
│   │   └── management/            # Instalação Docker, CRUD containers, FRP
│   └── system/                    # Configurações do sistema
│       ├── base.py                # Mixin base e menus
│       ├── network.py             # Configurações de rede
│       ├── wireguard.py           # VPN WireGuard
│       ├── tunnels.py             # Túneis SSH
│       ├── partitions.py          # Gerenciamento de partições
│       ├── diagnostic.py          # Diagnósticos do sistema
│       ├── ollama.py              # IA local (Ollama)
│       └── updates.py             # Atualizações do sistema
└── .gitignore
```

## Funcionalidades

### Docker e Containers
- **Gerenciamento completo**: listar, iniciar, parar, reiniciar, excluir containers
- **Bancos de dados**: PostgreSQL, MySQL
- **Web servers**: Traefik (reverse proxy), WordPress, OpenLiteSpeed, NodeJS
- **Ferramentas**: Portainer, FileBrowser, n8n (automação), Redis, SFTP, Rustdesk
- **Monitoramento**: Grafana, Prometheus, Node Exporter
- **IA**: Open WebUI, Ollama (local)
- **Comunicação**: Evolution API (WhatsApp), WAHA
- **Automação**: Selenium, Browserless (Chromium headless)
- **Backup/Sync**: Rclone, sincronização de pastas com Rsync

### VMs e Ambientes
- **Windows KVM**: Windows em container Docker
- **Ubuntu Container**: Ambiente Ubuntu isolado
- **Webtop**: Desktop Ubuntu via navegador
- **Nextcloud**: Cloud pessoal
- **Sistema CISO**: Ambiente especializado de segurança

### Sistema Operacional
- **Rede**: configuração de IP fixo (Netplan), WiFi (nmtui), SSH
- **SSH completo**: alterar porta, gerar chaves ED25519, autenticação por chave, login por senha
- **VPN**: WireGuard (servidor/cliente/peers), Cloudflare WARP, Pritunl
- **Túneis SSH**: gerenciador completo com geração automática de scripts (.sh/.bat), firewall, reconexão automática
- **Partições**: criar, formatar, montar/desmontar, fstab
- **RAID**: gerenciamento completo (estado, expansão, redução, BIOS/UEFI)
- **Swap**: criar, redimensionar, remover, ajustar swappiness
- **Permissões**: gerenciamento de permissões de arquivos/pastas
- **Diagnósticos**: temperatura (lm-sensors), velocidade internet (speedtest), espaço em disco, Glances
- **Monitor de rede**: vnstat (estatísticas mensais)
- **Atualizações**: apt update/upgrade/full-upgrade, limpeza de pacotes
- **Interfaces gráficas**: XFCE, GNOME, VNC Server (TigerVNC)
- **Serviços**: configurar inicialização automática (systemd), fechar tampa de notebook

### Ferramentas Adicionais
- **Editores de código**: VSCode oficial, OpenVSCode Server
- **Terminal web**: ttyd (Terminal sobre HTTP) com gerenciamento completo
- **Terminal mobile**: Termote PWA (Progressive Web App)
- **FRP**: reverse proxy para expor serviços locais
- **OpenCode**: CLI de IA para desenvolvimento
- **Open Claw**: automação e agentes (instalação, configuração, chat TUI)
- **Comandos Linux**: referência completa de comandos essenciais

## Arquitetura

### Padrão de Design
O projeto utiliza **Mixin Composition** via herança múltipla. A classe principal `Sistema` herda de ~40+ mixins, cada um responsável por uma funcionalidade específica.

### Configurações
- **Diretório base**: `/install_principal`
- **Redes Docker**: `_traefik`, `interno`
- **Banco de dados**: `/install_principal/bds`

### Dependências
Instaladas automaticamente via APT com fallback para pip:
- `mysql-connector-python`
- `PyYAML`
- `glances[web]`

## Uso

O sistema apresenta um menu interativo paginado com:
- **Navegação**: `n` (próxima), `p` (anterior)
- **Busca**: `/palavra` (filtrar itens)
- **Limpar filtro**: `c`
- **Seleção**: número do item ou `0` para sair

### Menus Principais
1. **Reiniciar/Desligar**
2. **Atualizar o sistema** (update, upgrade, full-upgrade, limpeza)
3. **Central de Instalações** (Docker, Ollama, interfaces gráficas, editores, Cloudflare WARP)
4. **Gerenciar Microserviços** (túneis SSH, FRP, SFTP, Traefik, monitoramento, PostgreSQL)
5. **Configurações do Sistema** (rede, SSH, partições, RAID, swap, WireGuard, serviços)
6. **Diagnóstico e Monitoramento** (temperatura, velocidade, espaço, Glances, vnstat)
7. **Comandos essenciais do Linux** (referência completa)

### Funcionalidades Destacadas

#### Gerenciador de Túneis SSH
- Criação automática de chaves ED25519
- Geração de scripts cliente (.sh para Linux, .bat para Windows)
- Configuração automática de firewall (UFW + iptables)
- Suporte a reconexão automática (autossh)
- Gerenciamento de múltiplos túneis com portas dedicadas

#### VPN WireGuard
- Instalação automática
- Geração de chaves pública/privada
- Configuração como servidor ou cliente
- Adição dinâmica de peers
- Assistente de configuração interativo

#### Gerenciamento de RAID
- Suporte a BIOS (Legacy) e UEFI
- Expansão e redução de RAID
- Formatação e adição de discos ao RAID
- Monitoramento em tempo real

#### Configuração SSH Completa
- Alteração de porta SSH
- Geração de chaves ED25519 para root
- Desabilitar/habilitar login por senha
- Configuração de autenticação por chave

## Contribuindo

Contribuições são bem-vindas! Abra uma issue ou pull request no [GitHub](https://github.com/mauriciowebme/Scripts_linux).

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

## Autor

**mauriciowebme**  
GitHub: [@mauriciowebme](https://github.com/mauriciowebme)

---

**Nota**: Este sistema é destinado a servidores Ubuntu. Execute com cuidado e certifique-se de entender as operações antes de executá-las em ambientes de produção.
