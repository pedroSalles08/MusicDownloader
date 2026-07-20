# Sistema visual retrô organizado

## Direção

A interface combina painéis de desktop dos anos 1990/2000 com a clareza de um
aplicativo atual. A referência `UI-inspirations-design.png` orienta molduras,
contraste e densidade; ela não deve ser reproduzida literalmente. O fluxo e a
legibilidade sempre vencem ornamentos.

## Tokens

- creme base: `#F4EBD8`;
- bege de painel: `#E4D5B7`;
- verde-água: `#8FCDBF`;
- azul dessaturado escuro: `#3F6078`;
- grafite: `#263238`;
- branco elevado: `#FFFDF7`;
- sucesso: `#417A5B`;
- aviso: `#754315`;
- erro: `#A13D3D`.

## Componentes

- Títulos usam fonte monoespaçada de sistema, peso alto e caixa curta.
- Seções têm borda grafite de 2 px, fundo creme e título azul/verde-água.
- Botões simulam leve bevel: borda superior/esquerda clara e borda
  inferior/direita escura; hover usa verde-água e pressionado usa bege.
- Campos e tabelas usam fundo quase branco, seleção azul e foco visível.
- Status semântico nunca depende apenas de cor: sempre há texto em pt-BR.
- Espaçamento base de 6/8/12 px; cantos discretos de 2–4 px.

## Acessibilidade e comportamento

- Texto principal mantém contraste alto sobre fundos claros.
- Azul sobre branco elevado e aviso sobre creme excedem contraste WCAG AA de
  4,5:1 para texto normal.
- Tabela e logs permanecem redimensionáveis; a janela inicia em 1180 × 780 e
  aceita redução até 900 × 640.
- Operações longas exibem texto, progresso e ação de cancelar.
- Ornamentos não piscam, não animam continuamente e não bloqueiam teclado.
