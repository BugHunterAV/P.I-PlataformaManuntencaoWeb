# 🏭 Plataforma de Manutenção Industrial Preditiva

> API REST completa e profissional para gestão inteligente de ativos industriais, manutenção preditiva, ordens de serviço, telemetria IoT em tempo real, alertas automáticos, dashboards executivos, exportação de relatórios e integração com Inteligência Artificial.

---

## 📌 Sobre o Projeto

Esta é uma API REST desenvolvida em Django que centraliza e digitaliza toda a gestão de manutenção industrial de uma empresa.

O sistema permite que indústrias gerenciem de forma eficiente seus equipamentos, monitorem parâmetros em tempo real através de sensores IoT, recebam alertas automáticos quando algum parâmetro sai do normal, controlem todas as ordens de serviço desde a abertura até o fechamento, e tenham visibilidade gerencial através de dashboards com indicadores importantes como MTBF, MTTR e Disponibilidade dos ativos.

O sistema conta com:
- **Integração com IA (Google Gemini)** para suporte técnico avançado e análise de ordens
- **Exportação de relatórios** em CSV, Excel (.xlsx) e PDF
- **Front-end completo** em Vue.js (pasta `FrontATT/`) com dashboard, gestão de ativos, OS, alertas e chat de IA

O projeto foi construído com foco em modularidade, segurança, escalabilidade, isolamento de dados por empresa (multi-tenant) e fácil integração com o Front-end.

---

## 🛠 Tecnologias Utilizadas

**Back-end:**
- Python 3.11+
- Django 5.2
- Django REST Framework 3.16
- `djangorestframework-simplejwt` — autenticação JWT
- `drf-spectacular` — documentação Swagger e ReDoc automática
- `django-cors-headers` — requisições cross-origin do front-end
- `django-filter` — filtros avançados nas listagens
- `python-dotenv` — variáveis de ambiente
- `google-generativeai` / `google-genai` — integração com Google Gemini
- `Faker` — geração de dados realistas no seed
- `WeasyPrint` + `ReportLab` — geração de PDF
- `openpyxl` — geração de Excel (.xlsx)
- PostgreSQL (produção) / SQLite (desenvolvimento rápido)

**Front-end (`FrontATT/`):**
- Vue.js 3 (via CDN, sem build step)
- CSS customizado com design moderno
- Consome 100% da API REST via JWT

---

## 🚀 Como Rodar Localmente

Siga os passos abaixo na ordem exata:

**1. Ative o ambiente virtual:**
```bash
# Windows PowerShell
.\venv\Scripts\activate
```

**2. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**3. Configure o banco de dados PostgreSQL:**
- Certifique-se de que o serviço do PostgreSQL está rodando
- Crie um banco de dados chamado `manutencao`
- Ajuste usuário e senha em `app/settings.py` se necessário

**4. Crie o arquivo de variáveis de ambiente:**

Na raiz do projeto, crie um arquivo `.env` com:
```env
GEMINI_API_KEY="sua_chave_api_do_google_gemini_aqui"
```
> Para obter a chave, acesse o [Google AI Studio](https://aistudio.google.com/).
> O `.env` já está listado no `.gitignore` e não deve ser commitado.

**5. Execute as migrações:**
```bash
python manage.py migrate
```

**6. Popule o banco com dados realistas:**
```bash
python scripts/seed_db.py
```
> Veja a seção [Scripts de Utilidade](#%EF%B8%8F-scripts-de-utilidade) para opções avançadas.

**7. Inicie o servidor:**
```bash
python manage.py runserver
# Se a porta 8000 estiver ocupada:
python manage.py runserver 9000
```

A API estará acessível em: **http://localhost:8000**

O Front-end está em `FrontATT/index.html` — basta abrir no navegador com o servidor rodando.

---

## 🧪 Como Executar os Testes

O projeto utiliza o framework de testes nativo do Django. Os testes são isolados e não afetam o banco de dados de produção.

```bash
# Rodar todos os testes
python manage.py test

# Rodar testes de um módulo específico
python manage.py test ativos
python manage.py test manutencao
python manage.py test alertas
python manage.py test gemini_api

# Log detalhado
python manage.py test -v 2
```

---

## 🛠️ Scripts de Utilidade

O projeto conta com **3 scripts** na pasta `scripts/` para facilitar o desenvolvimento e testes.

---

### 1. 🌱 Seed de Banco de Dados (`seed_db.py`)

Popula o banco com uma estrutura completa, multi-tenant e realista: empresas, usuários com cargos reais, equipamentos industriais, sensores, 120 dias de histórico de telemetria, ordens de serviço, histórico de manutenção e alertas.

> ⚠️ **Atenção:** o seed **apaga todos os dados existentes** antes de inserir os novos. Use com cuidado.

**Padrão** (2 empresas, 10 equipamentos cada):
```bash
python scripts/seed_db.py
```

**Customizado** (ex: 5 empresas, 30 equipamentos cada):
```bash
python scripts/seed_db.py --empresas 5 --equipamentos 30
```

| Argumento | Padrão | Descrição |
|---|---|---|
| `--empresas` | `2` | Número de empresas a criar |
| `--equipamentos` | `10` | Número de equipamentos por empresa |

---

### 2. 📡 Simulador de Telemetria em Tempo Real (`simulador_realtime.py`)

Simula um fluxo contínuo e realista de dados de sensores diretamente no banco, detectando sensores ativos dinamicamente. Ideal para testar alertas, o dashboard e o front-end sem precisar de hardware real.

O simulador preserva o histórico de valores entre ciclos (transições suaves), possui 1% de chance de gerar anomalias/picos, e se adapta automaticamente quando sensores ou equipamentos são ativados/desativados no banco.

**Uso básico** (ciclos contínuos, intervalo de 1 a 3 segundos):
```bash
python scripts/simulador_realtime.py
```

**Exemplos avançados:**
```bash
# Ciclo rápido, 50 ciclos, modo seco (sem gravar no banco)
python scripts/simulador_realtime.py --interval-min 0.5 --interval-max 1.0 --cycles 50 --dry-run

# Simular apenas sensores específicos com log de debug
python scripts/simulador_realtime.py --sensor 1 2 3 --debug

# Simular apenas equipamentos de uma empresa
python scripts/simulador_realtime.py --equipamento 4 5

# Resultado determinístico (mesma sequência de valores para testes)
python scripts/simulador_realtime.py --seed 42
```

| Argumento | Padrão | Descrição |
|---|---|---|
| `--interval-min` | `1.0` | Tempo mínimo em segundos entre ciclos |
| `--interval-max` | `3.0` | Tempo máximo em segundos entre ciclos |
| `--cycles` | `0` (infinito) | Número máximo de ciclos. `0` = execução contínua |
| `--seed` | — | Semente para geração determinística de valores |
| `--sensor` | — | IDs de sensores específicos para simular |
| `--equipamento` | — | IDs de equipamentos para limitar a simulação |
| `--dry-run` | `false` | Executa sem gravar leituras no banco |
| `--debug` | `false` | Ativa logs de depuração detalhados |

> 💡 **Dica:** use `--dry-run` para ver o que seria gerado antes de gravar no banco.

---

### 3. 🔥 Teste de Estresse de Telemetria (`stress_telemetry.py`)

Simula o envio massivo e paralelo de dados de sensores para testar a performance da API, a escalada de alertas e a criação automática de O.S. sob carga.

**Padrão** (100 leituras, 5 threads):
```bash
python scripts/stress_telemetry.py
```

**Carga pesada** (1000 leituras, 20 threads):
```bash
python scripts/stress_telemetry.py --leituras 1000 --threads 20
```

---

## 🔑 Credenciais Padrão (após o seed)

| Perfil | Usuário | Senha |
|---|---|---|
| Admin (Django + API) | `admin` | `admin` |
| Gestores e Técnicos | *(gerado pelo Faker, formato `nome.sobrenome`)* | `123` |

> Consulte o painel admin (`/admin/`) para ver todos os usuários criados pelo seed.

---

## 📁 Estrutura do Projeto

```
P.I-PlataformaManuntencaoWeb/
├── app/                      # Configurações globais (settings, urls raiz, wsgi)
├── authentication/           # Login JWT, /me, troca de senha
├── accounts/                 # Empresas e Usuários (modelo customizado)
├── ativos/                   # Equipamentos, Localização e Planos de Manutenção
├── manutencao/               # Ordens de Serviço e Histórico de Manutenção
│   └── dashboards/           # KPIs: MTBF, MTTR, Disponibilidade
├── telemetria/               # Sensores IoT e Leituras de Telemetria
├── alertas/                  # Sistema de Alertas automáticos
├── exportacao/               # Exportação de relatórios (CSV, Excel, PDF)
├── gemini_api/               # Integração com Google Gemini (IA)
├── scripts/                  # Scripts auxiliares (seed, simulador, stress)
├── FrontATT/                 # Front-end Vue.js completo
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── manage.py
```

### Descrição detalhada de cada app:

| App | Responsabilidade |
|---|---|
| `app/` | Configurações centrais: `settings.py`, `urls.py` raiz, `wsgi.py` |
| `authentication/` | Login JWT, refresh token, endpoint `/me`, troca de senha |
| `accounts/` | Modelos de `Empresa` e `Usuario` customizado (com `tipo_usuario`, `cargo`) |
| `ativos/` | Equipamentos, Localização física e Planos de Manutenção por Horímetro |
| `manutencao/` | Ordens de Serviço (O.S.) corretivas, preditivas e preventivas + Histórico |
| `manutencao/dashboards/` | Cálculo de KPIs: MTBF, MTTR, Disponibilidade, resumo geral |
| `telemetria/` | Sensores IoT e Leituras de telemetria em tempo real |
| `alertas/` | Alertas automáticos (baixo, médio, crítico) gerados pela telemetria |
| `exportacao/` | Relatórios exportáveis em CSV, Excel (.xlsx) e PDF |
| `gemini_api/` | Chat IA, análise de OS, priorização de ordens e gestão financeira |

---

## 🔗 Principais Relacionamentos e Regras de Cascade

| Modelo | Relacionado com | Tipo | Comportamento |
|---|---|---|---|
| **Usuario** | Empresa | ForeignKey | CASCADE — exclusão de empresa remove usuários |
| **Equipamento** | Empresa | ForeignKey | CASCADE — exclusão de empresa remove equipamentos |
| **EquipamentoLocalizacao** | Equipamento | OneToOneField | CASCADE — localização única por equipamento |
| **PlanoManutencao** | Equipamento | ForeignKey | CASCADE — planos removidos com o equipamento |
| **Sensor** | Equipamento | ForeignKey | CASCADE — sensores removidos com o equipamento |
| **Telemetria** | Sensor | ForeignKey | CASCADE — leituras removidas com o sensor |
| **Alerta** | Equipamento | ForeignKey | CASCADE — alertas removidos com o equipamento |
| **OrdemServico** | Equipamento | ForeignKey | PROTECT — não permite excluir equipamento com OS aberta |
| **OrdemServico** | Usuario (responsável) | ForeignKey | SET_NULL — responsável excluído → campo fica nulo |
| **HistoricoManutencao** | OrdemServico | OneToOneField | CASCADE — histórico removido com a OS |

---

## 🛡 Segurança e Controle de Acesso

**Autenticação via JWT:**
```
Authorization: Bearer SEU_TOKEN_AQUI
```

O sistema possui **isolamento completo por empresa (multi-tenant)**. Um usuário só vê e altera dados da empresa à qual está vinculado.

**Perfis disponíveis:**

| Perfil | Permissões |
|---|---|
| `admin` | Acesso total ao sistema, visualiza dados de todas as empresas |
| `gestor` | Gerencia usuários, equipamentos e ordens da **própria empresa** |
| `tecnico` | Visualiza dados e registra manutenções. Só vê OS sem responsável **ou** atribuídas a ele |

**Endpoint de login:** `POST /api/auth/login/`
```json
{ "username": "seu_usuario", "password": "sua_senha" }
```

---

## ⚙️ Inteligência Preditiva e Automação (Signals)

O sistema monitora a telemetria em tempo real e toma decisões automáticas:

### 1. Regras de Disparo de Alertas por Sensor

A severidade é calculada com base no percentual do `limite_alerta` configurado no sensor:

| Nível | Condição | Exemplo (limite = 100°C) |
|---|---|---|
| 🟢 **Baixo** | Valor ≥ 70% do limite | ≥ 70°C |
| 🟡 **Médio** | Valor ≥ 85% do limite | ≥ 85°C |
| 🔴 **Crítico** | Valor ≥ 100% do limite | ≥ 100°C |

> Os percentuais são configuráveis individualmente por sensor (`limite_alerta_baixo_pct`, `limite_alerta_medio_pct`, `limite_alerta_critico_pct`).

### 2. Geração Automática de O.S. por Alerta

Qualquer anomalia detectada gera instantaneamente uma **Ordem de Serviço** para inspeção. A prioridade da O.S. (`baixo`, `medio`, `critico`) reflete exatamente o nível do alerta.

### 3. Escalada e Agrupamento Inteligente

- **Escalada:** Se uma falha de nível "Médio" piorar para "Crítico", o sistema **eleva a prioridade** da O.S. já aberta em vez de criar duplicata.
- **Multifuncionalidade:** Se houver falhas de tipos diferentes (ex: Temperatura e Vibração) no mesmo motor, o sistema cria **duas O.S. distintas** para rastreamento individual.

### 4. Geração Automática de O.S. por Horímetro (Tempo de Uso)

Além dos sensores, o sistema gera O.S. automaticamente com base no tempo de operação (horímetro) do equipamento, usando Planos de Manutenção configuráveis.

**Fluxo completo:**

1. **Cadastro do equipamento** com horímetro atual (ex: `200h`). Se não informado, assume `0`.
2. **Criação do plano** (ex: "Troca de Óleo" a cada `100h`). O sistema grava internamente que a última manutenção foi em `200h`, então o próximo disparo será em `300h`.
3. **Atualização do horímetro** via `PATCH /api/equipamentos/{id}/`. Se atingir ou ultrapassar `300h`, o sistema **gera automaticamente uma O.S.**.
4. **Ciclo contínuo:** Após o disparo, o carimbo é atualizado para o horímetro atual. A próxima O.S. será projetada para `horímetro_atual + intervalo`.
5. **Anti-duplicação:** Se a O.S. de horímetro ainda estiver aberta, o sistema **não cria uma nova** até o fechamento da anterior.

---

## 🤖 Inteligência Artificial (Gemini API)

O sistema possui integração profunda com a API do Google Gemini, com **acesso baseado em perfil (RBAC)**.

- **Respostas contextualizadas:** O assistente sabe qual empresa o usuário pertence e responde apenas com dados relevantes.
- **Acesso hierárquico:**
  - **Admin:** perguntas e gestão de informações globais.
  - **Gestor:** conselhos estratégicos exclusivos dos dados da própria empresa.
  - **Técnico:** restrito às suas OS e manutenções — a IA não expõe relatórios gerenciais.

**Endpoints disponíveis:**

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/gemini/chat/` | Chat geral com contexto de ativos e manutenção |
| POST | `/api/gemini/ordens/analise/` | Análise de ordens de serviço abertas |
| POST | `/api/gemini/ordens/sem-atribuicao/` | Priorização de ordens sem responsável |
| POST | `/api/gemini/gestao/financeira/` | Orientação financeira (gestores e admins) |

> O Front-end (`FrontATT/`) já possui um widget de chat flutuante que consome o endpoint de chat, com sugestões rápidas personalizadas por perfil do usuário.

---

## 📤 Exportação de Relatórios

O sistema permite exportar dados em **CSV**, **Excel (.xlsx)** e **PDF**, com isolamento multi-tenant automático.

| Método | Endpoint | O que exporta |
|---|---|---|
| GET | `/api/exportar/ordens-servico/{formato}/` | Ordens de Serviço |
| GET | `/api/exportar/equipamentos/{formato}/` | Equipamentos |
| GET | `/api/exportar/alertas/{formato}/` | Alertas |
| GET | `/api/exportar/telemetria/{formato}/` | Leituras de Telemetria |
| GET | `/api/exportar/historico/{formato}/` | Histórico de Manutenção |
| GET | `/api/exportar/dashboard/{formato}/` | KPIs do Dashboard |

`{formato}` aceita: `csv`, `excel` ou `pdf`

**Exemplo com filtros:**
```
GET /api/exportar/ordens-servico/pdf/?status=pendente&prioridade=critico
```

---

## 📖 Documentação Interativa

Com o servidor rodando, acesse:

| Interface | URL |
|---|---|
| Swagger UI (interativa) | http://localhost:8000/api/schema/swagger-ui/ |
| ReDoc (documentação limpa) | http://localhost:8000/api/schema/redoc/ |
| Painel Administrativo Django | http://localhost:8000/admin/ |

---

## 🔗 Endpoints da API — Lista Completa

**Base URL:** `http://localhost:8000/api/`

### 🔐 Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/auth/login/` | Login — retorna tokens JWT (access + refresh) |
| POST | `/api/auth/refresh/` | Renovar o token de acesso |
| GET | `/api/auth/me/` | Dados do usuário atualmente logado |
| POST | `/api/auth/change-password/` | Trocar senha do usuário logado |

### 🏢 Empresas

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/empresas/` | Listar empresas |
| POST | `/api/empresas/` | Criar nova empresa |
| GET | `/api/empresas/{id}/` | Detalhes de uma empresa |
| PUT/PATCH | `/api/empresas/{id}/` | Atualizar empresa |
| DELETE | `/api/empresas/{id}/` | Excluir empresa |

### 👤 Usuários

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/usuarios/` | Listar usuários |
| POST | `/api/usuarios/` | Criar novo usuário |
| GET | `/api/usuarios/{id}/` | Detalhes de um usuário |
| PUT/PATCH | `/api/usuarios/{id}/` | Atualizar usuário |
| DELETE | `/api/usuarios/{id}/` | Excluir usuário |

### ⚙️ Equipamentos

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/equipamentos/` | Listar equipamentos |
| POST | `/api/equipamentos/` | Cadastrar novo equipamento |
| GET | `/api/equipamentos/{id}/` | Detalhes de um equipamento |
| PUT/PATCH | `/api/equipamentos/{id}/` | Atualizar (PATCH no `horimetro` dispara automações) |
| DELETE | `/api/equipamentos/{id}/` | Excluir equipamento |

**Filtros:** `?empresa=1`, `?status=ativo`, `?tipo=motor_eletrico`, `?search=bomba`

### 📍 Localização

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/localizacao/` | Listar localizações |
| POST | `/api/localizacao/` | Cadastrar localização |
| GET | `/api/localizacao/{id}/` | Detalhes de uma localização |
| PUT/PATCH | `/api/localizacao/{id}/` | Atualizar localização |
| DELETE | `/api/localizacao/{id}/` | Excluir localização |

### 📅 Planos de Manutenção (Horímetro)

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/planos-manutencao/` | Listar planos |
| POST | `/api/planos-manutencao/` | Criar novo plano preditivo |
| GET | `/api/planos-manutencao/{id}/` | Detalhes de um plano |
| PATCH | `/api/planos-manutencao/{id}/` | Atualizar intervalo ou detalhes |
| DELETE | `/api/planos-manutencao/{id}/` | Excluir plano |

**Filtros:** `?equipamento=1`, `?ativo=true`, `?prioridade=critico`

### 🛠️ Ordens de Serviço

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/ordens-servico/` | Listar O.S. |
| POST | `/api/ordens-servico/` | Criar nova O.S. |
| GET | `/api/ordens-servico/{id}/` | Detalhes de uma O.S. |
| PUT/PATCH | `/api/ordens-servico/{id}/` | Atualizar O.S. |
| DELETE | `/api/ordens-servico/{id}/` | Excluir O.S. (só Gestor/Admin) |

**Filtros:** `?status=pendente`, `?prioridade=critico`, `?tipo_os=corretiva`, `?equipamento=1`, `?responsavel=2`, `?search=motor`, `?ordering=-data_abertura`

### 📋 Histórico de Manutenção

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/historico/` | Listar histórico |
| POST | `/api/historico/` | Registrar histórico de manutenção |
| GET | `/api/historico/{id}/` | Detalhes de um histórico |
| PUT/PATCH | `/api/historico/{id}/` | Atualizar histórico |
| DELETE | `/api/historico/{id}/` | Excluir histórico |

### 🚨 Alertas

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/alertas/` | Listar alertas |
| POST | `/api/alertas/` | Criar alerta manual |
| GET | `/api/alertas/{id}/` | Detalhes de um alerta |
| PATCH | `/api/alertas/{id}/` | Atualizar status (ex: marcar como resolvido) |
| DELETE | `/api/alertas/{id}/` | Excluir alerta (só Gestor/Admin) |

**Filtros:** `?equipamento=1`, `?nivel=critico`, `?status=ativo`

### 📡 Telemetria — Sensores

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/telemetria/sensores/` | Listar sensores |
| POST | `/api/telemetria/sensores/` | Cadastrar sensor (com limites customizáveis) |
| GET | `/api/telemetria/sensores/{id}/` | Detalhes de um sensor |
| PUT/PATCH | `/api/telemetria/sensores/{id}/` | Atualizar sensor |
| DELETE | `/api/telemetria/sensores/{id}/` | Excluir sensor |

**Filtros:** `?equipamento=1`, `?tipo=temperatura`, `?ativo=true`

### 📡 Telemetria — Leituras

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/telemetria/leituras/` | Listar leituras |
| POST | `/api/telemetria/leituras/` | Enviar nova leitura (dispara alertas automáticos) |
| GET | `/api/telemetria/leituras/{id}/` | Detalhes de uma leitura |

**Filtros:** `?sensor=1`, `?sensor__equipamento=2`

### 📊 Dashboards e KPIs

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/dashboards/resumo/` | Resumo geral e KPIs da empresa |
| GET | `/api/dashboards/kpis/` | KPIs detalhados: MTBF, MTTR, Disponibilidade por equipamento |

### 🤖 Inteligência Artificial (Gemini)

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/api/gemini/chat/` | Chat com contexto isolado por usuário e empresa |
| POST | `/api/gemini/ordens/analise/` | Análise de ordens abertas e recomendações |
| POST | `/api/gemini/ordens/sem-atribuicao/` | Priorização de ordens sem responsável |
| POST | `/api/gemini/gestao/financeira/` | Orientação financeira (Gestor/Admin) |

### 📤 Exportação de Relatórios

| Método | Endpoint | Formatos aceitos |
|---|---|---|
| GET | `/api/exportar/ordens-servico/{formato}/` | `csv`, `excel`, `pdf` |
| GET | `/api/exportar/equipamentos/{formato}/` | `csv`, `excel`, `pdf` |
| GET | `/api/exportar/alertas/{formato}/` | `csv`, `excel`, `pdf` |
| GET | `/api/exportar/telemetria/{formato}/` | `csv`, `excel`, `pdf` |
| GET | `/api/exportar/historico/{formato}/` | `csv`, `excel`, `pdf` |
| GET | `/api/exportar/dashboard/{formato}/` | `csv`, `excel`, `pdf` |

---

## 🐛 Problemas Comuns e Soluções

| Problema | Solução |
|---|---|
| `python` não reconhecido | Use `py` no lugar de `python` no Windows |
| Ambiente virtual não ativado | Rode novamente o comando de ativação |
| Porta 8000 já em uso | Use `python manage.py runserver 9000` |
| Erro 401 Unauthorized | Token JWT ausente ou expirado — refaça login |
| Erro 403 Forbidden | Usuário sem permissão para a ação (verifique o perfil) |
| Listagens retornando vazias | Usuário não vinculado a uma empresa — verifique no admin |
| IA não responde | Verifique se `GEMINI_API_KEY` está configurado no `.env` |
| Simulador não encontra sensores | Execute o seed primeiro e verifique se há equipamentos `ativo` no banco |

---

## 🗺 Roadmap do Projeto

### ✅ Concluído

- Estrutura completa de apps Django com CRUDs para todos os recursos
- Autenticação JWT com Refresh Token
- Sistema de permissões RBAC por perfil (admin, gestor, técnico)
- Isolamento multi-tenant por empresa em todos os endpoints
- Geração automática e escalada de O.S. por alertas de telemetria
- Limites de alerta configuráveis individualmente por sensor (percentuais customizáveis)
- **Geração automática de O.S. por Horímetro** com planos customizados por equipamento
- **Classificação de O.S.:** Preditiva (horímetro e sensores), Corretiva (manual/emergência), Preventiva (manual)
- Regras de visibilidade restrita para técnicos (Sigilo de O.S.)
- Dashboard com KPIs: MTBF, MTTR, Disponibilidade e resumo geral
- Banco de dados PostgreSQL (pronto para produção)
- Seed completo e ultra-realista com 120 dias de histórico de telemetria
- **Simulador de telemetria em tempo real** com detecção dinâmica de sensores
- Documentação automática Swagger e ReDoc
- Suíte de testes automatizados de integração
- **Integração com Google Gemini** (chat, análise de OS, priorização, gestão financeira)
- **Exportação de relatórios** em CSV, Excel e PDF para todos os recursos
- **Front-end completo** (Vue.js) com dashboard, ativos, OS, alertas, telemetria e chat IA
- Troca de senha via endpoint autenticado

### 🔄 Em Desenvolvimento / Melhorias Planejadas

- Evolução da análise preditiva com IA (detecção de tendências automática via telemetria)
- WebSockets para telemetria em tempo real no front-end
- Paginação e filtros avançados no front-end
- Deploy em ambiente de produção
- Notificações por e-mail para alertas críticos
