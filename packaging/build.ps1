[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$specPath = Join-Path $projectRoot "MusicDownloader.spec"
$expectedExe = Join-Path $projectRoot "dist\MusicDownloader\MusicDownloader.exe"

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    $bootstrapPython = (Get-Command python -ErrorAction Stop).Source
    & $bootstrapPython -m venv (Join-Path $projectRoot ".venv")
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar o ambiente virtual."
    }
}

if (-not $SkipInstall) {
    & $venvPython -m pip install -e "${projectRoot}[dev]"
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao instalar as dependências de desenvolvimento."
    }
}

Push-Location $projectRoot
try {
    $originalPath = $env:Path
    try {
        # Avoid collecting unrelated DLLs exposed by developer-tool runtimes.
        $env:Path = "$env:SystemRoot\System32;$env:SystemRoot"
        & $venvPython -m PyInstaller `
            --noconfirm `
            --clean `
            --distpath (Join-Path $projectRoot "dist") `
            --workpath (Join-Path $projectRoot "build") `
            $specPath
        if ($LASTEXITCODE -ne 0) {
            throw "O PyInstaller não concluiu o build."
        }
    } finally {
        $env:Path = $originalPath
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $expectedExe -PathType Leaf)) {
    throw "Build terminou sem produzir $expectedExe"
}

Write-Output "Build concluído: $expectedExe"
