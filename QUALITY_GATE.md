# Quality Gate

Uma etapa só é aprovada com critérios verificáveis e revisão independente. O produto só é concluído quando todos os itens do gate final estão marcados e o revisor termina com `APROVADO`.

## Testes automatizados mínimos

- [ ] Parser: uma música, várias, espaços extras, `;;`, vazios, duplicatas e caracteres especiais.
- [ ] CSV: Exportify válido, colunas alternativas, BOM, linhas incompletas, arquivo vazio e falha parcial.
- [ ] Pesquisa: falha de rede simulada, nenhum resultado, metadados e cancelamento.
- [ ] Download: falha individual sem abortar lote, progresso por item/total e cancelamento.
- [ ] Windows: nome seguro de arquivo e pasta de saída.
- [ ] Dependências: ausência de FFmpeg/FFprobe com mensagem acionável.
- [ ] UI: workers fora da thread principal, sinais de progresso e transições de estado.

## Gate funcional

- [ ] Lista por `;` funciona e deduplica.
- [ ] Importação CSV funciona com resumo e erros parciais.
- [ ] Pesquisa real retorna resultado e não baixa durante a revisão.
- [ ] Itens podem ser editados, pesquisados novamente e desmarcados.
- [ ] Download selecionado gera MP3 e continua depois de falha individual.
- [ ] Progresso, cancelamento, erros e resumo final são compreensíveis.
- [ ] FFmpeg ausente é detectado antes do lote.
- [ ] UI segue a estética retrô organizada e permanece responsiva.

## Gate de entrega

- [ ] `pytest` completo passa.
- [ ] `git diff --check` passa.
- [ ] Fluxo manual completo é registrado.
- [ ] PyInstaller gera o `.exe`.
- [ ] O `.exe` inicia corretamente em Windows.
- [ ] README descreve execução, build, uso autorizado e limitações.
- [ ] `STATUS.md` corresponde ao estado real.
- [ ] Revisão final termina exatamente em `APROVADO`.

## Evidência por etapa

Registre comandos, resultado, itens não testados e limitações. Testes de rede real complementam, mas não substituem, testes determinísticos com fakes.

