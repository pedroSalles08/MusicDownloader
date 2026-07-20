# Produto

## Visão

O Music Downloader é um aplicativo desktop Windows para transformar listas de músicas e CSVs exportados do Spotify em uma fila revisável de resultados do YouTube e baixar os itens autorizados em MP3. O usuário mantém controle antes do download: pode conferir metadados, editar uma busca, repetir a pesquisa e desmarcar resultados incorretos.

O uso é limitado a conteúdo que o usuário possua ou tenha autorização para baixar.

## Público e problema

O fluxo original usa um script de terminal e listas longas separadas por ponto e vírgula. Ele já baixa com yt-dlp, mas torna difícil importar playlists, corrigir ambiguidades e acompanhar falhas. O aplicativo acrescenta importação, revisão visual, progresso, cancelamento e um pacote executável.

## MVP obrigatório

1. Receber texto separado por `;`, remover espaços e vazios e deduplicar sem perder a ordem.
2. Importar CSV UTF-8/UTF-8 com BOM, reconhecendo variações de colunas de faixa e artista, ignorando linhas inválidas sem derrubar o lote e exibindo um resumo.
3. Detectar links do Spotify e explicar o fluxo Exportify/CSV; consulta direta é fase 2.
4. Escolher e validar a pasta de saída.
5. Pesquisar cada query com yt-dlp, sem download, em trabalho assíncrono e cancelável.
6. Mostrar termo, título encontrado, canal, duração e status; permitir seleção, edição e nova busca por item.
7. Baixar selecionados, converter para MP3 192 kbps, opcionalmente incorporar capa e metadados.
8. Exibir progresso por item e total, continuar após falha individual e apresentar resumo final.
9. Detectar FFmpeg/FFprobe e orientar a correção quando ausentes.
10. Gerar um `.exe` Windows que inicia corretamente.

## Experiência

O fluxo principal usa áreas bem delimitadas para entrada, revisão e downloads, com uma barra de status persistente. A estética combina old web e desktop dos anos 90/2000, sem sacrificar legibilidade: creme e bege como base, verde-água e azul dessaturado como realces, bordas de alto contraste e controles levemente elevados.

Estados visuais mínimos: aguardando, pesquisando, encontrado, pronto, baixando, concluído, cancelado, sem resultado e erro.

## Fora do MVP

- Login ou credenciais do Spotify.
- Scraping frágil de playlists.
- Recomendações por IA.
- Download de serviços protegidos ou contorno de DRM.
- Gerenciamento completo de biblioteca musical.

## Indicadores de conclusão

O fluxo texto/CSV → pesquisa → revisão → download → resumo funciona sem congelar a interface; falhas parciais são isoladas; testes passam; QA final aprova; o executável é gerado e aberto em Windows.

