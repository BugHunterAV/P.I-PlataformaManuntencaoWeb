# 🏗️ Arquitetura Técnica: Telemetria, Alertas e Dashboards

Como desenvolvedor Sênior, vou te explicar a "fiação interna" do seu projeto. O segredo da nossa plataforma não são apenas os CRUDs, mas sim como os dados **fluem** entre os apps de forma automática.

---

### 1. 📡 Telemetria: Ingestão de Dados (O Gatilho)
A telemetria é a porta de entrada para dados de sensores IoT.
- **O Código**: No app `telemetria`, temos o modelo `Telemetria` vinculado a um `Sensor`.
- **Fluxo**: Quando um dispositivo externo (ou o seu front-end Vue) faz um `POST` para `/api/telemetria/leituras/`, o Django salva um novo registro no banco de dados.
- **Importância**: Isso cria um histórico temporal de performance do equipamento (temperatura, vibração, etc).

### 2. 🚨 Alertas: O Sistema "Event-Driven" (Signals)
Em vez de ficarmos perguntando ao banco de dados o tempo todo se há problemas, usamos **Django Signals**.
- **O Código**: No arquivo `telemetria/signals.py`, temos uma função chamada `checar_limites_telemetria`.
- **Como funciona**: Ela usa o decorador `@receiver(post_save, sender=Telemetria)`. Isso significa: "Toda vez que uma nova Telemetria for salva, execute esta função IMEDIATAMENTE".
- **Lógica**: A função verifica o `valor` recebido. Se o valor ultrapassar o limite (ex: > 80°C), ela executa um `Alerta.objects.create()`.
- **Vantagem**: O sistema reage em tempo real sem intervenção humana.

### 3. 🔧 Manutenção e Histórico: O Ciclo de Vida
Quando um Alerta é gerado, um gestor cria uma **Ordem de Servico (OS)**.
- **O Código**: No app `manutencao`, a OS rastreia quem é o responsável e qual o status.
- **Histórico**: Ao concluir uma OS, preenchemos o `HistoricoManutencao`. Isso é vital porque é aqui que registramos o **Custo** e o **Tempo Real de Reparo**, dados que alimentam a inteligência do negócio.

### 4. 📊 Dashboards: Inteligência com Agregações (KPIs)
O Dashboard não é apenas uma lista; é um processador de métricas industriais.
- **O Código**: No app `dashboards/views.py`, usamos a `KpiDashboardView`.
- **MTTR (Mean Time To Repair)**: Usamos `Avg` (Média) e `ExpressionWrapper` para calcular a diferença entre `data_conclusao` e `data_abertura` de todas as ordens finalizadas.
- **MTBF (Mean Time Between Failures)**: O código percorre as ordens de um equipamento e calcula o intervalo médio de tempo entre o fim de uma falha e o início da próxima.
- **Performance**: Usamos consultas otimizadas do Django ORM para que o cálculo seja rápido mesmo com muitos dados.

---

### 🔄 Resumo do Fluxo de Dados:
1. `POST` Telemetria -> 2. `Signal` detecta anomalia -> 3. `Alerta` gerado -> 4. `OS` aberta/fechada -> 5. `Dashboard` calcula eficiência.

**Essa estrutura garante que a sua API não seja apenas um depósito de dados, mas um sistema que "pensa" e ajuda na tomada de decisão.**

---
**Dúvida sanada? Estamos prontos para iniciar o Passo 5 (Segurança JWT e Permissões)?**
