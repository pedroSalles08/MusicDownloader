# Plano de execução

## Etapa 0 — Fundação

- [x] Inspecionar prompt, contexto, CSV real, imagem e projeto anterior.
- [x] Inicializar o repositório Git.
- [x] Criar documentação persistente.
- [x] Criar estrutura Python, ambiente e configuração de testes/build.

## Etapa 1 — Domínio e entradas

- [x] Modelar resultados de importação e dependências.
- [x] Implementar parser de lista por `;` com deduplicação estável.
- [x] Implementar CSV robusto e resumo de linhas inválidas/duplicadas.
- [x] Implementar saneamento de nomes Windows e detecção de dependências.
- [x] Cobrir casos mínimos com pytest.

## Etapa 2 — Serviços

- [x] Extrair configuração reutilizável do yt-dlp.
- [x] Implementar pesquisa sem download e mapeamento de metadados.
- [x] Implementar download MP3, capa opcional, hooks de progresso e resumo.
- [x] Implementar cancelamento cooperativo e continuação após falha.
- [x] Testar com fakes/mocks, incluindo rede, nenhum resultado e falha parcial.

## Etapa 3 — Interface

- [x] Criar janela PySide6 com entrada, importação, Spotify/fallback e destino.
- [x] Criar tabela de revisão editável/selecionável e nova pesquisa.
- [x] Criar painel de downloads, progresso por item/total, logs e resumo.
- [x] Integrar workers Qt sem bloquear a thread de UI.
- [x] Aplicar e documentar o sistema visual retrô.

## Etapa 4 — Robustez e empacotamento

- [ ] Executar suíte completa e análise do diff.
- [ ] Validar manualmente parser, CSV real e fluxo controlado de pesquisa/download.
- [ ] Criar spec/receita PyInstaller e gerar `.exe`.
- [ ] Abrir o executável e registrar evidência.
- [ ] Fazer revisão QA final e corrigir até aprovação.

## Estratégia de commits

Um commit pequeno após cada etapa aprovada: fundação; domínio/importação; serviços; UI; robustez; pacote final. Arquivos de entrada fornecidos pelo usuário permanecem versionados como referência, salvo decisão documentada em contrário.
