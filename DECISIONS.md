# Decisões de arquitetura

## ADR-001 — Aplicativo nativo com PySide6

**Status:** aceita.

Será usado PySide6, conforme a stack preferencial. O projeto anterior sugeria FastAPI + pywebview/React, mas isso adicionaria dois runtimes, IPC e um pipeline frontend sem necessidade para o MVP. Widgets Qt oferecem tabela, seletor de pasta, threads, sinais e empacotamento Windows em uma única aplicação Python.

## ADR-002 — Arquitetura em camadas

**Status:** aceita.

O pacote será separado em domínio/modelos, parsers, serviços yt-dlp/sistema, workers Qt e UI. Domínio e serviços não importam widgets. Isso mantém parsers e orquestração testáveis sem iniciar uma aplicação gráfica.

## ADR-003 — yt-dlp como biblioteca

**Status:** aceita.

O backend usa `yt_dlp.YoutubeDL` diretamente. Nenhuma query do usuário é interpolada em shell. A configuração do script anterior — melhor áudio, MP3 192 kbps, metadados, capa opcional, retries, fragmentos e aria2c opcional — será adaptada, não simplesmente copiada.

## ADR-004 — Pesquisa antes do download

**Status:** aceita.

Cada query usa pesquisa sem download para formar um resultado revisável. O download posterior usa a URL/ID aprovada, evitando repetir uma busca ambígua e possivelmente escolher outro vídeo.

## ADR-005 — Concorrência e cancelamento

**Status:** aceita.

Operações longas rodam fora da thread de UI. O cancelamento é cooperativo por token/evento verificado entre itens e nos hooks de progresso. O lote isola falhas por música. A concorrência inicial será conservadora para reduzir throttling e simplificar estados.

## ADR-006 — CSV como integração Spotify do MVP

**Status:** aceita.

O aplicativo importa arquivos Exportify e reconhece cabeçalhos normalizados. URLs do Spotify são detectadas e recebem orientação clara. Integração direta exigindo credenciais, login ou scraping fica para fase 2 e não bloqueia o executável.

## ADR-007 — Visual retrô por stylesheet Qt

**Status:** substituída pela ADR-011; preservada como histórico.

O visual será centralizado em um stylesheet e tokens: creme/bege, verde-água, azul dessaturado, grafite e cores semânticas; bordas de 1–2 px, sombras/estados elevados discretos e fontes de sistema legíveis com títulos monoespaçados. A referência inspira a direção sem reproduzir o caos visual de páginas antigas.

## ADR-008 — Empacotamento

**Status:** aceita.

PyInstaller gerará um executável `onedir` primeiro, por ser mais observável e iniciar mais rápido. O app detectará FFmpeg no PATH e, se futuramente binários forem incluídos, também no diretório empacotado. Um `onefile` poderá ser avaliado após o gate funcional.

## ADR-009 — Entrada mista e expansão de playlists do YouTube

**Status:** aceita.

O serviço de pesquisa classifica apenas URLs HTTP(S) de hosts oficiais do
YouTube. Nomes continuam usando `ytsearch1`; vídeos são resolvidos pela URL
exata; playlists são consultadas sem download e expandidas, na ordem, em uma
linha revisável por vídeo. A etapa de download continua recebendo somente as
URLs individuais aprovadas, preservando a revisão humana e evitando acoplar a
interface ao yt-dlp.

## ADR-010 — Revisão ampliada dentro da janela principal

**Status:** substituída pela ADR-011; preservada como histórico.

As três seções permanecem em um `QSplitter` vertical redimensionável. Depois da
pesquisa, entrada e atividade mantêm resumos compactos e a revisão recebe a
maior área. O modo foco apenas alterna visibilidade e tamanhos dos painéis,
preservando widgets, seleção, rolagem e dados; não cria outra janela nem altera
os serviços. Detalhes da faixa reutilizam a edição e pesquisa individual já
existentes.

## ADR-011 — Interface dark com fluxo progressivo

**Status:** aceita.

A aplicação mantém PySide6 Widgets e a moldura nativa do Windows. O conteúdo
principal usa `QStackedWidget` para exibir Adicionar, Pesquisar, Revisar, Baixar
e Concluído como estados exclusivos. Não são adotados sidebar, dashboard,
janela frameless, thumbnails remotas ou tela de configurações nesta versão.

A revisão usa `QAbstractListModel` e `QStyledItemDelegate`. O modelo é um
adaptador de apresentação sobre `SearchResult`: preserva ordem, URL/ID aprovado,
seleção, edição e progresso sem alterar serviços, workers ou tipos de domínio.
Tokens, popovers e ícones SVG locais ficam restritos à camada de UI.

Essa decisão substitui a composição simultânea baseada em `QSplitter` e
`QTableWidget`. Parsing, CSV, pesquisa, playlists, download, cookies, FFmpeg,
retries, cancelamento, guardas de geração e empacotamento permanecem protegidos.

## ADR-012 — Perfis fechados de saída de mídia

**Status:** aceita.

Áudio e vídeo usam `DownloadProfile` e enums de domínio. A interface escolhe
somente valores previamente permitidos; não aceita expressões `format` do
yt-dlp, IDs de formato ou argumentos FFmpeg digitados pelo usuário.

O padrão permanece MP3 192 kbps. Áudio pode ser convertido para AAC, ALAC,
FLAC, M4A, MP3, Opus, Vorbis ou WAV. Vídeo oferece MP4 compatível com
recodificação H.264/AAC, MP4 rápido sem recodificação, WebM e formato original,
com resolução máxima controlada. O caminho final usa a extensão conhecida pelo
perfil ou, no modo original, o `filepath` devolvido pelo yt-dlp.

Thumbnail é recusada no preflight para WAV e formato original, cujos contêineres
não oferecem uma garantia uniforme. MP4 compatível usa contêiner intermediário
MKV para assegurar que a etapa de conversão seja executada; MP4 rápido prefere
streams MP4/M4A e evita a perda de qualidade de uma recodificação.

## ADR-013 — Instalador e distribuição pública

**Status:** aceita.

A distribuição oficial do Windows usa o pacote `onedir` dentro de um instalador
Inno Setup por usuário. O instalador grava em `%LOCALAPPDATA%`, não pede
privilégios administrativos e cria um atalho `Music Downloader` no Menu
Iniciar, permitindo localizar o app na pesquisa do Windows. O atalho da Área de
Trabalho fica selecionado por padrão como fallback para instalações cujo índice
do Menu Iniciar esteja inconsistente. Atalhos e processo usam a mesma identidade
explícita e estável `PedroSalles08.MusicDownloader`, em formato PascalCase
conforme a recomendação para aplicativos Win32 não empacotados.

Cada release também oferece um ZIP portátil e hashes SHA-256. Tags `v*` acionam
um workflow Windows que executa os testes, recompila os artefatos e cria uma
GitHub Release. Assinatura de código permanece uma evolução futura e essa
limitação é informada ao usuário antes do download.
