# Quality Gate

Uma etapa só é aprovada com critérios verificáveis e revisão independente. O produto só é concluído quando todos os itens do gate final estão marcados e o revisor termina com `APROVADO`.

## Testes automatizados mínimos

- [x] Parser: uma música, várias, espaços extras, `;;`, vazios, duplicatas e caracteres especiais.
- [x] CSV: Exportify válido, colunas alternativas, BOM, linhas incompletas, arquivo vazio e falha parcial.
- [x] Pesquisa: falha de rede simulada, nenhum resultado, metadados e cancelamento.
- [x] Download: falha individual sem abortar lote, progresso por item/total e cancelamento.
- [x] Windows: nome seguro de arquivo e pasta de saída.
- [x] Dependências: ausência de FFmpeg/FFprobe com mensagem acionável.
- [x] UI: workers fora da thread principal, sinais de progresso e transições de estado.

## Gate funcional

- [x] Lista por `;` funciona e deduplica.
- [x] Importação CSV funciona com resumo e erros parciais.
- [x] Pesquisa real retorna resultado e não baixa durante a revisão.
- [x] Itens podem ser editados, pesquisados novamente e desmarcados.
- [x] Download selecionado gera MP3 e continua depois de falha individual.
- [x] Progresso, cancelamento, erros e resumo final são compreensíveis.
- [x] FFmpeg ausente é detectado antes do lote.
- [x] UI segue a estética retrô organizada e permanece responsiva.

## Gate de entrega

- [x] `pytest` completo passa.
- [x] `git diff --check` passa.
- [x] Fluxo manual completo é registrado.
- [x] PyInstaller gera o `.exe`.
- [x] O `.exe` inicia corretamente em Windows.
- [x] README descreve execução, build, uso autorizado e limitações.
- [x] `STATUS.md` corresponde ao estado real.
- [x] Revisão final termina exatamente em `APROVADO`.

## Evidência por etapa

Registre comandos, resultado, itens não testados e limitações. Testes de rede real complementam, mas não substituem, testes determinísticos com fakes.
