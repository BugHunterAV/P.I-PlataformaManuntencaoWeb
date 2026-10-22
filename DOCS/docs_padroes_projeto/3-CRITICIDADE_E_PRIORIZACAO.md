# Criticidade de equipamentos e priorização de OS

## Diagnóstico da arquitetura (22/10/2026)

O sistema já possuía `Equipamento`, `OrdemServico`, `PlanoManutencao`, `Alerta` e telemetria, com isolamento por empresa em viewsets e serializers. A criticidade era apenas `normal`/`alta`, sem justificativa ou histórico. O tipo do equipamento era texto livre, sem catálogo relacional. A prioridade de OS já tinha os quatro níveis requeridos, porém era calculada em dois sinais: alertas copiavam o nível do alerta e planos de horímetro copiavam a prioridade do plano. Isso duplicava regra, não guardava contexto histórico e confundia criticidade com urgência.

Reutilizados: CRUDs e URLs existentes, permissões de gestor, sinais de alerta/horímetro, alertas de telemetria e a interface Vue. Não houve mudança nas rotas existentes. Foram acrescentados um catálogo opcional de tipos, histórico de criticidade e contexto de cálculo da OS.

## Método de criticidade A/B/C/D para gestores

Criticidade é consequência de uma falha do ativo; não é a urgência de uma OS.

| Classe | Significado | Exemplo orientativo |
|---|---|---|
| A | Consequência muito grave para segurança, ambiente ou operação essencial | Bomba sem redundância que interrompe processo crítico |
| B | Impacto operacional elevado ou perda relevante | Compressor com contingência limitada |
| C | Impacto limitado, com contorno operacional | Ventilador com unidade reserva confiável |
| D | Baixo impacto e intervenção programável | Equipamento auxiliar fora do gargalo |

Ao classificar, o gestor registra a justificativa com: impacto em segurança/ambiente, produção e qualidade, redundância real e confiável, tempo de recuperação, custo e efeito da falha. Revise após mudança de processo, instalação de redundância, incidente significativo ou alteração de capacidade. Gestor e administrador podem cadastrar/alterar; técnico consulta. O tipo pode sugerir uma classe, mas não altera automaticamente equipamentos já avaliados. A falta de classe fica explícita como “não avaliada”.

## Matriz determinística de prioridade

O backend é a fonte de decisão. Risco de segurança ou gravidade crítica sempre retorna **crítica**. Para condições baixa, moderada e alta, a matriz é:

| Criticidade | Baixa | Moderada | Alta |
|---|---:|---:|---:|
| A | média | alta | alta |
| B | média | média | alta |
| C | baixa | média | alta |
| D | baixa | baixa | média |

Exemplos: classe A com tendência moderada resulta em alta; classe D com tendência moderada fica baixa; qualquer condição crítica ou risco de segurança é crítica. Preventivas/preditivas sem condição usam a prioridade do plano e uma classe A não as torna emergência por si só. Condição sem criticidade recebe alta para triagem explícita; condição sem gravidade recebe média com aviso, sem presunção de baixo risco. Uma prioridade manual de gestor/admin é preservada, marcada como manual e não é sobrescrita pelos sinais.

## Fluxo, histórico e compatibilidade

`PrioridadeOSService` concentra a matriz. `alertas.signals` e `ativos.signals` passaram a delegar para ela. Na abertura da OS, ficam gravados criticidade e justificativa daquele momento, prioridade automática e justificativa da decisão. Mudanças futuras de criticidade não apagam esse retrato. A alteração de gravidade recalcula somente OS não marcada como manual.

Campos antigos foram preservados. A migração torna a criticidade antiga nula (não avaliada), em vez de converter `normal` em uma classe arbitrária. A conversão operacional recomendada é avaliar os ativos existentes pelos critérios acima; não há alteração destrutiva nem atualização direta do banco.

## API

Mantidos: `GET/POST/PATCH /api/equipamentos/` e `GET/POST/PATCH /api/ordens-servico/`.

Novos recursos compatíveis:

- `GET/POST/PATCH /api/tipos-equipamento/`: catálogo por empresa com `criticidade_padrao` e critérios.
- `GET /api/historico-criticidade/?equipamento={id}`: trilha de auditoria, somente leitura.
- Equipamento: `tipo_equipamento`, `criticidade` (`A`–`D` ou nula), `criticidade_origem`, `justificativa_criticidade`, `criticidade_sugerida`.
- OS: `gravidade_condicao`, `risco_seguranca`, `prioridade_automatica`, `prioridade_manual`, `justificativa_prioridade`, `criticidade_na_abertura` e justificativa histórica.

Exemplo de OS corretiva: `{"equipamento": 7, "titulo": "Temperatura crescente", "descricao": "Leitura acima da faixa", "tipo_os":"corretiva", "gravidade_condicao":"moderada"}`. O servidor calcula a prioridade e devolve a justificativa. Gestores podem informar `prioridade` para uma exceção manual; técnicos não podem forçá-la.

## Alterações realizadas

| Arquivo | Responsabilidade da alteração |
|---|---|
| `ativos/models.py`, `ativos/services.py` | Catálogo opcional, A/B/C/D, justificativa e auditoria de criticidade |
| `ativos/serializers.py`, `views.py`, `urls.py` | Sugestão, autorização e endpoints compatíveis |
| `manutencao/models.py`, `services.py`, `serializers.py` | Matriz central, justificativa e contexto histórico da OS |
| `alertas/signals.py`, `ativos/signals.py` | Delegação da criação automática ao serviço central |
| `FrontATT/index.html`, `FrontATT/app.js` | Campos A/B/C/D, gravidade/risco e exibição do motivo |
| `ativos/migrations/0010_*`, `manutencao/migrations/0008_*` | Evolução não destrutiva do banco |
| `ativos/tests.py`, `manutencao/tests.py` | Cenários de sugestão, permissão, matriz, ausência e histórico |

## Verificações

Executados: `venv\\Scripts\\python.exe manage.py check` — aprovado, sem problemas; `venv\\Scripts\\python.exe manage.py test ativos.tests.CriticidadeTests manutencao.tests.PriorizacaoTests --verbosity 2` — 7 testes aprovados. A execução combinada de `manage.py test ativos manutencao` iniciou e executou os casos, mas o terminal não retornou seu resumo final; por isso ela não é registrada como aprovada. A interface é HTML/Vue estático e requer validação manual no navegador após subir a API.

## Limitações e evolução

Não há uma fonte existente de risco de segurança nos alertas, por isso esse dado é explícito na OS e não é inferido de texto ou IA. O catálogo de tipos é opcional para preservar o campo `tipo` textual e os registros atuais. Uma futura importação de ativos pode usar o catálogo para sugerir a classe, sempre exigindo revisão do gestor.
