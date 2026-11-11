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

As migrações versionadas incluem os novos vínculos, a restrição de episódio
ativo, a configuração de ausência de dados e a auditoria das execuções. Antes
de implantar, execute `python manage.py migrate` em uma cópia do banco e valide
o plano de migração do PostgreSQL.

O endpoint de alertas expõe os dados de tendência para consulta, mas os campos
que controlam automação (`sensor`, origem, chave do evento, métricas e análise
da IA) são somente leitura. Criações pela API passam a ser sempre alertas
manuais. Alertas por limite recebem o sensor de origem para evitar que dois
sensores iguais do mesmo equipamento sejam agrupados indevidamente.

Quando não há dados suficientes, a rotina conserva o alerta enquanto a última
leitura ainda estiver dentro de `max_horas_sem_dados`; após isso, encerra o
episódio com justificativa auditável. A configuração pertence a `TrendConfig`
e deve ser maior ou igual à janela de análise.

Cada execução do comando também grava um `TrendAnalysisRun`, com horário,
contadores e detalhes de falhas. Se qualquer sensor falhar, o comando devolve
erro para que o agendador/monitor detecte a execução degradada.

Para testes locais/CI sem PostgreSQL, use
`DJANGO_SETTINGS_MODULE=app.settings_test`. A validação final deve incluir
PostgreSQL porque a proteção de unicidade condicional é aplicada pelo banco.

## Implementação complementar — 4 de novembro de 2026

Foram aplicadas as melhorias identificadas na revisão técnica:

- Migrações geradas e conferidas para alertas, OS, configurações de tendência,
  histórico de execuções e configuração de ausência de dados.
- A API passou a aceitar somente criação de alertas manuais. Os campos que
  identificam e controlam eventos de tendência são somente leitura.
- O alerta por limite agora é vinculado ao sensor que o produziu, impedindo que
  sensores do mesmo tipo no mesmo equipamento compartilhem indevidamente um
  alerta ativo.
- Dados insuficientes não encerram um alerta prematuramente: a última leitura
  precisa estar ausente por mais que `max_horas_sem_dados`. O encerramento fica
  registrado na descrição e nas métricas da análise.
- O comando periódico registra cada execução em `TrendAnalysisRun`, incluindo
  sensores processados, análises sem dados, alertas/OS criados, resoluções e
  falhas. Ele retorna erro quando houver falha, permitindo que o agendador
  detecte execução degradada.
- O frontend passou a exibir a explicação persistida do Gemini no próprio alerta
  de tendência, sem exigir nova chamada ao modelo.
- A configuração de testes `app.settings_test` usa SQLite isolado. Ela é
  indicada para desenvolvimento e CI; a validação final em PostgreSQL continua
  obrigatória para confirmar a semântica da restrição parcial de unicidade.

### Agendamento recomendado

Agende `python manage.py analisar_tendencias` a cada 15 minutos no ambiente de
execução. No Windows, use o Agendador de Tarefas apontando para o interpretador
do ambiente virtual e para a pasta do projeto; no Linux, use cron ou o
orquestrador de deploy. Monitore registros `TrendAnalysisRun` com status
`partial_failure` ou `failed`.

### Validação executada

Em 4 de novembro de 2026, com `DJANGO_SETTINGS_MODULE=app.settings_test`:

- `python manage.py check`: aprovado, sem problemas.
- `python manage.py makemigrations --check --dry-run`: aprovado, sem mudanças
  pendentes.
- `python manage.py test`: aprovado, 52 testes executados.
- Compilação estática dos módulos Python afetados: aprovada.
