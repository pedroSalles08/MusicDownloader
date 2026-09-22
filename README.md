# Music Downloader

Aplicativo desktop Windows para pesquisar, revisar e baixar músicas e vídeos
em formatos selecionáveis, desde que o usuário possua o conteúdo ou tenha
autorização para baixá-lo. O backend usa yt-dlp e FFmpeg; a interface é feita
com PySide6.

> Estado atual: versão Windows `onedir` gerada, validada e aprovada pelo QA
> final. A suíte usa serviços fake; uma validação manual separada exercita
> yt-dlp e FFmpeg reais sem conservar a mídia temporária.

## Baixar para Windows

Baixe o instalador mais recente em
[`MusicDownloader-Setup`](https://github.com/pedroSalles08/MusicDownloader/releases/latest).
O instalador é destinado ao Windows 10/11 de 64 bits, não exige privilégios de
administrador e registra **Music Downloader** no Menu Iniciar. Depois da
instalação, basta pesquisar por `Music Downloader` na barra de pesquisa do
Windows para abrir o aplicativo.

O arquivo `MusicDownloader-<versão>-portable.zip` da mesma página funciona sem
instalação, mas não cria o atalho pesquisável. Os hashes SHA-256 dos dois
pacotes estão em `SHA256SUMS.txt`. Como os binários ainda não têm assinatura de
código, o Windows SmartScreen pode exibir um aviso na primeira execução.

## Funcionalidades entregues

- lista mista de músicas, vídeos e playlists do YouTube separada por `;`;
- importação de CSV do Spotify/Exportify;
- pesquisa por nome, resolução exata de vídeos do YouTube e expansão de playlists;
- edição, nova pesquisa e seleção por item;
- download em múltiplos formatos de áudio (MP3, M4A, Opus, AAC, Vorbis, FLAC, ALAC, WAV) e vídeo (MP4 compatível, MP4 rápido, WebM, Original) com limites de bitrate/resolução;
- progresso, cancelamento e resumo de downloads com métricas e detalhes técnicos recolhidos;
- autenticação anti-bot opcional com a sessão local do Firefox, Chrome, Edge,
  Brave, Vivaldi ou Opera;
- componentes EJS empacotados para resolver os desafios JavaScript atuais do
  YouTube e recuperar formatos de áudio;
- interface dark progressiva “Midnight Deck”, com etapa atual, botões
  autoexplicativos e comportamento nativo do Windows;
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

Se o YouTube pedir para confirmar que você não é um robô, escolha em
`Sessão YouTube` o navegador no qual você já está conectado ao YouTube e
inicie o download novamente. O navegador padrão do Windows é pré-selecionado
quando é compatível. O yt-dlp lê os cookies localmente; o aplicativo não os
exibe nem os transforma em argumentos de shell. Se a sessão não puder ser
lida, feche o navegador ou escolha outro perfil/navegador em que haja login.
Use uma conta somente quando necessário e respeite os limites do YouTube.

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
são obrigatórios no `PATH`; Node executa os desafios JavaScript do YouTube com
os scripts `yt-dlp-ejs` incluídos na distribuição, e aria2c é opcional. A
distribuição possui instalador por usuário, atalho pesquisável no Menu Iniciar
e pacote portátil. Os binários ainda não possuem assinatura de código.

Para gerar ambos localmente, instale o Inno Setup 6 e execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\packaging\build_release.ps1
```

O resultado fica em `release\`: instalador, pacote portátil e hashes SHA-256.

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
- pesquisa de um resultado por nome, resolução de links exatos e expansão de
  playlists do YouTube, sem download durante a revisão e com falhas isoladas;
- download por URL já aprovada, MP3 192 kbps, metadados, capa opcional,
  cookies opcionais do navegador, retries, progresso e cancelamento
  cooperativo;
- interface PySide6 em pt-BR com fluxo Adicionar → Pesquisar → Revisar →
  Baixar → Concluído, importação, fallback Spotify, revisão editável, seleção,
  progresso, logs recolhíveis, cancelamento e resumo;
- workers `QThread` que mantêm operações longas fora da thread da interface.

### Perfis de mídia

O backend também possui perfis validados para áudio AAC, ALAC, FLAC, M4A, MP3,
Opus, Vorbis e WAV e para vídeo MP4 compatível, MP4 rápido, WebM e original.
Bitrates e resoluções vêm de listas fechadas. A interface permite escolher
esses perfis no popover de opções e mantém MP3 192 kbps como padrão.

O visual e seus tokens estão documentados em `DESIGN_SYSTEM.md`. A execução por
Python e pelo pacote `onedir` foi validada no Windows.

## Pré-requisitos e limitações atuais

- Windows 10/11;
- Python 3.11 ou posterior para desenvolvimento;
- FFmpeg e FFprobe no PATH;
- Node no PATH para o suporte JavaScript atual do YouTube no yt-dlp;
- aria2c opcional.

yt-dlp com seu grupo de dependências `default` — incluindo `yt-dlp-ejs` — e
PySide6 são dependências de runtime; PyInstaller é dependência de desenvolvimento. Os testes automatizados não acessam a rede nem executam
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
