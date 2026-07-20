# Guia de trabalho dos agentes

## Missão

Entregar um aplicativo desktop Windows para preparar, revisar e baixar em MP3 músicas que o usuário possua ou tenha autorização para baixar. A fonte principal de requisitos é `promptMestre.md`; `PRODUCT.md`, `PLAN.md`, `STATUS.md`, `QUALITY_GATE.md` e `DECISIONS.md` mantêm o estado executável do projeto.

## Regras gerais

- Use Python, PySide6, yt-dlp, FFmpeg/FFprobe, pytest e PyInstaller.
- Reaproveite a lógica validada de `C:\Users\Usuario\Desktop\pessoal\scriptMusicas`, sem copiar defeitos nem acoplar a interface ao yt-dlp.
- Trabalhe em etapas pequenas. Não misture refatoração ampla com funcionalidade nova.
- Preserve `promptMestre.md`, `contextScriptMusicas.md`, `csv-example.csv` e `UI-inspirations-design.png` como entradas de referência.
- Não use texto do usuário para construir comandos de shell. Use APIs Python e argumentos estruturados.
- Não esconda erros com `except Exception` sem transformar o erro em estado compreensível e preservar diagnóstico.
- Não remova nem enfraqueça testes para obter sucesso artificial.
- Atualize `STATUS.md` depois de cada etapa aprovada, bloqueada ou concluída.
- Só faça commit de uma etapa depois de testes e revisão independente.

## Implementador

O implementador recebe uma tarefa pequena contendo objetivo, contexto, arquivos prováveis, restrições, critérios de aceitação e testes. Deve inspecionar o código antes de alterar, limitar o diff ao escopo, criar ou atualizar testes, executar as verificações relevantes e apresentar evidências. Não declara sucesso sem validação.

## Revisor QA

Durante a revisão, o revisor não corrige código. Ele inspeciona o diff, executa testes, verifica critérios de aceitação, regressões, importação CSV, responsividade, tratamento de erro e UX básica. A conclusão precisa terminar exatamente em `APROVADO` ou `REPROVADO`.

Implementador e revisor não alteram os mesmos arquivos ao mesmo tempo. Uma reprovação vira uma tarefa corretiva específica, com no máximo três ciclos antes de reorganizar o escopo ou a arquitetura.

## Convenções

- Código e identificadores técnicos em inglês quando isso favorecer integração; textos de UI e documentação para o usuário em pt-BR.
- Lógica de domínio não importa PySide6. Workers de UI apenas coordenam serviços e sinais.
- Testes automatizados não dependem de rede real; use fakes e mocks para yt-dlp e processos longos.
- Windows é a plataforma de entrega. Caminhos, caracteres reservados, FFmpeg ausente e cancelamento são casos obrigatórios.
- O link de playlist Spotify é fase 2. No MVP, detecte a URL e oriente a exportação via Exportify/CSV.

