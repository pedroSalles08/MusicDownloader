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

**Status:** aceita.

O visual será centralizado em um stylesheet e tokens: creme/bege, verde-água, azul dessaturado, grafite e cores semânticas; bordas de 1–2 px, sombras/estados elevados discretos e fontes de sistema legíveis com títulos monoespaçados. A referência inspira a direção sem reproduzir o caos visual de páginas antigas.

## ADR-008 — Empacotamento

**Status:** aceita.

PyInstaller gerará um executável `onedir` primeiro, por ser mais observável e iniciar mais rápido. O app detectará FFmpeg no PATH e, se futuramente binários forem incluídos, também no diretório empacotado. Um `onefile` poderá ser avaliado após o gate funcional.

