# Quality Gate

Uma etapa só é aprovada com critérios verificáveis e revisão independente. O produto só é concluído quando todos os itens do gate final estão marcados e o revisor termina com `APROVADO`.

## Testes automatizados mínimos

- [x] Parser: uma música, várias, espaços extras, `;;`, vazios, duplicatas e caracteres especiais.
- [x] CSV: Exportify válido, colunas alternativas, BOM, linhas incompletas, arquivo vazio e falha parcial.
- [x] Pesquisa: falha de rede simulada, nenhum resultado, metadados e cancelamento.
- [x] Download: falha individual sem abortar lote, progresso por item/total e cancelamento.
- [x] Windows: nome seguro de arquivo e pasta de saída.
- [x] Dependências: ausência de FFmpeg/FFprobe com mensagem acionável.
- [x] UI: workers fora da thread principal, sinais de progresso e transições entre as cinco telas.
- [x] Revisão: model/view preserva ordem, URL/ID, seleção e pesquisa individual.

## Gate funcional

- [x] Lista por `;` funciona e deduplica.
- [x] A lista mistura nomes, vídeos e playlists do YouTube; vídeos usam a URL
  exata e playlists são expandidas em faixas revisáveis e canceláveis.
- [x] Importação CSV funciona com resumo e erros parciais.
- [x] Pesquisa real retorna resultado e não baixa durante a revisão.
- [x] Itens podem ser editados, pesquisados novamente e desmarcados.
- [x] Download selecionado gera MP3 e continua depois de falha individual.
- [x] Progresso, cancelamento, erros e resumo final são compreensíveis.
- [x] FFmpeg ausente é detectado antes do lote.
- [x] UI dark progressiva permanece responsiva e mantém a moldura nativa do Windows.
- [x] Controles fora de contexto não aparecem antes da etapa correspondente.
- [x] Logs técnicos permanecem recolhidos e erros acionáveis continuam visíveis.

## Gate de entrega

- [x] `pytest` completo passa.
- [x] `git diff --check` passa.
- [x] Fluxo manual completo é registrado.
- [x] PyInstaller gera o `.exe`.
- [x] O `.exe` inicia corretamente em Windows.
- [x] README descreve execução, build, uso autorizado e limitações.
- [x] `STATUS.md` corresponde ao estado real.
- [x] Revisão final termina exatamente em `APROVADO`.

## Gate incremental — perfis de mídia

- [x] Perfis inválidos são recusados antes de acessar rede ou destino.
- [x] MP3 192 kbps continua sendo o comportamento padrão.
- [x] Formatos de áudio, extensões reais e bitrates possuem testes.
- [x] MP4 compatível, MP4 rápido, WebM, original e resoluções possuem testes.
- [x] Worker encaminha o perfil sem importar widgets no domínio/serviço.
- [x] UI permite escolher perfis sem expor sintaxe livre do yt-dlp/FFmpeg.
- [x] CTA, acessibilidade, estados ocupados e textos refletem áudio ou vídeo.
- [x] QA visual Windows, build, smoke do `.exe` e revisão independente passam.

## Gate de distribuição pública

- [x] Instalador é por usuário e não exige elevação administrativa.
- [x] Instalação cria atalho `Music Downloader` no Menu Iniciar e usa um AppUserModelID explícito e estável.
- [x] Build de release gera instalador, pacote portátil e hashes SHA-256.
- [x] Workflow executa testes e publica os artefatos ao receber uma tag `v*`.
- [x] Instalação, pesquisa do Windows, abertura e desinstalação são validadas.
- [x] Repositório e primeira GitHub Release estão públicos.
- [x] Revisão independente termina em `APROVADO`.

## Evidência por etapa

Registre comandos, resultado, itens não testados e limitações. Testes de rede real complementam, mas não substituem, testes determinísticos com fakes.
