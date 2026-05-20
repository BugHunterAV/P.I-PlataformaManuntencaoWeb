from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

from ativos.models import Equipamento
from alertas.models import Alerta
from manutencao.models import OrdemServico, HistoricoManutencao
from telemetria.models import Sensor, Telemetria
from manutencao.dashboards.views import KpiService

class GeminiChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        message = request.data.get("message")
        history = request.data.get("history", [])

        if not message:
            return Response({"error": "A mensagem é obrigatória."}, status=400)

        # 1. Verificar chave de API
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "CHAVEAQKUI" or len(api_key.strip()) == 0:
            return Response({
                "response": "Olá! A inteligência artificial do NanaSmart não está configurada no momento. "
                            "Por favor, configure uma chave GEMINI_API_KEY válida no arquivo `.env` do backend para habilitar este chat."
            })

        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            return Response({
                "response": f"Erro ao inicializar a IA do Gemini: {str(e)}. "
                            "Por favor, verifique se a chave de API fornecida no `.env` é válida."
            })

        # 2. Compilar informações do banco de dados (Isolamento Multi-tenant!)
        eq_filter = {}
        if user.tipo_usuario != 'admin':
            if user.empresa:
                eq_filter['empresa'] = user.empresa
            else:
                return Response({"response": "Erro: Usuário não possui uma empresa vinculada."})

        equipamentos = Equipamento.objects.filter(**eq_filter).select_related('localizacao')
        total_equipamentos = equipamentos.count()
        ativos_count = equipamentos.filter(status='ativo').count()
        manutencao_count = equipamentos.filter(status='manutencao').count()
        inativo_count = equipamentos.filter(status='inativo').count()

        # KPIs dos Equipamentos
        os_base = OrdemServico.objects.filter(
            status='concluida',
            data_conclusao__isnull=False,
            equipamento__in=equipamentos
        )
        individual_kpis = [KpiService.calcular_kpi(eq, os_base) for eq in equipamentos]

        # Alertas ativos
        alertas = Alerta.objects.filter(equipamento__in=equipamentos, status='ativo')
        alertas_criticos = alertas.filter(nivel='critico').count()
        alertas_medios = alertas.filter(nivel='medio').count()
        alertas_baixos = alertas.filter(nivel='baixo').count()

        alertas_lista = []
        for al in alertas.select_related('equipamento')[:10]:
            alertas_lista.append(f"- [{al.nivel.upper()}] {al.tipo_alerta} no equipamento '{al.equipamento.nome}': {al.descricao} (Aberto em: {al.data_alerta.strftime('%d/%m/%Y %H:%M')})")

        # Ordens de Serviço abertas
        os_abertas = OrdemServico.objects.filter(
            equipamento__in=equipamentos,
            status__in=['pendente', 'andamento']
        ).select_related('equipamento', 'responsavel')

        os_lista = []
        for o in os_abertas[:10]:
            responsavel_nome = o.responsavel.username if o.responsavel else "Não designado"
            os_lista.append(f"- #{o.id} '{o.titulo}' [{o.tipo_os.upper()} / Prioridade: {o.prioridade.upper()}] - Status: {o.status} - Equipamento: {o.equipamento.nome} - Responsável: {responsavel_nome}")

        # Resumo de Equipamentos com seus KPIs
        equipamentos_resumo = []
        for eq, k in zip(equipamentos, individual_kpis):
            disp_txt = f"{k['disponibilidade_porcentagem']}%" if k['disponibilidade_porcentagem'] is not None else "Sem histórico"
            try:
                setor = eq.localizacao.setor
            except Exception:
                setor = "Não informado"

            if user.tipo_usuario in ['admin', 'gestor']:
                # Admin and Gestor see full details including cost
                equipamentos_resumo.append(
                    f"- {k['equipamento']} (ID: {k['equipamento_id']}, Status: {k['status'].upper()}, Local: {setor}) -> "
                    f"MTBF: {k['mtbf_hours']}h | MTTR: {k['mttr_hours']}h | Disponibilidade: {disp_txt} | "
                    f"Manutenções realizadas: {k['total_manutencoes']} | Custo total: R$ {k['custo_total_manutencao']:.2f}"
                )
            else:
                # Technicians see limited info without cost
                equipamentos_resumo.append(
                    f"- {k['equipamento']} (ID: {k['equipamento_id']}, Status: {k['status'].upper()}, Local: {setor}) -> "
                    f"MTBF: {k['mtbf_hours']}h | MTTR: {k['mttr_hours']}h | Disponibilidade: {disp_txt} | "
                    f"Manutenções realizadas: {k['total_manutencoes']}"
                )

        # Telemetria recente
        telemetria_recente = []
        sensores = Sensor.objects.filter(equipamento__in=equipamentos, ativo=True).select_related('equipamento')
        for s in sensores[:10]:
            ultima_leitura = Telemetria.objects.filter(sensor=s).order_by('-timestamp').first()
            if ultima_leitura:
                telemetria_recente.append(
                    f"- Sensor {s.nome} ({s.get_tipo_display()}) no equipamento '{s.equipamento.nome}': "
                    f"Leitura mais recente = {ultima_leitura.valor}{s.unidade_medida} em {ultima_leitura.timestamp.strftime('%d/%m/%Y %H:%M')} (Limite Crítico: {s.limite_alerta}{s.unidade_medida})"
                )

        # Ajuste de resposta baseado no tipo de usuário para evitar vazamento de informações
        if user.tipo_usuario == 'tecnico':
            # Versão resumida para técnicos: informações essenciais sem detalhes sensíveis
            alertas_section = "\n".join(alertas_lista[:5])  # limitar número de alertas exibidos
            os_section = "\n".join(os_lista[:5])
            equipamentos_section = "\n".join(equipamentos_resumo[:5])
            telemetria_section = "\n".join(telemetria_recente[:5])
            system_instruction = f"""
            Você é a "NanaSmart AI", o assistente virtual oficial de inteligência artificial da plataforma NanaSmart (BugHunter AV) de gestão de ativos e manutenção preditiva e corretiva industrial.
            Seu papel é auxiliar operadores e técnicos a analisar a saúde dos equipamentos da planta, entender os indicadores de desempenho e tomar decisões preditivas.

            DIRETRIZ DE ESCOPO ABSOLUTA E CRÍTICA:
            1. Responda EXCLUSIVAMENTE sobre o projeto NanaSmart, a manutenção dos equipamentos da fábrica, telemetrias, ordens de serviço e alertas de sensores.
            2. Se o usuário perguntar sobre QUALQUER assunto fora deste escopo, recuse educadamente.
            3. Não revele informações sensíveis como custos detalhados ou métricas completas de custos da empresa.
            4. Em suas respostas, forneça SUGESTÕES PRÁTICAS do que fazer, COMO CONSERTAR os problemas e COMO ANALISAR as falhas relatadas. Seja sempre voltado para a resolução técnica em campo.

            DADOS ATUAIS EM TEMPO REAL DA FÁBRICA:
            - Empresa: {user.empresa.nome if user.empresa else 'Não vinculada'}
            - Total de Equipamentos Cadastrados: {total_equipamentos}
            - Alertas Ativos no Momento: {alertas.count()}
            - ORDENS DE SERVIÇO EM ABERTO: {len(os_abertas)}

            ALERTAS RELEVANTES (até 5):
            {alertas_section if alertas_section else "Nenhum alerta ativo registrado."}

            ORDENS DE SERVIÇO EM ABERTO (até 5):
            {os_section if os_section else "Nenhuma ordem de serviço aberta no momento."}

            RESUMO DE EQUIPAMENTOS (até 5):
            {equipamentos_section if equipamentos_section else "Nenhum equipamento cadastrado."}

            TELEMETRIA RECENTE (até 5):
            {telemetria_section if telemetria_section else "Sem leituras recentes de telemetria."}

            Dicas importantes para formular suas respostas:
            - Seja direto, técnico e foque no "como fazer", "como resolver" e "como analisar" o problema no equipamento.
            - Sempre mencione qual é o equipamento e onde ele está (Local/Setor) ao dar instruções.
            - Use formatação Markdown elegante.
            """
        elif user.tipo_usuario == 'gestor':
            system_instruction = f"""
            Você é a "NanaSmart AI", o assistente virtual oficial de inteligência artificial da plataforma NanaSmart (BugHunter AV) de gestão de ativos e manutenção preditiva e corretiva industrial.
            Seu papel é auxiliar gestores a administrar a saúde dos equipamentos da sua planta, entender os indicadores de desempenho e tomar decisões estratégicas.

            DIRETRIZ DE ESCOPO ABSOLUTA E CRÍTICA:
            1. Responda EXCLUSIVAMENTE sobre o projeto NanaSmart, a manutenção dos equipamentos da fábrica, telemetrias, ordens de serviço, alertas de sensores, gestão de funcionários e ferramentas de administração de equipamentos.
            2. Se o usuário perguntar sobre QUALQUER assunto fora deste escopo, recuse de forma educada.
            3. SEMPRE inclua nas suas respostas de qual equipamento se trata, qual é o seu modelo/tipo e ONDE ele está localizado (setor/local).
            4. Em suas respostas, foque em oferecer FERRAMENTAS DE GESTÃO de equipamentos e funcionários, insights para melhoria de confiabilidade, redução de custos e alocação eficiente da equipe.

            DADOS ATUAIS EM TEMPO REAL DA SUA EMPRESA:
            - Empresa: {user.empresa.nome if user.empresa else 'Desconhecida'}
            - Total de Equipamentos Cadastrados: {total_equipamentos} (Ativos: {ativos_count} | Em Manutenção: {manutencao_count} | Inativos: {inativo_count})
            - Alertas Ativos no Momento: {alertas.count()} (Críticos: {alertas_criticos} | Médios: {alertas_medios} | Baixos: {alertas_baixos})

            DETALHES DOS ALERTAS ATIVOS:
            {chr(10).join(alertas_lista) if alertas_lista else "Nenhum alerta ativo registrado."}

            ORDENS DE SERVIÇO EM ABERTO (PENDENTE OU EM ANDAMENTO):
            {chr(10).join(os_lista) if os_lista else "Nenhuma ordem de serviço aberta no momento."}

            KPIs E ESTADOS INDIVIDUAIS DOS EQUIPAMENTOS:
            {chr(10).join(equipamentos_resumo) if equipamentos_resumo else "Nenhum equipamento cadastrado."}

            TELEMETRIA RECENTE DOS SENSORES IoT:
            {chr(10).join(telemetria_recente) if telemetria_recente else "Sem leituras recentes de telemetria."}

            Dicas importantes para formular suas respostas:
            - Sugira ferramentas de gestão, planos de ação e melhores práticas de alocação de equipe técnica.
            - Utilize os KPIs financeiros e de confiabilidade disponíveis (Custo, MTBF, MTTR, Disponibilidade).
            - Use formatação Markdown elegante para facilitar a leitura rápida (negrito, marcadores).
            - Seja estratégico e orientado a dados.
            """
        else: # admin
            system_instruction = f"""
            Você é a "NanaSmart AI", o assistente virtual oficial de inteligência artificial da plataforma NanaSmart (BugHunter AV) de gestão de ativos e manutenção preditiva e corretiva industrial.
            Seu papel é auxiliar administradores globais a supervisionar a plataforma, administrar ativos gerais e gerenciar todas as equipes.

            DIRETRIZ DE ESCOPO ABSOLUTA E CRÍTICA:
            1. Responda EXCLUSIVAMENTE sobre o projeto NanaSmart, a manutenção dos equipamentos das fábricas cadastradas, ordens de serviço, alertas, ferramentas de gestão de equipamentos e funcionários em nível sistêmico.
            2. Se o usuário perguntar sobre QUALQUER assunto fora deste escopo, recuse de forma educada.
            3. SEMPRE inclua nas suas respostas de qual equipamento se trata, qual é o seu modelo/tipo, a qual EMPRESA ele pertence (se aplicável) e ONDE ele está localizado (setor/local).
            4. Em suas respostas, foque em oferecer FERRAMENTAS DE GESTÃO de equipamentos e funcionários, insights para melhoria de confiabilidade global, redução de custos e visão consolidada de dados de várias empresas.

            DADOS ATUAIS EM TEMPO REAL DA PLATAFORMA (VISÃO ADMINISTRADOR):
            - Empresa Foco: {user.empresa.nome if user.empresa else 'Todas as Empresas (Modo Administrador Global)'}
            - Total de Equipamentos Cadastrados: {total_equipamentos} (Ativos: {ativos_count} | Em Manutenção: {manutencao_count} | Inativos: {inativo_count})
            - Alertas Ativos no Momento: {alertas.count()} (Críticos: {alertas_criticos} | Médios: {alertas_medios} | Baixos: {alertas_baixos})

            DETALHES DOS ALERTAS ATIVOS:
            {chr(10).join(alertas_lista) if alertas_lista else "Nenhum alerta ativo registrado."}

            ORDENS DE SERVIÇO EM ABERTO (PENDENTE OU EM ANDAMENTO):
            {chr(10).join(os_lista) if os_lista else "Nenhuma ordem de serviço aberta no momento."}

            KPIs E ESTADOS INDIVIDUAIS DOS EQUIPAMENTOS:
            {chr(10).join(equipamentos_resumo) if equipamentos_resumo else "Nenhum equipamento cadastrado."}

            TELEMETRIA RECENTE DOS SENSORES IoT:
            {chr(10).join(telemetria_recente) if telemetria_recente else "Sem leituras recentes de telemetria."}

            Dicas importantes para formular suas respostas:
            - Sugira ferramentas de gestão, planos de ação e melhores práticas de alocação de equipe técnica e visão macro de negócios.
            - Utilize os KPIs financeiros e de confiabilidade disponíveis (Custo, MTBF, MTTR, Disponibilidade).
            - Use formatação Markdown elegante para facilitar a leitura rápida (negrito, marcadores).
            - Seja estratégico, focado em alta gestão e administração sistêmica.
            """

        # 4. Formatar histórico e mensagem para o SDK do Gemini
        contents = []
        for h_item in history:
            role = "user" if h_item.get("role") == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=h_item.get("text"))]
                )
            )

        # Adiciona a mensagem atual
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)]
            )
        )

        # Tenta modelos em ordem de prioridade com fallback automático
        # Modelos verificados como disponíveis na API generateContent do Gemini
        models_to_try = [
            "gemini-2.5-flash",       # Mais recente e rápido
            "gemini-2.0-flash",       # Boa performance geral
            "gemini-1.5-pro",         # Maior capacidade de raciocínio
            "gemini-1.5-flash",       # Rápido e confiável
        ]
        last_error = None

        for model_name in models_to_try:
            try:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,  # Baixo para respostas mais factuais e menos alucinação
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )

                return Response({
                    "response": response.text,
                    "model_used": model_name,
                })

            except Exception as e:
                err_str = str(e)
                # Erros recuperáveis: tenta o próximo modelo
                # 404/NOT_FOUND = modelo não existe nesta versão da API
                # 503/UNAVAILABLE = servidor temporariamente indisponível
                # 429/ResourceExhausted = limite de taxa excedido
                recoverable = (
                    "503" in err_str or "UNAVAILABLE" in err_str or
                    "ResourceExhausted" in err_str or "429" in err_str or
                    "404" in err_str or "NOT_FOUND" in err_str
                )
                if recoverable:
                    last_error = e
                    continue
                # Erro não recuperável (auth, permissão, etc.) retorna imediatamente
                return Response({
                    "response": f"Desculpe, ocorreu um erro na comunicação com o serviço da IA: {err_str}."
                })

        # Todos os modelos falharam
        return Response({
            "response": "Os servidores da IA do Google estão temporariamente indisponíveis. "
                        "Por favor, aguarde alguns instantes e tente novamente."
        })
