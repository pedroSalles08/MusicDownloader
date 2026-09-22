# Sistema visual Midnight Deck

## Direção

O Music Downloader mantém o fluxo dark e progressivo do redesign, mas abandona
a aparência de “app dark genérico”. A interface se inspira em decks de áudio e
ferramentas de preparação musical: fundo grafite azulado, texto levemente
quente, microtextos utilitários e sinais de azul mineral e âmbar.

A assinatura visual é a **linha de fluxo em forma de playhead** no cabeçalho.
Ela representa etapas reais, não decoração:

`Adicionar → Pesquisar → Revisar → Baixar → Concluído`

A moldura e os diálogos continuam nativos do Windows. Não são usados sidebar,
dashboard, janela frameless, imitação de controles do macOS, thumbnails remotas,
texturas pesadas ou efeitos nostálgicos que prejudiquem a leitura.

## Tokens

- fundo / `BACKGROUND`: `#0B0F14`;
- superfície / `SURFACE`: `#141A22`;
- superfície ativa / `SURFACE_HOVER`: `#1B2430`;
- separador / `SEPARATOR`: `#303B49`;
- texto principal / `TEXT_PRIMARY`: `#F2EFE7`;
- texto secundário / `TEXT_SECONDARY`: `#B4BDC8`;
- texto terciário / `TEXT_TERTIARY`: `#7F8A98`;
- ação e foco / `ACCENT`: `#78A7FF`;
- marcador de contexto / `CUE`: `#E7B56C`;
- sucesso / `SUCCESS`: `#67C587`;
- erro / `ERROR`: `#F07A77`.

Espaçamento usa a escala 4/8/12/16/24/32 px. Controles usam raio de 8 px,
superfícies 10–12 px e bordas estáveis de 1 px. Cor semântica nunca aparece sem
texto ou forma correspondente.

## Tipografia

- títulos: `Segoe UI Variable Display`, peso 650, com fallback para Segoe UI;
- corpo e controles: `Segoe UI Variable` / `Segoe UI`;
- etapas, contagens e rótulos utilitários: `Cascadia Mono` / `Consolas`.

A fonte monoespaçada é restrita a informação operacional. Ela cria a lembrança
de equipamento musical sem transformar todo o app em um terminal.

## Componentes e hierarquia

- `AppShell` mantém uma barra superior de 66 px com marca, propósito do produto,
  etapa textual (`03 / 05 · REVISAR`) e o playhead de cinco pontos.
- A entrada possui rótulo persistente, contagem de itens e aviso neutro de
  duplicatas. O CTA passa de `Pesquisar músicas` para `Pesquisar N itens`.
- O perfil de saída fica visível nos botões `MP3 · 192 kbps`, `FLAC` ou
  `MP4 compatível · até 1080p`; o popover continua concentrando as opções
  avançadas.
- Botões usam SVGs locais de uma única família, sempre acompanhados por texto.
  Rótulos descrevem a ação: `Importar lista`, `Escolher pasta`, `Trocar pasta`,
  `Mostrar log técnico` e `Adicionar nova lista`.
- A revisão usa `ReviewListModel` e `ReviewItemDelegate`. Cada faixa exibe
  seleção, título, metadados, duração, status em cápsula textual e um affordance
  de ações. A contagem selecionada fica visível fora do CTA.
- O dock inferior da revisão agrupa destino, motivo de bloqueio/prontidão e a
  única ação primária da tela. O CTA curto (`Baixar 3 áudios`) não repete o
  perfil, pois ele já está visível no cabeçalho.
- Pesquisa mostra progresso determinístico (`2 de 4 analisados · 2 encontradas`)
  e download mantém progresso total, faixa atual e log técnico recolhido.

## Estados e interação

- hover, pressed, foco e disabled são visualmente diferentes sem mudar o
  tamanho do controle;
- ações desabilitadas possuem orientação próxima: falta de entrada, seleção,
  destino ou configuração válida;
- a navegação de volta preserva entrada, seleção, rolagem e destino;
- a transição por opacidade só roda quando o estilo Qt informa que animações de
  widgets estão habilitadas;
- popovers preservam a divulgação progressiva de CSV/Spotify, formato, capa e
  sessão do YouTube;
- erros informam causa e recuperação, enquanto logs técnicos permanecem
  recolhidos por padrão.

## Windows, acessibilidade e responsividade

- janela inicial de 1060 × 760 e mínimo de 720 × 600;
- layouts Qt permanecem fluidos para resize, maximização e Snap;
- o dock de download usa elipse no meio para caminhos longos e mantém o caminho
  completo em tooltip e nome acessível;
- foco acompanha a tela ativa e a ordem de Tab segue a ordem visual;
- todos os ícones são vetoriais locais; nenhum asset depende de rede;
- contraste dos textos principal, secundário e terciário, do foco e do texto
  sobre o botão primário é verificado por teste automatizado;
- listas longas rolam sem ocultar o dock de ação;
- validar manualmente 100%, 125%, 150% e 200% de escala no Windows antes de uma
  release pública.
