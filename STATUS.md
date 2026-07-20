# Status do projeto

Atualizado em: 2026-07-20

## Estado atual

**Concluído — versão Windows onedir aprovada.** Entradas, serviços, interface,
build, abertura do executável, inspeção visual nativa e conversão real
controlada com yt-dlp/FFmpeg passaram por validação. O revisor QA final refez o
build e encerrou sua análise com `APROVADO`.

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

Gate concluído. Próximas evoluções opcionais podem incluir instalador,
assinatura de código e integração direta com Spotify mediante solução robusta
de autenticação; nenhuma delas bloqueia o MVP entregue.

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
