Você será o agente supervisor de um experimento de desenvolvimento autônomo de software.



Seu objetivo é coordenar agentes especializados até entregar um aplicativo desktop funcional para Windows. Você deve planejar, delegar, revisar, testar e corrigir o projeto sem depender de prompts manuais após o início.



\# CONTEXTO DO PROJETO



Existe um projeto anterior em forma de script Python funcional. Você deve inspecionar e reaproveitar esse contexto como base técnica, não reescrever tudo do zero sem motivo.



Há também uma imagem de referência de estilo visual. A interface do app final deve seguir essa direção estética: retro internet / old web / desktop UI vintage.



Use o contexto existente como ponto de partida para acelerar e reduzir risco.



\# OBJETIVO DO PRODUTO



Criar um aplicativo desktop para Windows que permita baixar músicas em MP3 usando yt-dlp como backend.



O app deve aceitar múltiplas formas de entrada e transformar tudo em uma fila de músicas para pesquisa e download no YouTube.



O aplicativo é destinado apenas ao download de conteúdo que o usuário possua ou tenha autorização para baixar.



\# REQUISITOS DE ENTRADA



O app deve suportar:



\## 1) Lista separada por ponto e vírgula

Exemplo:

Música A - Artista; Música B - Artista; Música C - Artista



O app deve:

\- quebrar a entrada por `;`

\- remover espaços extras

\- ignorar entradas vazias

\- detectar duplicatas

\- transformar isso numa lista normalizada de itens para busca



\## 2) Importação de CSV de playlist do Spotify

O usuário deve poder importar um arquivo `.csv` contendo músicas de uma playlist do Spotify, especialmente no formato exportado por ferramentas como Exportify.



O app deve:

\- ler o CSV com robustez

\- detectar colunas com nomes variáveis, por exemplo:

&#x20; - `Track Name`

&#x20; - `Track Name(s)`

&#x20; - `Artist Name`

&#x20; - `Artist Name(s)`

&#x20; - ou equivalentes

\- combinar título + artista em uma query apropriada

\- transformar as faixas em uma fila de busca interna

\- mostrar quantas músicas foram importadas com sucesso

\- lidar com linhas inválidas sem travar a importação inteira



\## 3) Link público de playlist do Spotify (opcional / fase 2)

Se houver tempo e viabilidade técnica, implemente suporte a colar uma URL pública de playlist do Spotify.



Porém:

\- isso NÃO deve bloquear a entrega do app

\- se depender de autenticação, scraping frágil ou setup excessivo, trate como feature opcional

\- o MVP obrigatório é:

&#x20; - lista por `;`

&#x20; - importação de CSV do Spotify



Se a importação direta por link não for robusta o suficiente, o app deve pelo menos:

\- detectar que é um link do Spotify

\- informar claramente ao usuário que ele pode exportar a playlist para CSV e importar o arquivo no app



\# REUTILIZAÇÃO DO SCRIPT EXISTENTE



Há um script anterior já funcional que:

\- recebe lista de músicas separadas por `;`

\- usa `yt\_dlp` como biblioteca Python

\- faz `ytsearch1:<query>`

\- baixa melhor áudio

\- converte para MP3

\- usa FFmpeg

\- trata falhas por item

\- pode embutir capa

\- tem otimizações como uso opcional de aria2c



Você deve aproveitar essa lógica sempre que fizer sentido.



Prefira:

\- extrair a lógica reutilizável para módulos

\- criar uma camada de serviço / backend interno

\- manter o comportamento já validado

\- só alterar a arquitetura quando houver justificativa clara



\# STACK PREFERENCIAL



Use preferencialmente:

\- Python

\- PySide6 para interface desktop

\- yt-dlp como biblioteca Python

\- FFmpeg / FFprobe

\- pytest

\- PyInstaller para gerar `.exe`



Somente altere essa stack se houver impedimento técnico real. Se alterar, documente a decisão em `DECISIONS.md`.



\# FUNCIONAMENTO ESPERADO



O app deve permitir:



1\. inserir uma lista de músicas separadas por `;`

2\. importar um CSV de playlist do Spotify

3\. opcionalmente colar uma URL de playlist do Spotify

4\. escolher pasta de destino

5\. pesquisar cada música no YouTube antes do download

6\. mostrar uma tela de revisão dos resultados encontrados

7\. exibir para cada item, quando disponível:

&#x20;  - termo pesquisado

&#x20;  - título encontrado

&#x20;  - canal

&#x20;  - duração

&#x20;  - status

8\. permitir desmarcar itens incorretos

9\. permitir editar a query e pesquisar novamente

10\. baixar os itens selecionados

11\. converter para MP3

12\. mostrar progresso por item e progresso total

13\. manter a interface responsiva durante pesquisa e download

14\. cancelar operações

15\. continuar o lote mesmo se uma música falhar

16\. mostrar erros compreensíveis

17\. tratar nomes de arquivo inválidos no Windows

18\. detectar ausência de FFmpeg e orientar o usuário

19\. gerar executável para Windows



\# ESTILO VISUAL OBRIGATÓRIO



A interface deve seguir a imagem de referência anexa.



Direção visual esperada:

\- retro internet aesthetic

\- old web / old desktop UI

\- vibe de interfaces dos anos 90 / início dos 2000

\- caixas, painéis e divisões bem marcadas

\- botões com aspecto retrô

\- barra de status / painéis informativos

\- tipografia que remeta a bitmap / sistema antigo, mas sem sacrificar legibilidade

\- paleta suave com tons como bege, cinza, verde-água, azul dessaturado, creme e detalhes contrastantes

\- aparência nostálgica e charmosa

\- sensação de “aplicativo retro de internet”, não de dashboard moderna padrão



Mas atenção:

\- o app deve continuar limpo e utilizável

\- evitar poluição visual excessiva

\- a interface não pode ficar bagunçada como um site antigo caótico

\- o estilo deve ser retrô, porém organizado



Crie um pequeno sistema visual documentado:

\- cores

\- tipografia

\- botões

\- painéis

\- status badges

\- listas/tabelas

\- estados de progresso e erro



\# FLUXO DE TELAS



O app deve ter algo próximo de:



1\. Tela principal

&#x20;  - campo grande para lista com `;`

&#x20;  - botão para importar CSV

&#x20;  - campo opcional para link de playlist

&#x20;  - escolha da pasta destino

&#x20;  - botão “Preparar lista” ou “Pesquisar músicas”



2\. Tela / área de revisão

&#x20;  - lista dos resultados encontrados

&#x20;  - status por item

&#x20;  - opção de editar query e pesquisar novamente

&#x20;  - opção de remover/desmarcar itens



3\. Tela / área de downloads

&#x20;  - fila

&#x20;  - progresso por item

&#x20;  - progresso total

&#x20;  - logs resumidos

&#x20;  - botão cancelar



4\. Resumo final

&#x20;  - quantas músicas baixadas com sucesso

&#x20;  - quantas falharam

&#x20;  - quais falharam

&#x20;  - pasta de saída



\# DOCUMENTAÇÃO PERSISTENTE



Antes de programar, crie e mantenha:

\- `AGENTS.md`

\- `PRODUCT.md`

\- `PLAN.md`

\- `STATUS.md`

\- `QUALITY\_GATE.md`

\- `DECISIONS.md`

\- `README.md`



Esses arquivos são a fonte persistente de contexto.



\# PAPÉIS



Você é o SUPERVISOR.



Crie e coordene pelo menos os seguintes subagentes:



\## IMPLEMENTADOR

Pode alterar o código.



Recebe uma tarefa pequena por vez com:

\- objetivo

\- contexto

\- arquivos prováveis

\- restrições

\- critérios de aceitação

\- testes obrigatórios



Ele deve:

\- inspecionar o código antes de alterar

\- implementar apenas o escopo da tarefa

\- criar ou atualizar testes

\- executar testes relevantes

\- mostrar evidências

\- não declarar sucesso sem validação



\## REVISOR\_QA

Não deve corrigir o código durante a revisão.



Ele deve:

\- revisar o diff

\- executar testes

\- verificar critérios de aceitação

\- procurar regressões

\- avaliar UX básica

\- avaliar robustez da importação CSV

\- avaliar responsividade da interface

\- avaliar tratamento de erro



A resposta dele deve terminar com exatamente:

\- `APROVADO`

ou

\- `REPROVADO`



\# REGRAS DE COORDENAÇÃO



1\. Não permita que implementador e revisor alterem os mesmos arquivos ao mesmo tempo.

2\. Trabalhe em etapas pequenas.

3\. Não considere uma etapa pronta só porque o implementador afirmou isso.

4\. Sempre valide com testes e revisão independente.

5\. Em caso de reprovação, transforme os problemas em prompt corretivo específico.

6\. Faça no máximo 3 ciclos corretivos por tarefa.

7\. Se 3 ciclos falharem, reorganize a tarefa ou a arquitetura.

8\. Atualize `STATUS.md` após cada etapa aprovada ou bloqueada.

9\. Faça commits pequenos por etapa aprovada.

10\. Não misture refatoração grande com funcionalidade nova sem necessidade.

11\. Não esconda erros com `try/except` genérico.

12\. Não remova testes apenas para fazê-los passar.

13\. Não declare o projeto pronto sem gerar e testar o executável.



\# ORDEM DE CONSTRUÇÃO SUGERIDA



1\. Inicializar estrutura do projeto e documentação

2\. Inspecionar e reaproveitar a lógica do script existente

3\. Criar parser da lista por `;`

4\. Criar importador de CSV do Spotify

5\. Criar camada de serviço para pesquisa via yt-dlp

6\. Criar camada de download/conversão

7\. Criar interface básica

8\. Integrar pesquisa assíncrona

9\. Implementar revisão dos resultados

10\. Implementar fila de downloads e progresso

11\. Implementar cancelamento e tratamento de falhas

12\. Aplicar o estilo retro internet aesthetic

13\. Escrever e melhorar testes

14\. Gerar executável com PyInstaller

15\. Validar manualmente um fluxo completo

16\. Revisão final



\# TESTES MÍNIMOS



Inclua testes para:

\- parser com 1 música

\- parser com várias músicas

\- espaços extras

\- `;;` repetidos

\- entradas vazias

\- duplicatas

\- caracteres especiais

\- CSV válido

\- CSV com colunas alternativas

\- CSV com linhas incompletas

\- CSV vazio

\- falha parcial na importação

\- falha de rede simulada

\- nenhum resultado encontrado

\- falha em uma música sem abortar o lote

\- cancelamento

\- atualização de progresso

\- geração segura de nome de arquivo

\- ausência de FFmpeg



Evite depender da rede real em todos os testes automatizados. Use mocks e fakes quando possível.



\# GATE FINAL



Só conclua o projeto quando:

\- lista por `;` funcionar

\- importação de CSV funcionar

\- pesquisa funcionar

\- revisão funcionar

\- download funcionar

\- progresso funcionar

\- erros forem tratados

\- UI estiver coerente com a estética retrô pedida

\- testes passarem

\- o revisor final emitir `APROVADO`

\- o `.exe` for gerado

\- o `.exe` iniciar corretamente

\- houver pelo menos um fluxo manual validado



\# ENTREGA FINAL



Ao terminar, apresente:

1\. resumo do app entregue

2\. arquitetura usada

3\. quais partes vieram do script anterior

4\. funcionalidades implementadas

5\. testes executados

6\. caminho do executável

7\. como rodar em desenvolvimento

8\. como gerar novamente o `.exe`

9\. limitações conhecidas

10\. status da feature de link do Spotify

11\. confirmação final do revisor



Comece agora inspecionando os arquivos existentes, criando a documentação persistente e montando o plano de execução.

# MODO DE EXECUÇÃO AUTÔNOMA



Este é um experimento de desenvolvimento autônomo e o usuário poderá ficar ausente durante a execução.



Portanto:



1\. Não pare após criar o plano ou a documentação.

2\. Continue automaticamente para a implementação.

3\. Depois de cada implementação, execute testes e solicite revisão.

4\. Quando houver reprovação, gere e execute o próximo ciclo corretivo.

5\. Não peça confirmação para decisões técnicas pequenas e reversíveis.

6\. Em caso de dúvida não crítica, escolha a alternativa mais simples, segura e documentada.

7\. Só interrompa para perguntar ao usuário quando existir:

&#x20;  - necessidade de credencial ou segredo;

&#x20;  - ação destrutiva irreversível;

&#x20;  - impedimento técnico que não possa ser contornado;

&#x20;  - decisão de produto com consequências importantes e sem resposta no contexto.

8\. Se uma funcionalidade opcional bloquear o desenvolvimento, registre a limitação e continue com o restante do MVP.

9\. Priorize primeiro uma versão funcional, testada e empacotável; faça o refinamento visual depois.

10\. Continue trabalhando até satisfazer o gate final ou encontrar um bloqueio real.

11\. Ao encontrar um bloqueio, deixe o repositório em estado estável, atualize STATUS.md e explique exatamente o que falta.

12\. Não considere a criação dos arquivos AGENTS.md, PRODUCT.md, PLAN.md e STATUS.md como conclusão da tarefa. Eles são apenas o início da execução.

