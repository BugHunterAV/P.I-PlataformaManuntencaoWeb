


def _truncate_lines(lines, max_lines=15):
    if len(lines) <= max_lines:
        return lines
    return lines[:max_lines] + [f"... ({len(lines) - max_lines} itens adicionais omitidos)"]


def build_system_instruction(user, purpose):
    company_name = user.empresa.nome if getattr(user, 'empresa', None) else 'Todas as empresas'
    if user.tipo_usuario == 'tecnico':
        role = 'técnico'
        focus = (
            'foco técnico de campo, análise de ordens de serviço e resolução prática de falhas, '
            'sem expor dados financeiros detalhados.'
        )
    elif user.tipo_usuario == 'gestor':
        role = 'gestor'
        focus = (
            'foco em gestão de manutenção, desempenho operacional, priorização de ordens e '
            'impacto financeiro da manutenção.'
        )
    else:
        role = 'administrador'
        focus = (
            'visão estratégica de gestão de ativos, governança de manutenção e controle financeiro '
            'de toda a plataforma.'
        )

    return (
        f"Você é a NanaSmart AI, o assistente de manutenção industrial e gestão de ativos "
        f"para a empresa {company_name}. Seu papel é entregar respostas claras, objetivas e "
        f"acionáveis para um {role}."
        "\n\nDiretriz de escopo: responda apenas sobre manutenção, ordens de serviço, alertas, "
        "telemetria, desempenho de equipamentos e gestão de manutenção. Recuse perguntas "
        f"fora desse escopo. {focus}\n"
        f"\n\nObjetivo atual: {purpose}. "
        "Use sempre formatação Markdown com marcadores ou tópicos quando for útil."
    )


def build_chat_prompt(message, context):
    blocks = [
        "CONTEXTUALIZAÇÃO RÁPIDA:",
        f"- Empresa: {context['company_name']}",
        f"- Total de equipamentos: {context['total_equipment']}",
        f"- Equipamentos ativos: {context['active_equipment']} | em manutenção: {context['maintenance_equipment']} | inativos: {context['inactive_equipment']}",
        f"- Ordens em aberto: {context['open_orders'].count()}",
        f"- Ordens sem atribuição: {context['unassigned_orders'].count()}"
    ]

    alert_lines = _truncate_lines([f"- {line}" for line in context['alert_summary']], max_lines=5)
    if alert_lines:
        blocks += ["\nALERTAS RELEVANTES:"] + alert_lines

    order_lines = _truncate_lines([f"- {line}" for line in context['open_order_summary']], max_lines=5)
    if order_lines:
        blocks += ["\nORDENS EM ABERTO:"] + order_lines

    equipment_lines = _truncate_lines([f"- {line}" for line in context['equipment_kpis']], max_lines=5)
    if equipment_lines:
        blocks += ["\nKPIs DE EQUIPAMENTOS:"] + equipment_lines

    telemetry_lines = _truncate_lines(context['telemetry'], max_lines=5)
    if telemetry_lines:
        blocks += ["\nTELEMETRIA RECENTE:"] + telemetry_lines

    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)


def build_os_analysis_prompt(user, context, message):
    blocks = [
        "CONTEXTUALIZAÇÃO DE ORDENS DE SERVIÇO:",
        f"- Total de ordens em aberto: {context['open_orders'].count()}",
        f"- Ordens sem atribuição: {context['unassigned_orders'].count()}",
        f"- Ordens atribuídas a este técnico: {context['assigned_orders'].count() if user.tipo_usuario == 'tecnico' else 'não aplicável'}",
    ]

    if context['assigned_order_summary']:
        blocks += ["\nORDENS ATRIBUÍDAS:"] + _truncate_lines(context['assigned_order_summary'], max_lines=5)

    if context['unassigned_order_summary']:
        blocks += ["\nORDENS SEM ATRIBUIÇÃO:"] + _truncate_lines(context['unassigned_order_summary'], max_lines=5)

    blocks += ["\nINSTRUÇÃO:",
               "Analise as ordens de serviço descritas acima e sugira os próximos passos práticos.",
               "Para técnicos, indique como priorizar, o que verificar no equipamento e quando escalar.",
               "Para gestores/admin, indique quais ordens devem receber atenção imediata e por quê." ]
    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)


def build_unassigned_orders_prompt(context, message):
    blocks = [
        "CONTEXTUALIZAÇÃO DE ORDENS NÃO ATRIBUÍDAS:",
        f"- Total de ordens sem atribuição: {context['unassigned_orders'].count()}",
    ]
    if context['unassigned_order_summary']:
        blocks += ["\nORDENS SEM ATRIBUIÇÃO (EXEMPLOS):"] + _truncate_lines(context['unassigned_order_summary'], max_lines=5)

    blocks += [
        "\nINSTRUÇÃO:",
        "Avalie estas ordens e sugira critérios claros para atribuição e priorização.",
        "Se houver ordens críticas ou de alto risco, indique-as e explique por quê."
    ]
    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)


def build_finance_prompt(user, context, message):
    financial = context['financial_summary']
    blocks = [
        "CONTEXTUALIZAÇÃO FINANCEIRA:",
        f"- Custo total de manutenção registrado: R$ {financial['total_cost']:.2f}",
        f"- Média de custo por OS concluída: R$ {financial['average_cost_per_os']:.2f}",
        f"- Ordens concluídas com histórico financeiro: {financial['completed_orders']}",
    ]

    if financial['top_equipment_costs']:
        blocks += ["\nEQUIPAMENTOS COM MAIOR CUSTO:"] + financial['top_equipment_costs']

    blocks += [
        "\nINSTRUÇÃO:",
        "Baseado nesses números, indique melhorias de gestão de manutenção, redução de custos e prioridades de investimento.",
        "Explique quais métricas devem ser monitoradas e quais ações trazer para reduzir retrabalho e tempo de parada." 
    ]
    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)
