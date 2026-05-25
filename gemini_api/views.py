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


class GeminiChatView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Pergunte ao assistente de manutenção sobre o parque de ativos e ordens de serviço.",
    )
    def post(self, request):
        serializer = GeminiMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])

        if not is_gemini_available():
            return Response({
                "response": "A IA do Gemini não está configurada no backend. "
                            "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar o chat."}
            )

        context = build_base_context(user)
        system_instruction = build_system_instruction(user, "responder perguntas gerais sobre o parque de ativos e manutenção")
        user_prompt = build_chat_prompt(message, context)

        try:
            response_text, model_used = generate_content(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                history=history,
                temperature=0.4,
            )
            return Response({"response": response_text, "model_used": model_used})
        except Exception as e:
            return Response({"response": f"Erro ao gerar resposta da IA: {e}"})


class GeminiOsAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Solicite análise das ordens de serviço abertas e recomendações práticas de ação.",
    )
    def post(self, request):
        serializer = GeminiMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])

        if not is_gemini_available():
            return Response({
                "response": "A IA do Gemini não está configurada no backend. "
                            "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar este endpoint."}
            )

        context = build_base_context(user)
        system_instruction = build_system_instruction(user, "analisar ordens de serviço e indicar ações práticas")
        user_prompt = build_os_analysis_prompt(user, context, message)

        try:
            response_text, model_used = generate_content(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                history=history,
                temperature=0.35,
            )
            return Response({"response": response_text, "model_used": model_used})
        except Exception as e:
            return Response({"response": f"Erro ao gerar análise da IA: {e}"})


class GeminiUnassignedOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Avalie ordens sem atribuição e indique critérios de priorização e alocação.",
    )
    def post(self, request):
        serializer = GeminiMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])

        if not is_gemini_available():
            return Response({
                "response": "A IA do Gemini não está configurada no backend. "
                            "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar este endpoint."}
            )

        context = build_base_context(user)
        system_instruction = build_system_instruction(user, "avaliar ordens sem atribuição e sugerir prioridades")
        user_prompt = build_unassigned_orders_prompt(context, message)

        try:
            response_text, model_used = generate_content(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                history=history,
                temperature=0.35,
            )
            return Response({"response": response_text, "model_used": model_used})
        except Exception as e:
            return Response({"response": f"Erro ao gerar estratégia da IA: {e}"})


class GeminiFinanceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=GeminiMessageSerializer,
        responses=GeminiResponseSerializer,
        description="Solicite orientação financeira e de redução de custos para manutenção.",
    )
    def post(self, request):
        serializer = GeminiMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        message = serializer.validated_data['message']
        history = serializer.validated_data.get('history', [])

        if user.tipo_usuario == 'tecnico':
            return Response({
                "response": "Este endpoint é dedicado a gestores e administradores. "
                            "Técnicos podem usar o chat geral ou a análise de ordens de serviço."},
                status=403
            )

        if not is_gemini_available():
            return Response({
                "response": "A IA do Gemini não está configurada no backend. "
                            "Adicione a variável GEMINI_API_KEY ao `.env` para habilitar este endpoint."}
            )

        context = build_base_context(user)
        context['financial_summary'] = get_financial_summary(user)
        system_instruction = build_system_instruction(user, "avaliar custos e gestão financeira de manutenção")
        user_prompt = build_finance_prompt(user, context, message)

        try:
            response_text, model_used = generate_content(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                history=history,
                temperature=0.35,
            )
            return Response({"response": response_text, "model_used": model_used})
        except Exception as e:
            return Response({"response": f"Erro ao gerar orientação financeira da IA: {e}"})
