# Status do projeto

Atualizado em: 2026-07-20

## Estado atual

**Em andamento — interface PySide6 aprovada; iniciando empacotamento.** O
repositório contém entradas e serviços aprovados e um fluxo desktop testado
offscreen. Ainda não existem empacotamento ou executável, e a integração de
rede real ainda não foi validada.

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

## Evidência automatizada

- Ambiente criado em `.venv` com Python 3.13.14.
- Instalação editável: `.\\.venv\\Scripts\\python.exe -m pip install -e '.[dev]'` — concluída.
- Testes de domínio, serviços, workers e interface:
  `.\\.venv\\Scripts\\python.exe -m pytest` — **101 passaram em 1,86 s**.
- Regressões específicas cobrem limite UTF-16 com emoji/surrogates e CSV com
  conteúdo após aspas, aspas não fechadas, escape válido e campo multilinha.
- O teste da amostra real confirmou 159 linhas lidas, 158 queries únicas, uma
  duplicata e nenhuma linha inválida.
- Testes Qt usam plataforma offscreen; não usam rede real, extração yt-dlp real
  nem FFmpeg externo. O smoke-test abre e fecha a janela sem rede.

## Inventário confirmado

- `promptMestre.md` lido integralmente.
- `contextScriptMusicas.md` e o projeto anterior inspecionados.
- `csv-example.csv`: 159 linhas de dados, 24 colunas, títulos/artistas presentes e 158 queries únicas; expectativa agora coberta por teste automatizado.
- `UI-inspirations-design.png`: painel de referências retro internet/desktop revisado.
- Ambiente: Python 3.13, FFmpeg 8.1.2, FFprobe, aria2c, Node e Git disponíveis.
- pytest 9.1.1, pytest-qt 4.5.0, yt-dlp 2026.7.4 e PySide6 6.11.1 instalados no
  `.venv`; PyInstaller permanece fora do ambiente até o empacotamento.

## Reutilização planejada

- Busca `ytsearch1`, download de melhor áudio e pós-processamento MP3 192 kbps.
- Retry por item, fragmentos simultâneos, aria2c opcional e capa opcional.
- Comparação normalizada de cabeçalhos CSV e leitura `utf-8-sig`.

## Próximo gate

PyInstaller gera o aplicativo Windows, o `.exe` inicia corretamente e um fluxo
manual controlado confirma entrada, busca e download/conversão sem regressões.

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
- Interface, primeiro ciclo: reprovado por callbacks atrasados/fora de ordem,
  progresso regressivo, contraste/acessibilidade e concordância gramatical.
- Interface, ciclo corretivo 1: sinais carregam geração, guardas terminais e
  monotônicas foram adicionadas, ordem é normalizada e acessibilidade revisada;
  aguardando re-revisão QA.

## Bloqueios

Nenhum bloqueio técnico confirmado. O acesso direto a playlists Spotify permanece fora do MVP e não bloqueia a entrega.
