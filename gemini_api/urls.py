from django.urls import path
from .views import GeminiChatView

urlpatterns = [
    path('chat/', GeminiChatView.as_view(), name='gemini_chat'),
]
