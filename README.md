# Music Downloader

Aplicativo desktop Windows para pesquisar, revisar e baixar em MP3 músicas que
o usuário possua ou tenha autorização para baixar. O backend usa yt-dlp e
FFmpeg; a interface é feita com PySide6.

> Estado atual: versão Windows `onedir` gerada, validada e aprovada pelo QA
> final. A suíte usa serviços fake; uma validação manual separada exercita
> yt-dlp e FFmpeg reais sem conservar a mídia temporária.

## Funcionalidades entregues

- lista de músicas separada por `;`;
- importação de CSV do Spotify/Exportify;
- pesquisa e revisão de resultados do YouTube;
- edição, nova pesquisa e seleção por item;
- download MP3 com progresso, cancelamento e resumo;
- interface retrô organizada;
- executável para Windows.

Links públicos do Spotify serão reconhecidos, mas a importação direta não faz parte do MVP; o aplicativo orientará o uso de Exportify e CSV.

## Desenvolvimento

Pré-requisito atual: Python 3.11 ou posterior. No PowerShell, crie o ambiente,
instale o pacote editável com as dependências de teste e execute a suíte:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

Para abrir o aplicativo ou executar apenas o smoke-test sem rede:

```powershell
.\.venv\Scripts\python.exe -m music_downloader
.\.venv\Scripts\python.exe -m music_downloader --smoke-test
```

## Build do aplicativo Windows

O build reproduzível usa o arquivo `MusicDownloader.spec`. Este comando cria o
ambiente quando necessário, instala as dependências de desenvolvimento, limpa
o estado de trabalho do PyInstaller e gera uma distribuição `onedir`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\packaging\build.ps1
```

Se o ambiente já estiver sincronizado, use `-SkipInstall`. O executável fica em
`dist\MusicDownloader\MusicDownloader.exe`; distribua a pasta
`dist\MusicDownloader` inteira, não apenas o `.exe`.

FFmpeg, FFprobe, Node e aria2c não são incorporados ao pacote. FFmpeg e FFprobe
são obrigatórios no `PATH`; Node melhora a compatibilidade atual do YouTube e
aria2c é opcional. A distribuição ainda não possui instalador nem assinatura
de código.

Para repetir a validação real controlada:

```powershell
.\.venv\Scripts\python.exe .\packaging\manual_validation.py
```

O script só baixa do YouTube quando ID e título correspondem ao vídeo público
de teste esperado. Caso contrário, gera um tom autorizado, serve-o apenas em
`localhost`, converte-o para MP3 com o mesmo serviço da aplicação e remove a
pasta temporária ao final.

O pacote `music_downloader` já oferece:

- parser de lista separada por `;`, com trim e deduplicação Unicode estável;
- importador CSV Exportify com diagnóstico de linhas inválidas; para recuperar
  após aspas malformadas, cada linha física é um registro e campos CSV
  multilinha são rejeitados;
- detecção de URL pública de playlist do Spotify;
- saneamento de componentes de nome de arquivo para Windows, limitado por
  unidades UTF-16 sem cortar caracteres suplementares;
- detecção injetável de FFmpeg e FFprobe;
- pesquisa de um resultado por query, sem download, com falhas isoladas;
- download por URL já aprovada, MP3 192 kbps, metadados, capa opcional,
  retries, progresso e cancelamento cooperativo;
- interface PySide6 em pt-BR com importação, fallback Spotify, revisão
  editável, seleção, progresso, logs, cancelamento e resumo;
- workers `QThread` que mantêm operações longas fora da thread da interface.

O visual e seus tokens estão documentados em `DESIGN_SYSTEM.md`. A execução por
Python e pelo pacote `onedir` foi validada no Windows.

## Pré-requisitos e limitações atuais

- Windows 10/11;
- Python 3.11 ou posterior para desenvolvimento;
- FFmpeg e FFprobe no PATH;
- Node no PATH para o suporte JavaScript atual do YouTube no yt-dlp;
- aria2c opcional.

yt-dlp e PySide6 são dependências de runtime; PyInstaller é dependência de
desenvolvimento. Os testes automatizados não acessam a rede nem executam
FFmpeg: ambos são substituídos por fakes nas verificações dos serviços e da
interface. Resultados do YouTube podem variar ou exigir atualização do yt-dlp;
por isso a revisão humana antes do download permanece obrigatória.

## Referências do repositório

- `promptMestre.md`: requisitos completos.
- `contextScriptMusicas.md`: histórico e decisões do script anterior.
- `csv-example.csv`: amostra real do Exportify.
- `UI-inspirations-design.png`: direção visual.
- `PRODUCT.md`: escopo do produto.
- `PLAN.md`: sequência de execução.
- `STATUS.md`: estado verificado.
- `QUALITY_GATE.md`: condições de aprovação.
- `DECISIONS.md`: decisões arquiteturais.

## Uso responsável

O projeto não se destina a contornar DRM nem a baixar conteúdo sem autorização. O usuário é responsável por respeitar direitos autorais, termos dos serviços e legislação aplicável.
