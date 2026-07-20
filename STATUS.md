# Status do projeto

Atualizado em: 2026-07-20

## Estado atual

**Em andamento — fundação.** O repositório foi inicializado e os requisitos foram inspecionados. Ainda não existe código do aplicativo, suíte de testes nem executável; nenhuma funcionalidade do produto deve ser considerada entregue neste ponto.

## Inventário confirmado

- `promptMestre.md` lido integralmente.
- `contextScriptMusicas.md` e o projeto anterior inspecionados.
- `csv-example.csv`: 159 linhas de dados, 24 colunas, títulos/artistas presentes e 158 queries únicas.
- `UI-inspirations-design.png`: painel de referências retro internet/desktop revisado.
- Ambiente: Python 3.13, FFmpeg 8.1.2, FFprobe, aria2c, Node e Git disponíveis.
- Dependências Python PySide6, yt-dlp, pytest e PyInstaller ainda não instaladas no ambiente do projeto.

## Reutilização planejada

- Busca `ytsearch1`, download de melhor áudio e pós-processamento MP3 192 kbps.
- Retry por item, fragmentos simultâneos, aria2c opcional e capa opcional.
- Comparação normalizada de cabeçalhos CSV e leitura `utf-8-sig`.

## Próximo gate

Estrutura instalável, modelos de domínio, parsers e testes aprovados por revisão independente.

## Bloqueios

Nenhum bloqueio técnico confirmado. O acesso direto a playlists Spotify permanece fora do MVP e não bloqueia a entrega.

