# Music Downloader

Aplicativo desktop Windows em construção para pesquisar, revisar e baixar em MP3 músicas que o usuário possua ou tenha autorização para baixar. O backend usa yt-dlp e FFmpeg; a interface será feita com PySide6.

> Estado atual: núcleo de entradas implementado e testado. A interface, pesquisa,
> download e executável ainda não foram implementados.

## MVP planejado

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

O pacote `music_downloader` já oferece:

- parser de lista separada por `;`, com trim e deduplicação Unicode estável;
- importador CSV Exportify com diagnóstico de linhas inválidas; para recuperar
  após aspas malformadas, cada linha física é um registro e campos CSV
  multilinha são rejeitados;
- detecção de URL pública de playlist do Spotify;
- saneamento de componentes de nome de arquivo para Windows, limitado por
  unidades UTF-16 sem cortar caracteres suplementares;
- detecção injetável de FFmpeg e FFprobe.

Essas APIs formam o núcleo de domínio e ainda não constituem um aplicativo
executável para o usuário final.

## Pré-requisitos previstos para o aplicativo completo

- Windows 10/11;
- Python 3.11 ou posterior para desenvolvimento;
- FFmpeg e FFprobe no PATH;
- Node no PATH para o suporte JavaScript atual do YouTube no yt-dlp;
- aria2c opcional.

PySide6, yt-dlp e PyInstaller serão adicionados nas etapas que implementarem a
interface, os serviços e o empacotamento. Nenhum download de rede faz parte da
etapa atual.

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
