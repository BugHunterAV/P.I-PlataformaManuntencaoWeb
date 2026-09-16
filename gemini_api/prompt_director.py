from .prompt_builder_pattern import PromptBuilder
from .prompt import Prompt

class PromptDirector:
    @staticmethod
    def montar_chat(builder: PromptBuilder, context: dict, context_str: str, message: str) -> Prompt:
        builder.reset()
        builder.com_contexto(context_str)
        builder.com_alertas(context.get('alert_summary', []))
        builder.com_ordens(context.get('open_order_summary', []), "ORDENS EM ABERTO")
        
        kpis = context.get('equipment_kpis', [])
        if kpis:
            builder.com_ordens(kpis, "KPIs DE EQUIPAMENTOS")
            
        builder.com_telemetria(context.get('telemetry', []))
        builder.com_pergunta(message)
        return builder.build()

    @staticmethod
    def montar_analise_os(builder: PromptBuilder, context: dict, context_str: str, instruction: str, message: str) -> Prompt:
        builder.reset()
        builder.com_contexto(context_str)
        builder.com_ordens(context.get('assigned_order_summary', []), "ORDENS ATRIBUÍDAS")
        builder.com_ordens(context.get('unassigned_order_summary', []), "ORDENS SEM ATRIBUIÇÃO")
        builder.com_instrucoes(instruction)
        builder.com_pergunta(message)
        return builder.build()
        
    @staticmethod
    def montar_ordens_nao_atribuidas(builder: PromptBuilder, context: dict, context_str: str, instruction: str, message: str) -> Prompt:
        builder.reset()
        builder.com_contexto(context_str)
        builder.com_ordens(context.get('unassigned_order_summary', []), "ORDENS SEM ATRIBUIÇÃO (EXEMPLOS)")
        builder.com_instrucoes(instruction)
        builder.com_pergunta(message)
        return builder.build()

    @staticmethod
    def montar_financeiro(builder: PromptBuilder, context: dict, context_str: str, instruction: str, message: str) -> Prompt:
        builder.reset()
        builder.com_contexto(context_str)
        financial = context.get('financial_summary', {})
        if financial.get('top_equipment_costs'):
            builder.com_ordens(financial['top_equipment_costs'], "EQUIPAMENTOS COM MAIOR CUSTO")
        builder.com_instrucoes(instruction)
        builder.com_pergunta(message)
        return builder.build()
