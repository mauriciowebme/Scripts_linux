# Tarefa: Permitir execução do install_master.py sem usuário root

## Objetivo
Permitir que o script `install_master.py` seja executado por um usuário comum (não-root), utilizando `sudo` apenas quando necessário para comandos privilegiados, mantendo todas as funcionalidades originais.

## Contexto
O usuário relatou: "naão consigo rodar o scriotpt se não for como root, pode me ajudar? sem pretder minhas funionalidades".
Atualmente, o script tenta criar o diretório `/install_principal` diretamente e executa comandos como `timedatectl` e `ln -sf /etc/localtime` sem `sudo`, o que causa falhas para usuários comuns.

## Plano de Implementação

### 1. Análise e Preparação
- [x] Analisar o início do script (`check_for_update`) para identificar bloqueios de permissão.
- [x] Identificar comandos de sistema que requerem privilégios elevados.

### 2. Implementação de Correções
- [x] Criar função auxiliar `garantir_diretorio_principal()` que:
    - Verifica se `/install_principal` existe.
    - Se não existir, tenta criar com `sudo mkdir`.
    - Ajusta permissões (owner) para o usuário atual com `sudo chown` para permitir escrita sem sudo subsequente.
- [x] Refatorar `check_for_update` para usar essa função.
- [x] Adicionar `sudo` aos comandos `timedatectl` e `ln` dentro de `check_for_update`.
- [x] Verificar e ajustar a classe `Docker` para garantir consistência no uso de `/install_principal`.

### 3. Validação
- [x] Verificar se a sintaxe do `subprocess` está correta.
- [x] Garantir que o script continue funcional para root (onde sudo é redundante mas aceitável ou desnecessário).

## Notas
- Manter o diretório hardcoded ( `/install_principal`) conforme padrão do script, mas garantindo acesso.
