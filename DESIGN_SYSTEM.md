# Sistema visual dark progressivo

## Direção

A interface combina a clareza e o acabamento de aplicativos modernos do macOS
com o comportamento esperado de um aplicativo Windows. A moldura, os controles
de janela e os seletores de arquivos permanecem nativos; o conteúdo usa
hierarquia, espaço, tipografia e contraste para produzir uma aparência premium.

O fluxo mostra apenas a etapa atual:

`Adicionar → Pesquisar → Revisar → Baixar → Concluído`

Não são usados sidebar, dashboard, janela frameless, imitação dos traffic
lights, thumbnails remotas ou grandes cards por faixa.

## Tokens

- fundo: `#0E0E10`;
- superfície: `#17171A`;
- hover/seleção: `#202025`;
- separador: `#2C2C2E`;
- texto principal: `#F5F5F7`;
- texto secundário: `#A1A1A6`;
- texto terciário: `#6E6E73`;
- ação e foco: `#0A84FF`;
- sucesso: `#32D74B`;
- aviso: `#FF9F0A`;
- erro: `#FF453A`.

Espaçamento usa a escala 4/8/12/16/24/32 px. Controles usam raio de 8 px e
superfícies/popovers 10–12 px. A fonte preferencial é `Segoe UI Variable`, com
fallback para `Segoe UI`.

## Componentes

- `AppShell` usa `QStackedWidget` e preserva a title bar nativa do Windows.
- A entrada universal concentra nomes, vídeos e playlists do YouTube.
- Importação CSV/Spotify e opções técnicas ficam em popovers discretos.
- A revisão usa `ReviewListModel` e `ReviewItemDelegate`, com linhas de 64 px,
  checkbox, ícone local, título, metadados, duração, status e menu contextual.
- Pesquisa e download possuem telas minimalistas próprias.
- Logs técnicos e erros detalhados ficam recolhidos por padrão.
- A conclusão apresenta uma única mensagem principal e expande falhas apenas
  quando existirem.
- Ícones são SVGs originais incorporados pelo Qt Resource System; nenhum asset
  visual depende de rede.

## Estados e interação

- hover, pressed e foco são sempre visíveis e discretos;
- animações duram 120–180 ms e nunca controlam transições funcionais;
- seleção e ação principal usam azul sem dominar a interface;
- aviso, erro e sucesso usam cor, texto e forma, nunca apenas cor;
- estados sem dados não exibem controles de revisão ou atividade;
- ações principais informam contexto, como `Baixar 7 músicas`.

## Windows, acessibilidade e responsividade

- janela inicial de 1060 × 760 e mínimo de 720 × 600;
- layouts Qt permanecem fluidos para resize, maximização e Snap;
- seletores de arquivos/pastas são nativos;
- atalhos Ctrl, Tab, clique direito, tecla Menu e `Shift+F10` são preservados;
- nomes e descrições acessíveis acompanham os campos e vistas principais;
- a lista expõe texto acessível, seleção e estado pelo model/view;
- foco visível e contraste de texto atendem WCAG AA nos tokens principais;
- validar manualmente 100%, 125%, 150% e 200% de escala no Windows.
