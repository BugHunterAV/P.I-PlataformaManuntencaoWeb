# Análise de tendências e OS preditiva

## Diagnóstico

O projeto já possuía `Sensor`, `Telemetria`, `TrendConfig`, regressão linear,
dashboard de tendências, alertas por limite, OS automáticas e integração com
Gemini. A consulta original ordenava leituras do passado para o presente e
aplicava o limite antes de selecionar as mais recentes; com mais registros que
o limite, a amostra podia ficar desatualizada. Alertas por limite também não
tinham vínculo com sensor ou evento, e a deduplicação de OS dependia de texto.

## Regra matemática

`TrendConfig` continua sendo a fonte da janela, quantidade de leituras e
sensibilidade. A rotina busca primeiro as leituras mais novas dentro da janela,
remove valores não finitos e mantém uma leitura por timestamp. Só então ordena
cronologicamente e calcula regressão linear em unidades por hora. Menos de três
leituras produz `insufficient_data=true`, sem projeção ou alerta preditivo.

O sensor atual possui limite operacional superior. Assim, aumento persistente é
aproximação do limite; redução persistente é apresentada no dashboard, mas não é
classificada como risco de limite superior. A projeção só existe para inclinação
positiva e valor abaixo do limite. É uma estimativa matemática, não uma data de
falha.

Risco: `baixo` para condição normal ou distante, `medio` para aproximação ou
proximidade configurada, `alto` quando a projeção fica próxima e `critico` para
limite ultrapassado ou projeção imediata. A geração preditiva exige tendência
crescente e risco `medio`, `alto` ou `critico`; a OS só é aberta para risco
`alto`/`critico` ou projeção em até 24 horas.

## Alertas, episódios e OS

Alertas de tendência usam `origem=tendencia`, o sensor, `dados_analise`, um
`evento_chave` estável (`tendencia:<sensor>:<direção>`) e a análise opcional do
Gemini. Enquanto o episódio está ativo, a mesma linha é atualizada. Quando a
condição deixa de ser relevante ou muda de direção, o alerta é resolvido e o
histórico permanece. A restrição parcial `alerta_evento_ativo_unico` protege a
criação simultânea no banco.

A OS preditiva aponta para `alerta_origem` e `sensor_origem`. Essa relação
OneToOne evita duplicidade em reprocessamentos, permite elevar a prioridade sem
criar outra ordem e libera um novo episódio depois que o anterior for resolvido.
Falha ou indisponibilidade do Gemini não interfere no alerta nem na OS.

Alertas de limite existentes mantêm o comportamento anterior para preservar a
compatibilidade da aplicação.

## Execução automática

Cada nova leitura dispara a sincronização preditiva por sinal, sem depender da
navegação no dashboard. Também existe o comando `python manage.py
analisar_tendencias`, adequado para agendamento pelo mecanismo já usado no
ambiente (Task Scheduler, cron ou rotina de deploy), sem introduzir Celery,
Redis ou outro serviço. O comando processa sensores ativos, registra falhas no
log e é seguro para reexecução.

## Gemini e interface

O endpoint existente `/api/gemini/tendencia/` continua recebendo somente os
resultados calculados e as últimas dez leituras resumidas. O texto é salvo em
`Alerta.analise_ia` quando disponível; o modelo não altera risco, prioridade ou
abertura de OS. A resposta de tendência também expõe `active_alert_id` e
`predictive_work_order` para que a interface possa indicar o vínculo.

## Arquivos alterados

- `telemetria/trend_analysis.py`: seleção correta, limpeza, qualidade e regras.
- `telemetria/predictive_service.py`: ciclo de vida, alertas e OS preditivas.
- `telemetria/signals.py`: execução na ingestão.
- `telemetria/management/commands/analisar_tendencias.py`: processamento periódico.
- `alertas/models.py` e `alertas/signals.py`: origem, vínculo e deduplicação.
- `manutencao/models.py` e `manutencao/services.py`: origem da OS e sincronização.
- `gemini_api/models.py`, `prompt_builder.py` e `views.py`: explicação limitada e persistida.
- `alertas/serializers.py`, `alertas/admin.py`, `manutencao/admin.py` e
  `telemetria/admin.py`: exposição e operação administrativa dos novos vínculos.
- `FrontATT/index.html`: indicação visual da recomendação e da OS associada.
- `telemetria/test_trend_analysis.py`: cobertura de seleção, qualidade, projeção,
  direções, reprocessamento e resolução.
- `telemetria/management/commands/analisar_tendencias.py`: rotina periódica.

## Migrações e testes

Os apps deste repositório não continham migrações iniciais versionadas; os novos
campos devem ser incluídos no ciclo normal de `makemigrations`/`migrate` antes de
um deploy. A execução local desta entrega não conseguiu iniciar a suíte porque
o ambiente não possui Django instalado (`ModuleNotFoundError: No module named
'django'`). Portanto nenhum teste é declarado como aprovado aqui.
