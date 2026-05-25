from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .cliente import generate_content, is_gemini_available
from .context_service import build_base_context, get_financial_summary
from .prompt_builder import (
    build_system_instruction,
    build_chat_prompt,
    build_os_analysis_prompt,
    build_unassigned_orders_prompt,
    build_finance_prompt,
)
from .serializers import (
    GeminiMessageSerializer,
    GeminiResponseSerializer,
)


class GeminiBaseView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GeminiMessageSerializer
    response_serializer_class = GeminiResponseSerializer
    system_purpose = "fornecer orientação de manutenção"
    prompt_builder = None
    temperature = 0.35
    missing_api_suffix = "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar este endpoint."
    forbidden_message = None
    requires_financial_summary = False

    def get_missing_api_response(self):
        return {
            "response": f"A IA do Gemini não está configurada no backend. {self.missing_api_suffix}"
        }

    def check_access(self, user):
        return True

    def get_prompt(self, user, context, message):
        if self.prompt_builder is None:
            return message
        prompt_fn = type(self).prompt_builder
        return prompt_fn(user, context, message)

    def run_gemini(self, system_instruction, user_prompt, history):
        return generate_content(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            history=history,
            temperature=self.temperature,
        )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])

        if self.forbidden_message and not self.check_access(user):
            return Response({"response": self.forbidden_message}, status=403)

        if not is_gemini_available():
            return Response(self.get_missing_api_response())

        context = build_base_context(user)
        if self.requires_financial_summary:
            context['financial_summary'] = get_financial_summary(user)

        system_instruction = build_system_instruction(user, self.system_purpose)
        user_prompt = self.get_prompt(user, context, message)

        try:
            response_text, model_used = self.run_gemini(system_instruction, user_prompt, history)
            return Response({"response": response_text, "model_used": model_used})
        except Exception as e:
            return Response({"response": f"Erro ao gerar resposta da IA: {e}"})


class GeminiChatView(GeminiBaseView):
    system_purpose = "responder perguntas gerais sobre o parque de ativos e manutenção"
    prompt_builder = build_chat_prompt
    temperature = 0.4
    missing_api_suffix = "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar o chat."

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Pergunte ao assistente de manutenção sobre o parque de ativos e ordens de serviço.",
    )
    def post(self, request):
        return super().post(request)


class GeminiOsAnalysisView(GeminiBaseView):
    system_purpose = "analisar ordens de serviço e indicar ações práticas"
    prompt_builder = build_os_analysis_prompt

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Solicite análise das ordens de serviço abertas e recomendações práticas de ação.",
    )
    def post(self, request):
        return super().post(request)


class GeminiUnassignedOrdersView(GeminiBaseView):
    system_purpose = "avaliar ordens sem atribuição e sugerir prioridades"

    def get_prompt(self, user, context, message):
        return build_unassigned_orders_prompt(user, context, message)

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Avalie ordens sem atribuição e indique critérios de priorização e alocação.",
    )
    def post(self, request):
        return super().post(request)


class GeminiFinanceView(GeminiBaseView):
    system_purpose = "avaliar custos e gestão financeira de manutenção"
    requires_financial_summary = True
    forbidden_message = (
        "Este endpoint é dedicado a gestores e administradores. "
        "Técnicos podem usar o chat geral ou a análise de ordens de serviço."
    )

    def check_access(self, user):
        return user.tipo_usuario != 'tecnico'

    def get_prompt(self, user, context, message):
        return build_finance_prompt(user, context, message)

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Solicite orientação financeira e de redução de custos para manutenção.",
    )
    def post(self, request):
        return super().post(request)
