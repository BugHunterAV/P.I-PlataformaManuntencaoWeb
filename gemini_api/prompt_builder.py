from .prompt_builder_pattern import PromptBuilderConcreto
from .prompt_director import PromptDirector

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
        context_str = custom_context.format(
            company_name=context['company_name'],
            total_equipment=context['total_equipment'],
            active_equipment=context['active_equipment'],
            maintenance_equipment=context['maintenance_equipment'],
            inactive_equipment=context['inactive_equipment'],
            open_orders_count=context['open_orders'].count(),
            unassigned_orders_count=context['unassigned_orders'].count(),
        )
    else:
        context_str = (
            "CONTEXTUALIZAÇÃO RÁPIDA:\n"
            f"- Empresa: {context['company_name']}\n"
            f"- Total de equipamentos: {context['total_equipment']}\n"
            f"- Equipamentos ativos: {context['active_equipment']} | em manutenção: {context['maintenance_equipment']} | inativos: {context['inactive_equipment']}\n"
            f"- Ordens em aberto: {context['open_orders'].count()}\n"
            f"- Ordens sem atribuição: {context['unassigned_orders'].count()}"
        )

    builder = PromptBuilderConcreto()
    prompt = PromptDirector.montar_chat(builder, context, context_str, message)
    return prompt.obter_texto()


def build_os_analysis_prompt(user, context, message):
    context_str = (
        "CONTEXTUALIZAÇÃO DE ORDENS DE SERVIÇO:\n"
        f"- Total de ordens em aberto: {context['open_orders'].count()}\n"
        f"- Ordens sem atribuição: {context['unassigned_orders'].count()}\n"
        f"- Ordens atribuídas a este técnico: {context['assigned_orders'].count() if user.tipo_usuario == 'tecnico' else 'não aplicável'}"
    )

    instruction = _get_effective_text('os_analysis')
    builder = PromptBuilderConcreto()
    prompt = PromptDirector.montar_analise_os(builder, context, context_str, instruction, message)
    return prompt.obter_texto()


def build_unassigned_orders_prompt(user, context, message):
    context_str = (
        "CONTEXTUALIZAÇÃO DE ORDENS NÃO ATRIBUÍDAS:\n"
        f"- Total de ordens sem atribuição: {context['unassigned_orders'].count()}"
    )

    instruction = _get_effective_text('unassigned_orders')
    builder = PromptBuilderConcreto()
    prompt = PromptDirector.montar_ordens_nao_atribuidas(builder, context, context_str, instruction, message)
    return prompt.obter_texto()


def build_finance_prompt(user, context, message):
    financial = context['financial_summary']
    context_str = (
        "CONTEXTUALIZAÇÃO FINANCEIRA:\n"
        f"- Custo total de manutenção registrado: R$ {financial['total_cost']:.2f}\n"
        f"- Média de custo por OS concluída: R$ {financial['average_cost_per_os']:.2f}\n"
        f"- Ordens concluídas com histórico financeiro: {financial['completed_orders']}"
    )

    instruction = _get_effective_text('finance')
    builder = PromptBuilderConcreto()
    prompt = PromptDirector.montar_financeiro(builder, context, context_str, instruction, message)
    return prompt.obter_texto()
