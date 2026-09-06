[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$buildScript = Join-Path $PSScriptRoot "build.ps1"
$installerScript = Join-Path $PSScriptRoot "MusicDownloader.iss"
$distributionDir = Join-Path $projectRoot "dist\MusicDownloader"
$releaseDir = Join-Path $projectRoot "release"

if (-not $SkipTests) {
    if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Ambiente virtual ausente. Execute packaging\build.ps1 primeiro."
    }
    $pytestTemp = Join-Path $projectRoot ".pytest-release-$PID"
    & $venvPython -m pytest -q --basetemp $pytestTemp
    if ($LASTEXITCODE -ne 0) {
        throw "A suíte de testes falhou; a release não será criada."
    }
}

& $buildScript -SkipInstall:$SkipInstall
if ($LASTEXITCODE -ne 0) {
    throw "O build do aplicativo falhou."
}

$version = (& $venvPython -c "import sys, tomllib, pathlib; print(tomllib.loads(pathlib.Path(sys.argv[1]).read_text('utf-8'))['project']['version'])" (Join-Path $projectRoot "pyproject.toml")).Trim()
if (-not $version) {
    throw "Não foi possível determinar a versão do aplicativo."
}

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
$zipPath = Join-Path $releaseDir "MusicDownloader-$version-portable.zip"
Compress-Archive -LiteralPath $distributionDir -DestinationPath $zipPath -CompressionLevel Optimal -Force

$compilerCandidates = @(
    $env:INNO_SETUP_COMPILER,
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { $_ }
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1
if (-not $iscc) {
    $iscc = $compilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
if (-not $iscc) {
    throw "Inno Setup 6 não encontrado. Instale com: winget install --id JRSoftware.InnoSetup -e"
}

& $iscc "/DAppVersion=$version" $installerScript
if ($LASTEXITCODE -ne 0) {
    throw "A compilação do instalador falhou."
}

$installerPath = Join-Path $releaseDir "MusicDownloader-Setup-$version.exe"
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Instalador esperado não foi criado: $installerPath"
}

$assets = @($installerPath, $zipPath)
$checksumLines = foreach ($asset in $assets) {
    $hash = Get-FileHash -LiteralPath $asset -Algorithm SHA256
    "$($hash.Hash.ToLowerInvariant())  $([IO.Path]::GetFileName($asset))"
}
$checksumPath = Join-Path $releaseDir "SHA256SUMS.txt"
Set-Content -LiteralPath $checksumPath -Value $checksumLines -Encoding ascii

Write-Output "Release criada em $releaseDir"
Get-Item -LiteralPath $installerPath, $zipPath, $checksumPath | Select-Object Name, Length, LastWriteTime
