# Plano de execução

## Etapa 0 — Fundação

- [x] Inspecionar prompt, contexto, CSV real, imagem e projeto anterior.
- [x] Inicializar o repositório Git.
- [x] Criar documentação persistente.
- [x] Criar estrutura Python, ambiente e configuração de testes/build.

## Etapa 1 — Domínio e entradas

- [x] Modelar resultados de importação e dependências.
- [x] Implementar parser de lista por `;` com deduplicação estável.
- [x] Implementar CSV robusto e resumo de linhas inválidas/duplicadas.
- [x] Implementar saneamento de nomes Windows e detecção de dependências.
- [x] Cobrir casos mínimos com pytest.

## Etapa 2 — Serviços

- [x] Extrair configuração reutilizável do yt-dlp.
- [x] Implementar pesquisa sem download e mapeamento de metadados.
- [x] Implementar download MP3, capa opcional, hooks de progresso e resumo.
- [x] Implementar cancelamento cooperativo e continuação após falha.
- [x] Testar com fakes/mocks, incluindo rede, nenhum resultado e falha parcial.

## Etapa 3 — Interface

- [x] Criar janela PySide6 com entrada, importação, Spotify/fallback e destino.
- [x] Criar tabela de revisão editável/selecionável e nova pesquisa.
- [x] Criar painel de downloads, progresso por item/total, logs e resumo.
- [x] Integrar workers Qt sem bloquear a thread de UI.
- [x] Aplicar e documentar o sistema visual retrô.
- [x] Ampliar a revisão com splitter persistente, painéis compactos, modo foco,
  tabela legível e detalhes recolhíveis por faixa.

## Etapa 4 — Robustez e empacotamento

- [x] Executar suíte completa e análise do diff.
- [x] Validar manualmente parser, CSV real e fluxo controlado de pesquisa/download.
- [x] Criar spec/receita PyInstaller e gerar `.exe`.
- [x] Abrir o executável e registrar evidência.
- [x] Fazer revisão QA final e corrigir até aprovação.

## Etapa 5 — Redesign UI/UX progressivo

- [x] Criar sistema visual dark, popovers e recursos SVG locais.
- [x] Substituir as três áreas simultâneas por `QStackedWidget` com cinco etapas.
- [x] Migrar a revisão para `ReviewListModel` e `ReviewItemDelegate`.
- [x] Criar telas minimalistas de pesquisa, download e conclusão.
- [x] Preservar serviços, workers, tipos de domínio e guardas funcionais.
- [x] Migrar testes legados e ampliar cobertura da nova navegação/modelo.
- [x] Concluir build, smoke do executável e QA manual Windows do redesign.

## Etapa 6 — Perfis de áudio e vídeo

- [x] Modelar perfis fechados e validados, sem aceitar seletores livres do
  yt-dlp ou argumentos FFmpeg vindos da UI.
- [x] Implementar áudio AAC, ALAC, FLAC, M4A, MP3, Opus, Vorbis e WAV, com
  bitrates controlados para formatos com perdas.
- [x] Implementar vídeo MP4 compatível, MP4 rápido, WebM e formato original,
  com limites de 360p, 720p, 1080p ou melhor qualidade.
- [x] Tornar a extensão e o caminho final dinâmicos e passar o perfil pelo
  `DownloadWorker`, preservando MP3 192 kbps como padrão.
- [x] Integrar os seletores ao popover de opções e adaptar CTA/textos da UI.
- [x] Fazer QA visual Windows, build e smoke do executável com a nova UI.

## Etapa 7 — Distribuição pública

- [x] Criar instalador por usuário com atalho no Menu Iniciar pesquisável pelo Windows.
- [x] Criar pacote portátil e hashes SHA-256.
- [x] Automatizar build e GitHub Release para tags `v*`.
- [x] Validar instalador, atalho e desinstalação.
- [ ] Publicar repositório e primeira release pública após QA independente.

## Estratégia de commits

Um commit pequeno após cada etapa aprovada: fundação; domínio/importação; serviços; UI; robustez; pacote final. Arquivos de entrada fornecidos pelo usuário permanecem versionados como referência, salvo decisão documentada em contrário.
