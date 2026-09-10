



def _truncate_lines(lines, max_lines=15):
    if len(lines) <= max_lines:
        return lines
    return lines[:max_lines] + [f"... ({len(lines) - max_lines} itens adicionais omitidos)"]


# ─── Original (default) prompt texts ────────────────────────────────────────
# These are the built-in defaults that are used when no custom prompt is set.

DEFAULTS = {}

DEFAULTS['system_instruction_tecnico'] = (
    'foco técnico de campo, análise de ordens de serviço e resolução prática de falhas, '
    'sem expor dados financeiros detalhados.'
)

DEFAULTS['system_instruction_gestor'] = (
    'foco em gestão de manutenção, desempenho operacional, priorização de ordens e '
    'impacto financeiro da manutenção.'
)

DEFAULTS['system_instruction_admin'] = (
    'visão estratégica de gestão de ativos, governança de manutenção e controle financeiro '
    'de toda a plataforma.'
)

DEFAULTS['chat_context'] = (
    "CONTEXTUALIZAÇÃO RÁPIDA:\n"
    "- Empresa: {company_name}\n"
    "- Total de equipamentos: {total_equipment}\n"
    "- Equipamentos ativos: {active_equipment} | em manutenção: {maintenance_equipment} | inativos: {inactive_equipment}\n"
    "- Ordens em aberto: {open_orders_count}\n"
    "- Ordens sem atribuição: {unassigned_orders_count}"
)

DEFAULTS['os_analysis'] = (
    "INSTRUÇÃO:\n"
    "Analise as ordens de serviço descritas acima e sugira os próximos passos práticos.\n"
    "Para técnicos, indique como priorizar, o que verificar no equipamento e quando escalar.\n"
    "Para gestores/admin, indique quais ordens devem receber atenção imediata e por quê."
)

DEFAULTS['unassigned_orders'] = (
    "INSTRUÇÃO:\n"
    "Avalie estas ordens e sugira critérios claros para atribuição e priorização.\n"
    "Se houver ordens críticas ou de alto risco, indique-as e explique por quê."
)

DEFAULTS['finance'] = (
    "INSTRUÇÃO:\n"
    "Baseado nesses números, indique melhorias de gestão de manutenção, redução de custos e prioridades de investimento.\n"
    "Explique quais métricas devem ser monitoradas e quais ações trazer para reduzir retrabalho e tempo de parada."
)


def get_all_defaults():
    """Return a copy of the default prompt texts dictionary."""
    return dict(DEFAULTS)


def _get_custom_prompt(key):
    """Fetch custom prompt from DB. Returns None if not customized."""
    try:
        from .models import PromptConfig
        config = PromptConfig.objects.filter(key=key).first()
        if config and config.is_customized:
            return config.custom_text.strip()
    except Exception:
        pass
    return None


def _get_effective_text(key):
    """Return custom text if set, otherwise the default."""
    custom = _get_custom_prompt(key)
    return custom if custom else DEFAULTS.get(key, '')


def build_system_instruction(user, purpose):
    company_name = user.empresa.nome if getattr(user, 'empresa', None) else 'Todas as empresas'
    if user.tipo_usuario == 'tecnico':
        role = 'técnico'
        focus = _get_effective_text('system_instruction_tecnico')
    elif user.tipo_usuario == 'gestor':
        role = 'gestor'
        focus = _get_effective_text('system_instruction_gestor')
    else:
        role = 'administrador'
        focus = _get_effective_text('system_instruction_admin')

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


def build_chat_prompt(user, context, message):
    # Build contextualisation header (may be customized)
    custom_context = _get_custom_prompt('chat_context')
    if custom_context:
        blocks = [custom_context.format(
            company_name=context['company_name'],
            total_equipment=context['total_equipment'],
            active_equipment=context['active_equipment'],
            maintenance_equipment=context['maintenance_equipment'],
            inactive_equipment=context['inactive_equipment'],
            open_orders_count=context['open_orders'].count(),
            unassigned_orders_count=context['unassigned_orders'].count(),
        ).split('\n')]
        blocks = blocks[0]  # flatten from split
    else:
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

    instruction = _get_effective_text('os_analysis')
    blocks += [f"\n{instruction}"]
    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)


def build_unassigned_orders_prompt(user, context, message):
    blocks = [
        "CONTEXTUALIZAÇÃO DE ORDENS NÃO ATRIBUÍDAS:",
        f"- Total de ordens sem atribuição: {context['unassigned_orders'].count()}",
    ]
    if context['unassigned_order_summary']:
        blocks += ["\nORDENS SEM ATRIBUIÇÃO (EXEMPLOS):"] + _truncate_lines(context['unassigned_order_summary'], max_lines=5)

    instruction = _get_effective_text('unassigned_orders')
    blocks += [f"\n{instruction}"]
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

    instruction = _get_effective_text('finance')
    blocks += [f"\n{instruction}"]
    blocks += ["\nPERGUNTA DO USUÁRIO:", message]
    return "\n".join(blocks)
