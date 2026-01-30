---
trigger: always_on
---

# Diretrizes Primárias
## 1. Idioma e Localização
- **Regra Absoluta**: Todo o output (respostas, documentação, mensagens de commit, artefatos) DEVE ser em **Português do Brasil (pt-BR)**.

## 2. Protocolo de Commit
- **Padrão**: Utilize estritamente **Conventional Commits**.
- **Contexto de Build**:
  - Priorize SEMPRE o que está em **stage (staged)** para criar a mensagem.
  - Se necessário, leia os arquivos não preparados para entender o contexto, mas a mensagem deve descrever fielmente **o que será comitado (staged)**.

### Tipos de Commit Permitidos
- `feat`: Nova funcionalidade ou recurso para o sistema.
- `fix`: Correção de bugs.
- `chore`: Manutenção de configurações, build, scripts ou ferramentas **sem impacto percebido pelo usuário final**.
- `docs`: Alterações exclusivas em documentação.
- `style`: Formatação e estilos de código (espaços, lint) sem alterar lógica.
- `refactor`: Refatoração de código que não corrige bugs nem cria features.
- `test`: Adição ou correção de testes.
- `build`: Alterações que afetam o sistema de build ou dependências.
- `ci`: Alterações em arquivos de configuração de CI.

### Regra de Classificação: feat vs chore
Use `feat` ou `fix` quando a alteração trouxer um **benefício direto ou nova capacidade** que o usuário final possa usufruir.

| Tipo | Pergunta-chave | Exemplo |
|------|----------------|---------|
| `feat` | O usuário recebe algo NOVO? | Nova página, nova integração, recurso de backend que habilita nova função. |
| `fix` | O usuário percebia algo ERRADO? | Botão que não funcionava, correção em regra de cálculo, falha funcional. |
| `chore/refactor/test/docs/build/ci/style` | O usuário NÃO nota diferença? | Ajustes internos, organização, manutenção, testes, pipelines, documentação. |

**Resumo:** Se a mudança não altera a experiência ou as capacidades do usuário, não é `feat` nem `fix`.

### Controle de Exibição no Changelog do Cliente
O sistema filtra automaticamente as atualizações para o cliente final seguindo esta lógica:
- **Funcionalidades (`feat`)** e **Correções (`fix`)**: Só aparecem para o cliente se possuírem um **escopo permitido para exibição**.
- **Escopos Permitidos para Exibição**: `frontend`, `dashboard`, `ui`, `ux`, `novidades`.
- **Exemplo**: `fix(dashboard): corrige cores` (Aparece). `fix(api): erro interno` (Oculto).

### Mensagens Amigáveis ao Cliente
- **IMPORTANTE**: Para commits que aparecem para o cliente, as mensagens DEVEM ser escritas de forma amigável, focando no benefício e evitando termos técnicos.
- **Princípio**: Escreva como se estivesse conversando com o cliente.

## 3. Documentação
- Mantenha toda a documentação (artifacts, tasks, planos) sempre atualizada e em **PT-BR**.

## 4. Segurança e Execução (CRÍTICO)
- **BLOQUEIO DE EXECUÇÃO**: Você está **PROIBIDO** de executar planos ou sequências de passos sem a permissão explícita do usuário.
- **PROIBIÇÃO DE COMMITS**: Você está **ESTRITAMENTE PROIBIDO** de realizar commits ou pushes diretamente no repositório em qualquer circunstância. Sua função é sugerir as mensagens e alterações, mas a execução do commit cabe exclusivamente ao usuário.
- **Protocolo**: Sempre apresente o plano e **AGUARDE** o comando claro de 'pode executar' antes de iniciar qualquer ação que altere o estado do projeto.
