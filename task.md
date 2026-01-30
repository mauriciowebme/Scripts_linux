# Task: Ajustes finais de layout no menu

## Status
- [x] Ocultar banner inicial.
- [x] Integrar informações no cabeçalho.
- [x] Alinhar e formatar textos do banner dentro do menu.

## Contexto
O usuário solicitou melhorias visuais para que as informações de versão e instruções fiquem alinhadas corretamente dentro do quadro do menu, melhorando a estética.

## Alterações
- Modificado `c:\DESENVOLVIMENTO\Scripts_linux\install_master.py`:
    - Adicionado padding (2 espaços) para cada linha do banner no `mostrar_menu_paginado`.
    - Adicionado separador inferior após o banner para isolar do conteúdo da página.
    - Limpo string `banner` em `main` para evitar formatação manual conflitante.
