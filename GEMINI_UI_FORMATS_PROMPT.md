# Prompt para o Gemini CLI — integrar perfis de mídia à UI

Você está trabalhando no repositório Windows/Python/PySide6
`C:\Users\Usuario\Desktop\pessoal\MusicDownloader`.

Implemente a integração visual dos novos perfis de áudio e vídeo já existentes
no backend. Antes de alterar qualquer arquivo, leia integralmente `AGENTS.md`,
`PRODUCT.md`, `PLAN.md`, `STATUS.md`, `QUALITY_GATE.md`, `DECISIONS.md`,
`DESIGN_SYSTEM.md` e os arquivos de UI/testes relevantes. Inspecione também o
diff atual e preserve todas as alterações existentes do usuário.

## Contexto obrigatório

A aplicação já passou por um redesign dark progressivo. O fluxo existente é:

`Adicionar → Pesquisar → Revisar → Baixar → Concluído`

Ele usa `QStackedWidget`, title bar nativa do Windows, `OptionsPopover`,
`ReviewListModel` e `ReviewItemDelegate`. Preserve essa arquitetura e a direção
visual atual. Não crie sidebar, dashboard, janela frameless, nova tela de
configurações, thumbnails remotas ou cards grandes por faixa. Não faça uma
refatoração ampla e não altere a camada de pesquisa/importação.

O backend novo está em `src/music_downloader/download_profiles.py` e já é
coberto por testes. Use exatamente estes contratos:

- `MediaKind.AUDIO` e `MediaKind.VIDEO`;
- `AudioFormat`: `AAC`, `ALAC`, `FLAC`, `M4A`, `MP3`, `OPUS`, `VORBIS`, `WAV`;
- `VideoFormat`: `MP4_COMPATIBLE`, `MP4_FAST`, `WEBM`, `ORIGINAL`;
- `AUDIO_BITRATE_CHOICES`: 128, 192, 256, 320;
- `VIDEO_HEIGHT_CHOICES`: 360, 720, 1080; `None` significa melhor qualidade;
- `DownloadProfile.for_audio(...)` e `DownloadProfile.for_video(...)`;
- `DownloadProfile.supports_thumbnail` e `output_extension`;
- `DEFAULT_DOWNLOAD_PROFILE`, que deve manter MP3 192 kbps como padrão.

`DownloadWorker` e `DownloadService.download_batch` já aceitam `profile=`. Não
reimplemente seletores do yt-dlp na UI e não aceite texto livre, IDs de formato,
expressões `format` ou argumentos FFmpeg do usuário. Não modifique os perfis ou
o serviço salvo se encontrar um defeito funcional concreto, coberto por teste e
explicado no handoff.

## Objetivo visual e funcional

Amplie o `OptionsPopover` existente com uma seção clara de saída, sem deixar o
popover pesado. Use controles nativos estilizados pelos tokens atuais e
layouts fluidos.

Controles esperados:

1. `Tipo de mídia`: `Somente áudio` ou `Vídeo`.
2. Para áudio:
   - `Formato`: MP3, M4A, Opus, AAC (.m4a), Vorbis (.ogg), FLAC, ALAC (.m4a),
     WAV;
   - `Qualidade`: 128, 192, 256 ou 320 kbps para formatos com perdas;
   - para FLAC, ALAC e WAV, esconda ou desabilite qualidade e mostre
     `Sem perdas`;
   - inclua uma ajuda curta dizendo que converter uma fonte comprimida para um
     formato sem perdas não recupera qualidade.
3. Para vídeo:
   - `Formato`: `MP4 compatível`, `MP4 rápido`, `WebM`, `Original`;
   - `Resolução máxima`: 360p, 720p, 1080p ou `Melhor disponível`;
   - ajuda contextual:
     - MP4 compatível: H.264/AAC, maior compatibilidade, mais lento por
       recodificar;
     - MP4 rápido: evita recodificação e depende de streams MP4/M4A disponíveis;
     - WebM: preserva streams WebM compatíveis;
     - Original: preserva a seleção/container entregue pelo yt-dlp e a extensão
       pode variar.
4. Mantenha `Incorporar thumbnail como capa` e `Sessão do YouTube`.

Use valores enum como `userData` dos `QComboBox`; nunca reconstrua enums a partir
do texto visível. Uma única configuração vale para todo o lote. Não implemente
formato por item nesta etapa.

## Regras de estado

- O estado inicial deve continuar sendo áudio, MP3 e 192 kbps.
- Ao alternar tipo/formato, mostre somente controles relevantes.
- Se o perfil não aceitar thumbnail (`supports_thumbnail == False`), desmarque
  e desabilite o checkbox e explique por tooltip/ajuda. Ao voltar a um perfil
  compatível, reabilite o controle sem marcá-lo automaticamente.
- Todos os novos controles ficam desabilitados durante pesquisa/download junto
  aos controles já protegidos por `_set_busy`.
- A seleção feita no popover deve persistir ao abrir o mesmo popover nas telas
  Adicionar e Revisar durante a sessão.
- Mudanças de perfil devem atualizar imediatamente os textos contextuais e o
  CTA da revisão.
- Preserve cancelamento, cookies, aria2c, guardas de geração, retry, seleção,
  edição, nova pesquisa e transições atuais.

## Integração na `MainWindow`

Crie um método pequeno e testável que produza o `DownloadProfile` atual a
partir dos `currentData()` dos combos. No `start_download`, construa o perfil
antes de iniciar o worker e passe explicitamente `profile=profile` ao
`DownloadWorker`.

Não armazene sintaxe do yt-dlp na janela. Se uma combinação impossível ocorrer
por estado programático, mostre uma mensagem pt-BR compreensível e permaneça em
Revisar, sem iniciar worker ou criar a pasta de destino.

Adapte textos que hoje presumem exclusivamente música/MP3:

- placeholder do destino deve falar em `arquivos`, não `arquivos MP3`;
- CTA de áudio, exemplos:
  - `Baixar 1 áudio em MP3 · 192 kbps`;
  - `Baixar 7 áudios em FLAC`;
- CTA de vídeo, exemplos:
  - `Baixar 1 vídeo em MP4 · até 1080p`;
  - `Baixar 3 vídeos no formato original`;
- tela de download e conclusão devem usar `arquivo`, `áudio` ou `vídeo` quando
  necessário, sem chamar vídeo de música;
- mantenha os textos compactos: em largura mínima, evite que o rodapé ou botão
  principal corte informações essenciais. Se preciso, use tooltip e uma versão
  visual curta do CTA preservando nome acessível completo.

Os nomes pt-BR podem ficar na camada de UI; código e identificadores técnicos
devem continuar em inglês.

## Acessibilidade e acabamento

- Defina `accessibleName` e, quando útil, `accessibleDescription` para os novos
  campos.
- Labels devem ter buddy/associação quando a API Qt usada permitir.
- Preserve navegação por Tab, foco visível, contraste e operação por teclado.
- Use a escala 4/8/12/16/24/32 px e os tokens de `DESIGN_SYSTEM.md`.
- O popover deve caber na área disponível em 720 × 600 e continuar utilizável
  em escala de 125%, 150% e 200%. Se necessário, torne o conteúdo compacto ou
  rolável; não fixe uma altura que corte controles.
- Não acrescente dependências ou assets remotos.

## Testes obrigatórios

Atualize `tests/test_ui.py` e somente outros testes que forem realmente
necessários. Cubra pelo menos:

1. padrão visual produz `DEFAULT_DOWNLOAD_PROFILE`;
2. cada item dos combos guarda o enum correto em `userData`;
3. áudio com perdas mostra bitrate e produz o perfil escolhido;
4. FLAC/ALAC/WAV não enviam bitrate;
5. vídeo produz formato e resolução corretos, incluindo `None` para melhor;
6. WAV e Original desmarcam/desabilitam thumbnail;
7. perfil volta a permitir thumbnail sem reativá-la sozinho;
8. `start_download` encaminha o perfil escolhido ao fake service;
9. CTA usa singular/plural e descrição de qualidade coerentes;
10. novos controles ficam indisponíveis enquanto o worker está ocupado;
11. transições, cancelamento e testes legados continuam passando;
12. nomes acessíveis não estão vazios.

Os testes não podem acessar rede real nem executar FFmpeg. Ajuste os fakes sem
reduzir asserções existentes e não enfraqueça testes para obter sucesso.

## Verificação e documentação

Ao terminar:

1. execute a suíte focada de UI;
2. execute `python -m pytest` completo no `.venv`;
3. execute `python -m compileall -q src tests`;
4. execute `python -m music_downloader --smoke-test` com ambiente offscreen se
   necessário;
5. execute `git diff --check`;
6. inspecione visualmente a janela em 1060 × 760 e 720 × 600, incluindo os
   estados áudio com perdas, áudio sem perdas, MP4 compatível e Original;
7. atualize `STATUS.md`, `PLAN.md`, `QUALITY_GATE.md`, `README.md` e, se houver
   nova decisão arquitetural, `DECISIONS.md`, sem reescrever o histórico;
8. não faça commit antes de testes e revisão QA independente, conforme
   `AGENTS.md`.

Entregue um resumo objetivo com arquivos alterados, decisões de UX, comandos e
resultados, evidência visual inspecionada, limitações e qualquer item ainda não
validado. Não declare a nova release aprovada se build, smoke do executável ou
QA independente ainda estiverem pendentes.
