from django.urls import path
from .views import ChatView, ChatHistoryView, ChatDetailView, SpeechToTextView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('history/', ChatHistoryView.as_view(), name='chat_history'),
    path('<uuid:chat_id>/', ChatDetailView.as_view(), name='chat_detail'),
    path('speech-to-text/', SpeechToTextView.as_view(), name='speech_to_text'),
]
