# Diretório do script
$ScriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent

# Diretório do Git Hooks
$HooksDir = Resolve-Path -Path (Join-Path -Path $ScriptDir -ChildPath "../.git/hooks") | ForEach-Object { $_.Path }

# Verifica se o diretório .git/hooks existe
if (-Not (Test-Path -Path $HooksDir)) {
    Write-Host "Erro: O diretório .git/hooks não foi encontrado. Execute este script na raiz do repositório." -ForegroundColor Red
    exit 1
}

# Seleciona os arquivos para copiar, ignorando os scripts de cópia
$FilesToCopy = Get-ChildItem -Path "$ScriptDir" -File | Where-Object { $_.Name -notmatch "copia-hooks\.(ps1|sh)$" }

if ($FilesToCopy.Count -eq 0) {
    Write-Host "Nenhum arquivo encontrado para copiar." -ForegroundColor Red
    exit 1
}

# Copia os arquivos para o diretório .git/hooks
$FilesToCopy | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $HooksDir -Force
}

Write-Host "Hooks copiados para .git/hooks com sucesso!" -ForegroundColor Green
