# Music Downloader

Aplicativo desktop Windows em construção para pesquisar, revisar e baixar em MP3 músicas que o usuário possua ou tenha autorização para baixar. O backend usa yt-dlp e FFmpeg; a interface será feita com PySide6.

> Estado atual: fundação e documentação. O aplicativo e o executável ainda não foram implementados.

## MVP planejado

- lista de músicas separada por `;`;
- importação de CSV do Spotify/Exportify;
- pesquisa e revisão de resultados do YouTube;
- edição, nova pesquisa e seleção por item;
- download MP3 com progresso, cancelamento e resumo;
- interface retrô organizada;
- executável para Windows.

Links públicos do Spotify serão reconhecidos, mas a importação direta não faz parte do MVP; o aplicativo orientará o uso de Exportify e CSV.

## Pré-requisitos previstos

- Windows 10/11;
- Python 3.11 ou posterior para desenvolvimento;
- FFmpeg e FFprobe no PATH;
- Node no PATH para o suporte JavaScript atual do YouTube no yt-dlp;
- aria2c opcional.

Os comandos de instalação, execução, testes e build serão adicionados assim que a estrutura Python correspondente existir e for validada.

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
