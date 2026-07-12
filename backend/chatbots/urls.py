from django.urls import path
from .views import ChatView, ChatHistoryView, ChatDetailView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('history/', ChatHistoryView.as_view(), name='chat_history'),
    path('<uuid:chat_id>/', ChatDetailView.as_view(), name='chat_detail'),
]
