# Status do projeto

Atualizado em: 2026-09-22

## Estado atual

**Refinamento visual e de affordances Midnight Deck concluído e validado.**
O fluxo progressivo e o backend permanecem intactos, mas a interface ganhou uma
identidade musical própria, indicador das cinco etapas, perfil de saída visível,
botões com rótulos acionáveis, feedback de entrada/seleção/destino, pesquisa com
progresso determinístico e estados de revisão mais legíveis.

## Evolução atual — refinamento UI/UX Midnight Deck

- A linguagem visual deixou de reproduzir um dark genérico inspirado no macOS e
  passou a usar grafite azulado, texto quente, azul mineral, âmbar e microtexto
  monoespaçado, conforme `DESIGN_SYSTEM.md` e a ADR-014.
- O cabeçalho exibe `etapa / total`, nome da etapa e uma linha de fluxo em forma
  de playhead; a informação acessível acompanha cada transição.
- A entrada mostra quantidade válida e duplicatas, desabilita a pesquisa vazia
  com orientação e transforma o CTA em `Pesquisar N itens`.
- `Importar`, `Opções`, `Alterar…`, `Mais ações`, `Ver detalhes` e
  `Nova operação` receberam rótulos mais específicos e ícones SVG locais.
- O formato efetivo (`MP3 · 192 kbps`, `FLAC`, `MP4 compatível · até 1080p`)
  permanece visível fora do popover; o CTA curto informa ação e quantidade.
- A revisão ganhou contagem selecionada, status em cápsulas textuais, affordance
  de ações e dock de destino com explicação do motivo de bloqueio/prontidão.
- Caminhos longos usam elipse central, mantendo o valor completo em tooltip e
  nome acessível. A navegação move o foco para a tela ativa e respeita a
  preferência Qt por animações de widgets.
- Capturas dos cinco estados foram inspecionadas em 1060 × 760; Adicionar e
  Revisar também foram validados no mínimo de 720 × 600.

### Evidência automatizada desta evolução

- Testes focados da UI (`tests/test_ui.py`): **36 passaram**.
- Suíte completa do projeto: **198 passaram em 3,59 s**.
- `compileall` de `src` e `tests`, smoke Python e `git diff --check`: código 0.
- O módulo gerado de recursos contém os novos SVGs e
  `music_downloader.ui.resources_rc` está presente no arquivo PYZ.
- Build final isolado em `dist-ui-polish-final\MusicDownloader`: 236 arquivos,
  128.416.568 bytes. O executável tem 9.828.801 bytes, SHA-256
  `5E5D869E898B26323BD9DFA65FCB0E5FF2ECAC4BBEF0D5892B1151E60FFE7B04` e
  smoke-test concluído com código 0.
- Revisão QA independente da interface: **APROVADO**; verificou diff, suíte,
  importação CSV, erros, cancelamento, acessibilidade básica, cinco etapas e
  layout mínimo. A captura offscreen não valida a fonte no Windows real.
- Versão `0.1.1` preparada para publicar a nova interface como release mais
  recente, preservando a release `v0.1.0` anterior.

## Evolução anterior — integração UI e perfis de mídia

- `OptionsPopover` integrado com `media_kind_combo`, `audio_format_combo`, `audio_quality_combo`, `video_format_combo`, `video_resolution_combo`, `cover_checkbox` e `cookie_browser_combo`.
- Alternância dinâmica entre container de áudio e container de vídeo com redimensionamento automático.
- FLAC, ALAC e WAV ocultam o seletor de bitrate e exibem badge "Sem perdas" com dica contextual de qualidade.
- Formatos de vídeo exibem dica técnica contextual explicativa sobre recodificação / preservação de streams.
- Thumbnail é desmarcada e desabilitada automaticamente para WAV e Original; ao retornar para formatos com suporte, o controle é reabilitado sem ser remarcado sozinho.
- `MainWindow` expõe `current_download_profile()`, conecta o sinal `profileChanged` para atualização reativa do botão de ação e repassa o perfil ao `DownloadWorker`.
- `format_download_cta` formata o CTA com contagem, tipo de mídia, formato e qualidade de forma gramaticalmente correta em pt-BR.
- Acessibilidade configurada em todos os novos componentes de formulário.

### Evidência automatizada desta evolução

- Testes focados da UI (`tests/test_ui.py`): **32 passaram em 3,84 s**.
- Suíte completa do projeto: **189 passaram em 3,58 s**.
- `compileall` de `src` e `tests`: concluído com código 0.
- Smoke-test Python (`music_downloader --smoke-test`): concluído com código 0.
- `git diff --check`: concluído sem erros de formatação ou espaços.

## Evolução atual — redesign UI/UX progressivo

- Entrada universal, destino, importação CSV/Spotify e opções técnicas foram
  reorganizados sem mudar parsing ou contratos de importação.
- Pesquisa e download possuem telas próprias e minimalistas; detalhes técnicos
  ficam recolhidos por padrão.
- A revisão usa `ReviewListModel` e `ReviewItemDelegate`, preservando ordem,
  seleção inicial, URL/ID aprovado, edição, pesquisa individual e playlists.
- A conclusão apresenta sucesso de forma simples, diferencia término parcial e
  oferece abertura da pasta via `QDesktopServices`.
- `QSplitter`, `QTableWidget`, modo foco e estilos retrô foram removidos após a
  migração da cobertura funcional.
- Ícones SVG locais são incorporados por `resources_rc.py`; nenhuma capa é
  baixada para fins visuais.

### Evidência automatizada do redesign

- Testes focados do QA independente: **39 passaram**.
- Suíte completa: **144 passaram em 2,53 s**.
- `compileall` de `src` e `tests`: concluído sem erro.
- Capturas dos estados Adicionar, Pesquisar, Revisar, Baixar e Concluído foram
  inspecionadas em 1060 × 760 e no mínimo 720 × 600.
- Backend nativo `windows` validado em DPI 125%, com maximização em 1536 × 793
  e restauração/redimensionamento para 760 × 640.
- Build isolado gerou `dist-redesign\MusicDownloader` com 275 arquivos e
  130.252.222 bytes. O executável tem 9.802.903 bytes, SHA-256
  `C060F4903185F0758FDE1516D70B48641E19D832E6FC4780A40B85E920E574E3` e
  smoke-test concluído com código 0.
- `pip check` e `git diff --check` concluíram sem erro; o módulo
  `music_downloader.ui.resources_rc` está presente no PYZ do pacote.
- Revisão QA independente: **APROVADO**.

## Correção anterior — formatos de áudio e EJS

## Correção atual — formatos de áudio e EJS

- Após a autenticação resolver o bloqueio anti-bot, 24 faixas passaram a falhar
  com `Requested format is not available`. O vídeo removido por copyright
  continuou como uma falha individual legítima.
- A causa confirmada era a instalação simples de `yt-dlp`: Node estava
  disponível, mas o pacote complementar `yt-dlp-ejs` não estava instalado nem
  presente no executável.
- A dependência de runtime agora usa `yt-dlp[default]`, que mantém
  `yt-dlp-ejs` sincronizado com a versão do extrator e inclui os componentes
  recomendados pelo projeto upstream.
- Erros de formato indisponível e vídeo removido são tratados como não
  transitórios e deixam de consumir três tentativas idênticas por faixa.
- A validação real, sem baixar mídia, consultou `91Kg7Sc79_E` com a sessão
  Firefox e encontrou 12 formatos, incluindo 5 com áudio: `140`, `91`,
  `93`, `18` e `94`. PO Token não foi necessário nesse vídeo.

### Evidência da correção atual

- Testes focados de download e empacotamento: **34 passaram**.
- Suíte completa: **137 passaram em 2,37 s**.
- `compileall`, smoke-test Python e `git diff --check` concluíram sem erro.
- Como `dist\MusicDownloader` estava aberto pelo usuário no PID 19340, o
  processo não foi encerrado e a correção foi gerada em
  `dist-ejs\MusicDownloader`.
- A nova distribuição contém 275 arquivos, 130.232.708 bytes e 5 arquivos EJS.
  O executável tem 9.783.389 bytes, SHA-256
  `D74FA7968C7F6635625D6C735FD5A5984D28CB38259B64F667DF0137DAB3E856` e
  smoke-test bloqueante concluído com código 0.

## Correção anterior — autenticação anti-bot do YouTube

- O diagnóstico real de 25 faixas mostrou 24 recusas `Sign in to confirm
  you're not a bot` e um vídeo removido por copyright; a expansão da playlist
  estava correta e a falha ocorria ao baixar cada URL individual sem cookies.
- A revisão agora oferece `Sessão YouTube` junto ao botão de download, com
  Firefox, Chrome, Edge, Brave, Vivaldi e Opera e seleção inicial baseada no
  navegador HTTPS padrão do Windows.
- O serviço envia ao yt-dlp somente o valor estruturado
  `cookiesfrombrowser=(browser,)`; valores fora da lista permitida são
  recusados antes de detectar ferramentas, acessar a rede ou criar o destino.
- Cookies permanecem sob responsabilidade do yt-dlp e não são exibidos,
  persistidos pelo aplicativo nem interpolados em comandos de shell.
- A recusa anti-bot é tratada como falha de autenticação não transitória: não
  repete inutilmente três vezes e orienta selecionar, autenticar, fechar ou
  trocar o navegador. Vídeos realmente removidos continuam como falha isolada.

### Evidência da correção atual

- Testes focados de cookies, download, workers e UI: **62 passaram**.
- Suíte completa: **134 passaram em 2,20 s**.
- `compileall`, smoke-test Python e `git diff --check` concluíram sem erros; os
  testes não acessam rede real nem cookies reais do usuário.
- `packaging/build.ps1 -SkipInstall` gerou `dist\MusicDownloader` com 217
  arquivos e 125.662.991 bytes. O executável tem 8.351.826 bytes, SHA-256
  `38E0F3C8849CB92F15874959705727EAC6A833CA38D66B0AA15CBD69DAB1D57C` e
  smoke-test bloqueante concluído com código 0.

## Evolução atual — usabilidade da revisão

- `QSplitter` vertical acessível e redimensionável permanece como estrutura das
  seções 01, 02 e 03; a revisão recebe a maior altura inicial.
- Pesquisa concluída compacta entrada e atividade. O resumo da entrada preserva
  quantidade, destino e botão para reabrir; progresso, resumo e acesso ao log
  permanecem disponíveis na atividade compacta.
- `AMPLIAR ⛶` ativa o modo foco dentro da mesma janela e `RESTAURAR` devolve os
  painéis com seus estados, dados, seleção e rolagem preservados.
- Tabela com linhas de 46 px, cabeçalho fixo, colunas interativas e responsivas,
  seleção estreita e tooltips completos de consulta e título.
- Painel recolhível da faixa selecionada mostra consulta, título, canal,
  duração, URL e status e reutiliza a pesquisa individual existente.
- Cancelamento permanece visível no cabeçalho da revisão durante operações,
  inclusive em modo foco.

### Evidência da evolução atual

- Testes de UI focados: **22 passaram**.
- Suíte completa: **119 passaram em 2,05 s**.
- `compileall`, smoke-test Python e `git diff --check` — concluídos sem erro.
- Renderização nativa Windows inspecionada nos estados compacto e foco; sem
  sobreposição, corte de controles ou perda da estética retrô.
- Revisão QA independente: **22 testes de UI e 119 testes completos passaram;
  REVISOR_QA: APROVADO**.
- A distribuição anterior estava aberta e bloqueou sua substituição segura; o
  processo do usuário não foi encerrado. A nova versão foi gerada em
  `dist-review\\MusicDownloader` com 217 arquivos e 125.659.987 bytes.
- O novo `MusicDownloader.exe` tem 8.348.822 bytes, SHA-256
  `FB75BA8CE30A41E3A6B66FC9A986E804CDA614EAD346A6986AECE8C05C2D0062` e
  smoke bloqueante concluído com código 0.

## Evolução atual — links e playlists do YouTube

- Entradas separadas por `;` podem misturar nomes, vídeos e playlists.
- Nomes continuam usando `ytsearch1`; links reconhecidos de vídeos usam a URL
  exata, sem pesquisa textual intermediária.
- Playlists são extraídas sem download e expandidas em uma linha marcada por
  vídeo, preservando a ordem e usando a URL individual em cada resultado.
- A pesquisa individual de uma faixa expandida usa sua URL direta e não reabre
  a playlist completa.
- A expansão usa iteração lazy e observa cancelamento entre entradas; falhas e
  playlists sem vídeos válidos permanecem estados revisáveis.
- A UI e sua descrição acessível informam explicitamente a entrada mista.

### Evidência da evolução atual

- `.\\.venv\\Scripts\\python.exe -m pytest` — **115 passaram em 2,14 s**.
- `compileall`, smoke-test Python e `git diff --check` — concluídos sem erro.
- O primeiro ciclo QA reproduziu dois problemas: nova pesquisa reabria a
  playlist e a expansão não observava cancelamento. Ambos receberam correções
  específicas e testes de regressão.
- Segundo ciclo QA: **41 testes focados e 115 testes completos passaram;
  REVISOR_QA: APROVADO**.
- `packaging/build.ps1 -SkipInstall` gerou a nova distribuição com 217 arquivos
  e 125.652.973 bytes. `MusicDownloader.exe` tem 8.341.808 bytes e SHA-256
  `5CB85E3209783DE639FB04D21EA03F8E1C1DB3036E53008387FE6D75A1E45331`.
- O smoke do novo `.exe` encerrou com código 0.

## Implementado nesta etapa

- Parser de texto por `;` com trim, descarte de vazios, ordem estável e
  deduplicação case-insensitive com normalização Unicode NFKC.
- Importador CSV com UTF-8/BOM e fallback cp1252, aliases normalizados de faixa
  e artista, separadores comuns, validação estrita de aspas, recuperação por
  linha, registro de linhas inválidas e deduplicação. Campos multilinha são
  rejeitados para preservar a recuperação do próximo registro Exportify.
- Detecção restrita de URLs `open.spotify.com/playlist/...`; a integração direta
  continua fora do MVP.
- Saneamento de nomes Windows para caracteres inválidos/controles/surrogates,
  sufixos com ponto ou espaço, nomes reservados, fallback e limite medido em
  unidades UTF-16 sem corte de caracteres suplementares.
- Detecção de FFmpeg e FFprobe com resolvedor injetável e orientação acionável.
- Estrutura `src`, configuração `pyproject.toml`, `.gitignore` e testes pytest.
- Pesquisa `ytsearch1` sem download, mapeamento de metadados, estados de nenhum
  resultado/erro e continuação do lote após falha individual.
- Download somente da URL aprovada, com MP3 192 kbps, metadados, capa e aria2c
  opcionais, nomes seguros com ID/hash, reserva contra colisões no lote/disco,
  até três tentativas, progresso e cancelamento.
- Preflight de FFmpeg/FFprobe antes do lote e factories/espera injetáveis para
  testes determinísticos sem rede ou processos reais.
- Busca ignora entradas sem ID/URL e só aceita resultado com URL direta ou
  fallback estável pelo ID; destino inválido vira diagnóstico de preflight e
  lote vazio retorna sem detectar ferramentas ou criar diretório.
- Janela principal em pt-BR com lista `;`, CSV, orientação Spotify/Exportify,
  destino, capa, revisão editável/selecionável, pesquisa por linha e status bar.
- Workers em `QThread` para pesquisa/download, progresso por item e total,
  cancelamento cooperativo e fechamento seguro enquanto há trabalho ativo.
- Fila visual de download com aria2c autodetectado, logs de falhas e resumo de
  sucesso/falha/cancelamento/pasta.
- Sistema visual retrô organizado documentado em `DESIGN_SYSTEM.md` e entry
  point `python -m music_downloader` com `--smoke-test` sem rede.
- Gerações de operação isolam callbacks antigos; pesquisa preserva a ordem das
  consultas e progressos nunca regridem nem reabrem estado terminal.
- Campos principais têm labels/buddies com atalhos, nomes e descrições
  acessíveis; tokens de azul/aviso atendem contraste WCAG AA de 4,5:1.
- Receita PyInstaller `onedir` versionada, com build limpo repetível e smoke
  sem rede; binários externos FFmpeg, FFprobe, Node e aria2c não são embutidos.
- Validação manual controlada tenta o vídeo público conhecido apenas após
  confirmar ID e título; se a confirmação falhar, usa um tom autorizado servido
  em `localhost`, convertido pelo serviço real e removido ao final.

## Evidência automatizada

- Ambiente criado em `.venv` com Python 3.13.14.
- Instalação editável: `.\\.venv\\Scripts\\python.exe -m pip install -e '.[dev]'` — concluída.
- Testes de domínio, serviços, workers, interface e empacotamento:
  `.\\.venv\\Scripts\\python.exe -m pytest` — **105 passaram em 1,82 s**.
- Regressões específicas cobrem limite UTF-16 com emoji/surrogates e CSV com
  conteúdo após aspas, aspas não fechadas, escape válido e campo multilinha.
- O teste da amostra real confirmou 159 linhas lidas, 158 queries únicas, uma
  duplicata e nenhuma linha inválida.
- Testes Qt usam plataforma offscreen; não usam rede real, extração yt-dlp real
  nem FFmpeg externo. O smoke-test Python abre e fecha a janela sem rede.
- `packaging/build.ps1 -SkipInstall` concluiu o build final em cerca de 63 s e
  gerou `dist\\MusicDownloader\\MusicDownloader.exe`: 8.338.876 bytes, 217
  arquivos e 125.650.041 bytes na pasta onedir. Nenhum executável externo ou
  módulo de desenvolvimento foi incluído.
- O smoke do `.exe` terminou com código 0. Na abertura normal, o processo
  permaneceu ativo por 3,5 s com o título esperado e foi encerrado pelo PID
  exato lançado para o teste.
- O QA final confirmou SHA-256
  `99CCCD774850D9EBDAE1E6E464349268CDABE9687591E050D6F721AC0F78D161`
  para o executável de 8.338.876 bytes.
- Pesquisa real encontrou um resultado, mas com ID diferente do vídeo público
  esperado; o download foi corretamente bloqueado. O fallback local gerou WAV
  de 88.278 bytes e MP3 de 26.059 bytes em uma tentativa, encerrou o servidor e
  removeu toda a mídia temporária.
- A janela foi renderizada com o backend Qt `windows` e inspecionada em estado
  inicial; hierarquia, legibilidade, alinhamento e estados desabilitados estavam
  coerentes. A captura temporária foi removida e não integra o repositório.
- `pip check`, `compileall`, smoke-test Python e `git diff --check` concluíram
  sem erro.

## Inventário confirmado

- `promptMestre.md` lido integralmente.
- `contextScriptMusicas.md` e o projeto anterior inspecionados.
- `csv-example.csv`: 159 linhas de dados, 24 colunas, títulos/artistas presentes e 158 queries únicas; expectativa agora coberta por teste automatizado.
- `UI-inspirations-design.png`: painel de referências retro internet/desktop revisado.
- Ambiente: Python 3.13, FFmpeg 8.1.2, FFprobe, aria2c, Node e Git disponíveis.
- pytest 9.1.1, pytest-qt 4.5.0, yt-dlp 2026.7.4, PySide6 6.11.1 e PyInstaller
  6.21.0 instalados no `.venv`.

## Reutilização do script anterior

- Busca `ytsearch1`, download de melhor áudio e pós-processamento MP3 192 kbps.
- Retry por item, fragmentos simultâneos, aria2c opcional e capa opcional.
- Comparação normalizada de cabeçalhos CSV e leitura `utf-8-sig`.

## Próximos passos opcionais

Gate funcional concluído. Próximas evoluções opcionais podem incluir assinatura
de código e integração direta com Spotify mediante solução robusta de
autenticação; nenhuma delas bloqueia o MVP entregue.

## Revisão da etapa

- Primeiro ciclo: reprovado por limite de nome baseado em pontos de código e
  parsing CSV permissivo.
- Ciclo corretivo 1: limite alterado para unidades UTF-16 e parser CSV estrito
  com recuperação por linha.
- Resultado final: **49 testes passaram; REVISOR_QA: APROVADO**.
- Serviços, primeiro ciclo: reprovado por colisões de saída, candidato de busca
  sem URL, `ValueError` de destino e efeito colateral em lote vazio.
- Serviços, ciclo corretivo 1: reserva de nomes únicos, filtro de candidatos,
  preflight robusto e retorno vazio sem efeitos.
- Resultado dos serviços: **79 testes passaram; REVISOR_QA: APROVADO**.
- Interface, primeiro ciclo: reprovado por callbacks regressivos, contraste e
  metadados insuficientes de acessibilidade.
- Interface, ciclo corretivo 1: sinais com geração, guardas monotônicas e
  terminais, contraste AA e associações acessíveis.
- Resultado da interface: **101 testes passaram; REVISOR_QA: APROVADO**.
- Robustez/empacotamento: **105 testes passaram**, build limpo refeito, `.exe`
  aberto e fluxo real controlado repetido; **REVISOR_QA FINAL: APROVADO**.

## Bloqueios

Nenhum bloqueio técnico confirmado. O acesso direto a playlists Spotify
permanece fora do MVP e não bloqueia a entrega. A variabilidade da pesquisa do
YouTube exige revisão humana; nesta validação, a divergência de ID foi detectada
e nenhum conteúdo ambíguo foi baixado.

## Etapa 7 — Distribuição pública (concluída)

- Build hermético evita coletar DLLs expostas por runtimes de ferramentas no
  `PATH`; uma primeira tentativa contaminada falhou no QtCore e foi descartada.
- O executável possui metadados Windows de produto, descrição e versão 0.1.0.0.
- O instalador Inno Setup 6 é por usuário, grava em `%LOCALAPPDATA%`, registra
  desinstalação e App Paths em HKCU e cria atalho no Menu Iniciar. Atalho e
  processo usam o AppUserModelID explícito `PedroSalles08.MusicDownloader`.
- O Windows Search desta máquina não enumerou o atalho do Menu Iniciar nem após
  reinício, mas indexou imediatamente o atalho oficial da Área de Trabalho. Essa
  opção agora vem selecionada por padrão no instalador como fallback de busca.
- Um atalho manual antigo chamado `MusicDownloader.exe - Atalho (2)`, que
  apontava para `dist-redesign`, foi removido para a Lixeira. A consulta ao
  índice passou a retornar apenas `Music Downloader.lnk` como `link,program`,
  apontando para o executável instalado em `%LOCALAPPDATA%`.
- Upgrades removem somente `_internal`, o executável e atalhos gerenciados antes
  de copiar a versão nova; arquivo estranho criado na raiz foi preservado no
  teste de QA.
- Desinstalação silenciosa removeu executável, atalhos e registro gerenciado;
  reinstalação terminou com código 0 e o app instalado passou no smoke-test.
- A suíte completa passou com **197 testes**; o ciclo corretivo adicionou testes
  de metadados, identidade do aplicativo e empacotamento.
- Artefatos locais em `release\`: instalador, ZIP portátil e `SHA256SUMS.txt`.
  Eles permanecem ignorados pelo Git e serão anexados à GitHub Release.
- A primeira estratégia usava um AUMID cujo segmento de publicador começava em
  minúscula e não apareceu em `Get-StartApps` mesmo após novo login. O ciclo
  corretivo adotou um identificador PascalCase, igual no processo e no atalho.
- Primeiro ciclo de QA da distribuição: **REPROVADO** por atalho sem AUMID,
  documentação contraditória e ausência do repositório/release pública. AUMID
  e documentação foram corrigidos; a publicação aguardava a nova aprovação.
- Ciclo final de QA: **197 testes passaram**, hashes e smokes do instalado e do
  ZIP conferiram, atalhos e índice foram validados; **REVISOR_QA: APROVADO**.
- Repositório público: <https://github.com/pedroSalles08/MusicDownloader>.
- Primeira release pública: <https://github.com/pedroSalles08/MusicDownloader/releases/tag/v0.1.0>,
  com instalador, ZIP portátil e `SHA256SUMS.txt` disponíveis para download.
- A primeira execução remota passou nos testes, mas falhou no build porque
  `-SkipInstall` deixou o ambiente virtual local sem PyInstaller. O workflow foi
  corrigido para instalar as dependências dentro do ambiente usado pelo build.
- A execução corretiva da tag `v0.1.0` concluiu em **3 min 20 s**: testes,
  build, upload do artefato e atualização idempotente da release passaram. Os
  hashes publicados conferem com o `SHA256SUMS.txt` remoto.
