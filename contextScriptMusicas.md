# Contexto do Projeto — Script/App de Download de Músicas

## Quem sou e contexto geral
Sou estudante do Curso Técnico em Informática no IFFar (Instituto Federal Farroupilha –
Campus Júlio de Castilhos). Esse projeto começou de uma necessidade prática: curar e
baixar playlists de MP3 organizadas por gênero pra um caminhoneiro, e evoluiu pra uma
ideia maior de app desktop.

Fluxo de trabalho que uso: planejo/arquiteto as ideias com uma IA (Claude), e delego a
implementação de código pra outra ferramenta (Codex). Prefiro soluções objetivas e
funcionais — não precisa ser bonito, precisa funcionar.

---

## Objetivo geral do projeto
1. **Curto prazo (já em andamento):** um script Python funcional que recebe uma lista de
   nomes de músicas separadas por ";" e baixa o MP3 de cada uma via yt-dlp.
2. **Longo prazo (planejamento, ainda não iniciado):** um app desktop com interface
   gráfica, usando yt-dlp (+ spotdl/spotify-dlp) pra download de músicas/vídeos de
   grandes plataformas, com um diferencial de criação automatizada de playlists via IA.

---

## Contexto original: curadoria de playlists por gênero
Antes do script, eu tinha uma coleção de MP3 organizada em pastas por gênero (num
diretório local), com uma média de 50-150 músicas por gênero:

- **Boêmias** (dupla romântica/sertanejo raiz): Chico Rey & Paraná, Teodoro & Sampaio,
  Gilberto & Gilmar, Mato Grosso & Matias, Milionário & José Rico, Trio Parada Dura,
  Joaquim & Manuel, Eduardo Costa
- **Internacional** (dance/pop remix, tropical house): Vintage Culture, Tiësto, MEDUZA,
  Felix Jaehn, Glockenbach, La Bouche, Ace Hood, Masked Wolf
- **Reggae**: na verdade é mais uma cena de "reggae remix" nacional (produtoras/DJs
  remixando faixas eletrônicas em versão reggae) do que artistas fixos com carreira —
  ex: Infinity Project / ID Produções, FZIRO NO BEAT
- **Rock**: Bob Dylan, Bruce Springsteen, Creedence Clearwater Revival, Eric Clapton,
  Guns N' Roses, Queen, Ramones, Red Hot Chili Peppers, Sheryl Crow, Skank
- **Sertanejo**: Bruno & Marrone, Jorge & Mateus, Ícaro & Gilmar, Humberto & Ronaldo,
  Panda, Flávio Pizada Quente

A partir disso, já foram identificados artistas do mesmo estilo pra pesquisar (ex:
Chitãozinho & Xororó, César Menotti & Fabiano, Henrique & Juliano, Gusttavo Lima, Ana
Castela, Alok, David Guetta, Rolling Stones, Foo Fighters, entre outros), e já foram
geradas duas listas grandes de músicas reais (não inventadas, verificadas via busca ou
conhecimento geral confiável) prontas no formato ";" pra alimentar o script — uma
focada em lançamentos recentes (~155 músicas) e outra usando os artistas sugeridos
adicionais + clássicos já conhecidos (~200 músicas). Ambas no formato
`Título Artista;Título Artista;...`.

---

## Status atual: script `baixar.py` (já funcionando)

**O que ele faz:**
- Recebe uma lista de músicas separadas por ";", passada como argumento de linha de
  comando ou digitada via `input()` se nenhum argumento for passado
- Aceita flags `--capa` / `--sem-capa` (embute ou não a thumbnail do vídeo como capa/arte
  do álbum no MP3); sem nenhuma flag, o script pergunta interativamente antes de baixar
- Usa **yt-dlp como biblioteca Python** (`import yt_dlp`, não subprocess/shell) — busca
  cada música com `ytsearch1:<nome da música>` e baixa o melhor áudio disponível
- Converte pra **MP3 192kbps** usando os postprocessors nativos do yt-dlp
  (`FFmpegExtractAudio`, `FFmpegMetadata`, `EmbedThumbnail`)
- Salva os arquivos numa pasta `downloads/`
- Trata erro por música individualmente (uma falha não interrompe o resto da lista) e
  imprime um resumo de sucessos/falhas no final
- **Otimização de velocidade:** `concurrent_fragment_downloads: 8` nas opções do yt-dlp,
  mais detecção automática de `aria2c` no PATH (via `shutil.which`) — se disponível, usa
  aria2c como downloader externo (`-x 16 -s 16 -k 1M`); se não, cai no downloader padrão
  do yt-dlp sem travar nem dar erro, só avisa no console

**Dependências:**
- Python 3
- `yt-dlp` (pip)
- `ffmpeg` — precisa estar instalado e no PATH do sistema (testar com `ffmpeg -version`;
  no Windows, instalar com `winget install ffmpeg`)
- Opcional: `aria2c` (`winget install aria2`) pra acelerar downloads

**Gotchas já resolvidos/conhecidos:**
- **PowerShell:** usar sempre **aspas duplas** (`"..."`) ao passar a lista como
  argumento, nunca aspas simples (`'...'`) — várias músicas têm apóstrofo (ex:
  "Don't Stop Me Now") e aspas simples quebram o parsing do PowerShell, causando erro
  de sintaxe (`MissingOpenParenthesisInIfStatement` ou parecido)
- **Velocidade de download baixa** (~100-150 KiB/s mesmo com internet de 200 mega) é
  throttling do lado do servidor do YouTube, não é limitação da conexão do usuário —
  mitigado com `concurrent_fragment_downloads` e `aria2c`
- Argumentos muito longos no PowerShell podem eventualmente dar problema de tamanho —
  se acontecer, a alternativa é o script ler a lista de um arquivo `.txt` em vez de
  receber por linha de comando

---

## Feature planejada (ainda não implementada): importar playlist do Spotify

**Objetivo:** pegar o nome das músicas de uma playlist do Spotify pra alimentar o
`baixar.py` — sem precisar baixar áudio direto do Spotify (que é protegido/difícil),
já que praticamente tudo que existe no Spotify também existe no YouTube.

**Contexto importante — restrições do Spotify em 2026:**
- Fev/Mar 2026 o Spotify restringiu bastante o "Development Mode" da API de
  desenvolvedor. Isso quebrou o fluxo de autenticação que ferramentas como o spotDL
  usavam (compartilhar um client ID entre muitos usuários agora viola os termos e é
  bloqueado rapidamente)
- O Spotify também está "se afastando do fluxo Client Credentials para endpoints de
  metadados" — ou seja, até só *ler* dados de playlist (sem baixar nada) ficou mais
  burocrático
- Development Mode agora exige conta Spotify Premium
- **Implicação prática:** qualquer parte do projeto que dependa da API do Spotify
  (download via spotdl/spotify-dlp, ou só leitura de metadados de playlist) só é
  viável de forma confiável pro **uso pessoal** (com app própria registrada + login
  próprio), não pra distribuir livremente pra outros usuários

**Caminho recomendado (mais simples, evita lidar com as restrições de API):**
1. Usar **Exportify** (exportify.net) — ferramenta gratuita, login é do próprio usuário
   (sem precisar registrar app no Spotify for Developers), exporta qualquer playlist
   pra **CSV** com nome da música, artista, álbum etc.
2. Um script Python (a implementar) lê esse CSV (`csv.DictReader`, detectando variações
   de nome de coluna tipo "Track Name"/"Artist Name(s)") e monta automaticamente a
   string ";" no formato que o `baixar.py` espera

**Caminho alternativo (mais automatizado, mais trabalho de setup):**
- Usar a biblioteca `spotipy` com **Authorization Code flow** (login do próprio usuário,
  não Client Credentials) — permite ler playlists direto por código sem exportar CSV
  manualmente toda vez, mas exige conta Spotify Premium e uma app própria registrada

---

## Ideia do app desktop completo (planejamento em aberto)

**Stack sugerida** (reaproveitando o que já uso em outros projetos, ex: OrbitalAuto):
- Backend em Python (FastAPI), chamando yt-dlp/spotdl como biblioteca (nunca via
  shell/subprocess construído a partir de texto livre — risco de command injection)
- Interface gráfica: **pywebview** (janela nativa renderizando um frontend
  Next.js/React exportado como estático) pra começar rápido reaproveitando o que já
  sei; migrar pra **Tauri** (shell Rust + sidecar Python) depois se precisar de algo
  mais robusto pra distribuir

**Divisão do projeto:**
- Parte yt-dlp (GUI + download): **gratuita**, pra disponibilizar pra todo mundo
- Parte Spotify (spotdl/spotify-dlp): provavelmente só uso pessoal, pelas restrições
  de API descritas acima

**Diferencial — IA que cria playlists automaticamente:**
- **Modo restrito:** lista de músicas separada por ";" (sem IA nenhuma — zero custo,
  zero risco de segurança, é só parsing de string)
- **Modo prompt livre:** usuário descreve o que quer (artistas/estilo), a IA interpreta
  e devolve uma lista estruturada `{artista, música}`, podendo sugerir músicas
  parecidas (esse é o tipo de coisa que já foi feita manualmente nesta conversa, pra
  boêmia/sertanejo/rock/eletrônico)
- **Escolha de modelo:** a tarefa é extração estruturada, não exige modelo caro — um
  modelo barato (ex: DeepSeek V4 Flash, ~$0,14/$0,28 por milhão de tokens; ou Gemini
  Flash, GPT-4o-mini, Claude Haiku) já resolve. O gargalo real não é "inteligência" do
  modelo, é **cobertura de conhecimento sobre música regional brasileira** (nichada) —
  vale testar empiricamente 2-3 modelos com prompts reais antes de escolher
- **Mitigar alucinação:** não confiar só na memória da IA pra "lançamentos recentes"
  (ela tem data de corte) — cruzar com uma API real e gratuita tipo Last.fm (tem
  "artistas similares") ou MusicBrainz
- **Segurança real (não é sobre "jailbreak"):** o risco que importa é injeção de
  comando, se a saída da IA (ou texto do usuário) for usada pra montar comandos de
  shell sem validação. A solução é: nunca montar strings de shell a partir de texto
  livre, usar yt-dlp como biblioteca Python direto, e validar a saída da IA contra um
  schema JSON fixo antes de usar pra qualquer coisa

**Busca manual (parte sem IA, base do app):**
- Uma barra de busca única que aceita URL direta OU texto livre (detectado por regex
  simples tipo `^https?://`)
- Se for busca: usa `ytsearchN:<query>` via yt-dlp (`extract_flat: "in_playlist"` pra
  ser rápido) e mostra resultados numa grid (thumbnail, título, canal, duração) pro
  usuário escolher visualmente — isso resolve a ambiguidade de covers/ao vivo/lyric
  video sem precisar de heurística automática
- Truque: a URL da thumbnail pode ser montada direto a partir do ID do vídeo
  (`https://i.ytimg.com/vi/{id}/hqdefault.jpg`), sem esperar metadado extra
- Fila de download (tipo carrinho) + seletor de pasta destino (reaproveitando a lógica
  de pastas por gênero que já uso) + lista de progresso em tempo real via
  `progress_hooks` do yt-dlp
- URLs de playlist do YouTube devem ser detectadas e expandidas na lista completa de
  faixas

**Ordem de construção sugerida:**
1. GUI simples + yt-dlp funcionando por URL/busca manual (já é útil sozinho)
2. Suporte a lote/playlist e organização por pasta
3. Modo ";" restrito (sem custo, sem IA) — **é o que já está pronto hoje**
4. Modo prompt livre com IA, como feature opcional/pessoal (chave de API própria)
5. Empacotamento pra distribuição pública (só a parte yt-dlp)
