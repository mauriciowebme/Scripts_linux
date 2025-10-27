# Instruções para o Agente (AGENTS.md)

Estas instruções se aplicam a todo o repositório `Scripts_linux` e a todas as suas subpastas. Arquivos `AGENTS.md` mais profundos substituem estas regras dentro do seu próprio escopo. Instruções diretas do usuário/desenvolvedor sempre têm precedência sobre este arquivo.

### Escopo

- O foco destas regras é o trabalho do agente dentro deste projeto (ler, editar arquivos, gerar artefatos intermediários, etc.).
- Não criar artefatos temporários fora da pasta do projeto. Todo temporário deve viver exclusivamente em `./.tmp/` na raiz do repositório.
- Scripts deste repositório que rodam localmente durante o desenvolvimento devem usar `./.tmp/` para qualquer artefato transitório.

## Arquivos e Diretórios Temporários

- Permitido: criar arquivos/diretórios temporários para trabalho intermediário, scaffolding ou contextos de build.
- Limpeza obrigatória: remover todos os artefatos temporários assim que não forem mais necessários e antes de finalizar a tarefa.
- Nunca commitar: não versionar artefatos temporários nem deixá-los em caminhos persistentes do projeto.
- Local obrigatório: `./.tmp/` (na raiz do repositório). Não usar `/tmp`, `%TEMP%` ou outros diretórios fora do projeto para trabalho do agente neste repo.
- Nomenclatura: usar prefixos claros como `tmp-` ou `scripts-linux-` para evitar colisões e facilitar a limpeza.

## Padrões Recomendados

### Python

Use `./.tmp/` e context managers para garantir a limpeza:

```python
import os, tempfile

ROOT_TMP = os.path.join(os.path.dirname(__file__), ".tmp")
os.makedirs(ROOT_TMP, exist_ok=True)

# Diretório temporário sob ./.tmp (removido ao final)
with tempfile.TemporaryDirectory(dir=ROOT_TMP, prefix="tmp-") as tmpdir:
    # trabalhe dentro de tmpdir
    pass

# Arquivo temporário sob ./.tmp (remoção explícita quando delete=False)
f = tempfile.NamedTemporaryFile(delete=False, dir=ROOT_TMP, suffix=".txt", prefix="tmp-")
try:
    f.write(b"dados"); f.flush(); f.close()
    # use f.name
finally:
    try:
        os.remove(f.name)
    except FileNotFoundError:
        pass
```

### Bash / Shell

Use `./.tmp/` e `trap` para limpeza automática:

```bash
mkdir -p ./.tmp
TMPDIR=$(mktemp -d -p ./.tmp tmp-XXXXXXXX)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT INT TERM
# use "$TMPDIR" para arquivos transitórios
```

### Docker

- Ao gerar Dockerfiles ou contextos de build temporários, use `./.tmp/` e remova-os após o `docker build`.
- Evite persistir artefatos de cache de build dentro do repositório. Prefira `./.tmp/` (que é ignorado pelo Git).

## Proibido

- Não deixar arquivos temporários em diretórios versionados (a menos que sejam cobertos por `.gitignore`).
- Não deixar credenciais, variáveis de ambiente ou materiais sigilosos após o uso.
- Não manter contêineres, volumes ou redes de longa duração criados apenas para operações temporárias; remova-os ao concluir.

## Verificação e Limpeza

- Antes de concluir uma tarefa, verifique se os artefatos temporários foram deletados (incluindo `./.tmp/` quando não houver mais uso ativo).
- Se algum artefato precisar persistir (ex.: logs ou saídas por design), documente seus caminhos no código ou comentários e não os trate como temporários.
