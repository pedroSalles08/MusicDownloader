# Produto

## Visão

O Music Downloader é um aplicativo desktop Windows para transformar listas de músicas e CSVs exportados do Spotify em uma fila revisável de resultados do YouTube e baixar os itens autorizados em MP3. O usuário mantém controle antes do download: pode conferir metadados, editar uma busca, repetir a pesquisa e desmarcar resultados incorretos.

O uso é limitado a conteúdo que o usuário possua ou tenha autorização para baixar.

## Público e problema

O fluxo original usa um script de terminal e listas longas separadas por ponto e vírgula. Ele já baixa com yt-dlp, mas torna difícil importar playlists, corrigir ambiguidades e acompanhar falhas. O aplicativo acrescenta importação, revisão visual, progresso, cancelamento e um pacote executável.

## MVP obrigatório

1. Receber nomes, links de vídeos e playlists do YouTube separados por `;`, remover espaços e vazios e deduplicar sem perder a ordem. Nomes são pesquisados; vídeos usam a URL exata; playlists são expandidas em itens revisáveis.
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

O fluxo principal é progressivo: Adicionar, Pesquisar, Revisar, Baixar e
Concluído. A janela mostra somente a etapa relevante, sem sidebar, dashboard ou
painel de atividade permanente. A moldura continua nativa do Windows; o
conteúdo usa a direção dark Midnight Deck: hierarquia minimalista, sinais de
equipamento musical e comportamento nativo do Windows, sem imitar outro
sistema operacional.

A entrada universal aceita nomes, vídeos e playlists sem exigir que o usuário
escolha previamente o tipo. CSV/Spotify e opções técnicas ficam em popovers.
A revisão usa uma lista compacta com hierarquia musical, seleção, ações
contextuais, perfil de saída visível e CTA que informa a quantidade escolhida.
O cabeçalho mostra a etapa real do fluxo; pesquisa, download e conclusão
possuem telas próprias e logs técnicos ficam recolhidos por padrão.

Estados visuais mínimos: aguardando, pesquisando, encontrado, pronto, baixando,
convertendo, nova tentativa, concluído, cancelado, sem resultado e erro. Todo
estado combina texto e forma, sem depender somente de cor.

## Fora do MVP

- Login ou credenciais do Spotify.
- Scraping frágil de playlists.
- Recomendações por IA.
- Download de serviços protegidos ou contorno de DRM.
- Gerenciamento completo de biblioteca musical.

## Saída de áudio e vídeo

O backend aceita perfis fechados para áudio AAC, ALAC, FLAC, M4A, MP3, Opus,
Vorbis e WAV, além de vídeo MP4 compatível, MP4 rápido, WebM e formato original.
Qualidade de áudio e resolução são valores validados pelo domínio; a UI não
deve expor seletores livres do yt-dlp nem argumentos FFmpeg.

MP4 compatível recodifica para H.264/AAC; MP4 rápido preserva os streams e
depende de combinações MP4/M4A disponíveis na fonte. Formatos sem perdas não
prometem recuperar qualidade ausente na origem. Esses perfis estão integrados
ao popover de opções do redesign, mantendo MP3 192 kbps como padrão.

## Indicadores de conclusão

O fluxo texto/CSV → pesquisa → revisão → download → resumo funciona sem congelar a interface; falhas parciais são isoladas; testes passam; QA final aprova; o executável é gerado e aberto em Windows.
