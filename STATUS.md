# Status do projeto

Atualizado em: 2026-07-20

## Estado atual

**Em andamento — domínio e entradas aprovados; iniciando serviços.** O
repositório agora contém um pacote Python instalável e uma suíte determinística
para os componentes de entrada e sistema desta etapa. Ainda não existem UI,
pesquisa/download com yt-dlp, workers, empacotamento ou executável.

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

## Evidência automatizada

- Ambiente criado em `.venv` com Python 3.13.14.
- Instalação editável: `.\\.venv\\Scripts\\python.exe -m pip install -e '.[dev]'` — concluída.
- Testes após o ciclo corretivo 1:
  `.\\.venv\\Scripts\\python.exe -m pytest` — **49 passaram em 0,14 s**.
- Regressões específicas cobrem limite UTF-16 com emoji/surrogates e CSV com
  conteúdo após aspas, aspas não fechadas, escape válido e campo multilinha.
- O teste da amostra real confirmou 159 linhas lidas, 158 queries únicas, uma
  duplicata e nenhuma linha inválida.
- Testes não usam rede real nem processos externos.

## Inventário confirmado

- `promptMestre.md` lido integralmente.
- `contextScriptMusicas.md` e o projeto anterior inspecionados.
- `csv-example.csv`: 159 linhas de dados, 24 colunas, títulos/artistas presentes e 158 queries únicas; expectativa agora coberta por teste automatizado.
- `UI-inspirations-design.png`: painel de referências retro internet/desktop revisado.
- Ambiente: Python 3.13, FFmpeg 8.1.2, FFprobe, aria2c, Node e Git disponíveis.
- pytest 9.1.1 instalado no `.venv`; PySide6, yt-dlp e PyInstaller permanecem fora do ambiente por pertencerem às próximas etapas.

## Reutilização planejada

- Busca `ytsearch1`, download de melhor áudio e pós-processamento MP3 192 kbps.
- Retry por item, fragmentos simultâneos, aria2c opcional e capa opcional.
- Comparação normalizada de cabeçalhos CSV e leitura `utf-8-sig`.

## Próximo gate

Serviços de pesquisa e download com yt-dlp, progresso, cancelamento e isolamento
de falhas cobertos por testes determinísticos e aprovados por QA independente.

## Revisão da etapa

- Primeiro ciclo: reprovado por limite de nome baseado em pontos de código e
  parsing CSV permissivo.
- Ciclo corretivo 1: limite alterado para unidades UTF-16 e parser CSV estrito
  com recuperação por linha.
- Resultado final: **49 testes passaram; REVISOR_QA: APROVADO**.

## Bloqueios

Nenhum bloqueio técnico confirmado. O acesso direto a playlists Spotify permanece fora do MVP e não bloqueia a entrega.
