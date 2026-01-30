# Task: Mover informações para dentro do cabeçalho do menu

## Status
- [x] Ocultar banner inicial (passar a ser simples no início).
- [x] Integrar informações do banner (Versão, Comando, IP) dentro do cabeçalho do menu paginado.
- [x] Ajustar layout dentro da função `mostrar_menu_paginado`.

## Contexto
O usuário solicitou que as informações de versão, comando de execução e IP do servidor sejam exibidas DENTRO da moldura do menu principal, logo abaixo do título, para ficar mais organizado e visível.

## Alterações
- Modificado `c:\DESENVOLVIMENTO\Scripts_linux\install_master.py`:
    - Simplificar `banner` em `main`.
    - Ajustar `mostrar_menu_paginado` para renderizar `mensagem_topo` dentro do bloco do cabeçalho.
