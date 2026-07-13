import os
import logging
import tempfile

import requests
from django.conf import settings
from rest_framework import status
from sarvamai import SarvamAI
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatSession
from .prompt_builder import build_messages
from .retrieval import SchemeRetriever, detect_state

logger = logging.getLogger(__name__)


def call_nvidia_nim(messages):
    """
    Calls an NVIDIA NIM hosted model via their OpenAI-compatible chat completions endpoint.
    """

    api_key = settings.NVIDIA_API_KEY

    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY is not set. Add it to your .env file.")

    url = "https://integrate.api.nvidia.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.NVIDIA_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 512,
    }

    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print("\n" + "=" * 70)
    print("NVIDIA RESPONSE")
    print("Status Code:", resp.status_code)
    print("Response Body:")
    print(resp.text)
    print("=" * 70 + "\n")

    if not resp.ok:
        raise RuntimeError(f"NVIDIA API Error ({resp.status_code}): {resp.text}")

    data = resp.json()

    return data["choices"][0]["message"]["content"]


def call_sarvam(messages):
    """
    Calls Sarvam AI's Chat Completions API via the official sarvamai SDK.
    """

    api_key = settings.SARVAM_API_KEY

    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set. Add it to your .env file.")

    client = SarvamAI(api_subscription_key=api_key)

    response = client.chat.completions(
        model=settings.SARVAM_MODEL,
        messages=messages,
        reasoning_effort=None,
        frequency_penalty=0.4,
        presence_penalty=0.2,
    )

    return response.choices[0].message.content


def detect_script_language(text):
    for char in text:
        code = ord(char)
        if 0x0C00 <= code <= 0x0C7F:
            return "te"  # Telugu
        if 0x0900 <= code <= 0x097F:
            return "hi"  # Hindi
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"  # Tamil
        if 0x0C80 <= code <= 0x0CFF:
            return "kn"  # Kannada
        if 0x0D00 <= code <= 0x0D7F:
            return "ml"  # Malayalam
    return None


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        message = request.data.get("message", "").strip()
        chat_id = request.data.get("chat_id")
        language = request.data.get("language", "en")
        # Optional today (frontend doesn't send it yet); wires straight into
        # the retrieval layer once a state-scoped UI exists.
        state = request.data.get("state")

        if not message:
            return Response(
                {"message": "message field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        if chat_id:
            try:
                session = ChatSession.objects.get(id=chat_id)
                # Enforce ownership check (IDOR mitigation)
                if session.user != user:
                    return Response(
                        {"message": "Not authorized to access this chat session."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(
                    user=user,
                    title=message[:50],
                )
        else:
            session = ChatSession.objects.create(
                user=user,
                title=message[:50],
            )

        ChatMessage.objects.create(
            session=session,
            sender="user",
            content=message,
        )

        # Fetch the 10 most recent messages and order them chronologically (oldest first)
        history = list(reversed(session.messages.order_by("-created_at")[:10]))

        # Dataset Retrieval Layer -> Relevant Scheme Search
        # Returns [] until real dataset files exist (see retrieval.py) — no
        # behavior change today, just the seam for tomorrow's integration.
        prior_user_messages = " ".join(
            m.content for m in history if m.sender == "user"
        )[-300:]
        search_query = f"{prior_user_messages} {message}".strip()

        if not state:
            state = detect_state(message) or detect_state(search_query)

        retrieved_schemes = SchemeRetriever().search(
            search_query,
            state=state,
            limit=15 if state else 5,
        )

        # 1. Detect language from script characters (e.g. typing in Telugu/Hindi script)
        script_lang = detect_script_language(message)
        if script_lang:
            language = script_lang
        else:
            # 2. Detect language from explicit English instructions/keywords
            msg_lower = message.lower()
            if "english" in msg_lower or "in english" in msg_lower or "speak english" in msg_lower or "talk english" in msg_lower:
                language = "en"
            elif "telugu" in msg_lower or "in telugu" in msg_lower or "speak telugu" in msg_lower:
                language = "te"
            elif "hindi" in msg_lower or "in hindi" in msg_lower or "speak hindi" in msg_lower:
                language = "hi"
            elif "tamil" in msg_lower or "in tamil" in msg_lower or "speak tamil" in msg_lower:
                language = "ta"
            elif "kannada" in msg_lower or "in kannada" in msg_lower or "speak kannada" in msg_lower:
                language = "kn"
            elif "malayalam" in msg_lower or "in malayalam" in msg_lower or "speak malayalam" in msg_lower:
                language = "ml"

        # Prompt Builder -> System Prompt
        api_messages = build_messages(language, history, retrieved_schemes)

        try:
            if settings.AI_PROVIDER == "sarvam":
                ai_reply = call_sarvam(api_messages)
            else:
                ai_reply = call_nvidia_nim(api_messages)

        except Exception as e:

            logger.exception("AI provider call failed (%s)", settings.AI_PROVIDER)
            return Response(
                {
                    "success": False,
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ChatMessage.objects.create(
            session=session,
            sender="ai",
            content=ai_reply,
        )

        return Response(
            {
                "success": True,
                "response": ai_reply,
                "chat_id": session.id,
            },
            status=status.HTTP_200_OK,
        )


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = ChatSession.objects.filter(user=request.user).order_by("-updated_at")

        chats = [
            {
                "id": s.id,
                "title": s.title,
                "preview": s.preview(),
            }
            for s in sessions
        ]

        return Response({"chats": chats})


class ChatDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):

        try:
            session = ChatSession.objects.get(id=chat_id)

        except ChatSession.DoesNotExist:
            return Response(
                {"message": "Chat not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_admin = (
            request.user.is_staff or getattr(request.user, "role", None) == "admin"
        )

        if session.user != request.user and not is_admin:
            return Response(
                {"message": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN,
            )

        messages = [
            {
                "sender": m.sender,
                "content": m.content,
            }
            for m in session.messages.all()
        ]

        return Response({"messages": messages})


class SpeechToTextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No audio file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_file = request.FILES['file']

        api_key = settings.SARVAM_API_KEY
        if not api_key:
            return Response(
                {"error": "SARVAM_API_KEY is not configured on the server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Reject oversized uploads (>10MB) to avoid cost/timeout issues
        if audio_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "Audio file too large (max 10MB)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Pick correct file suffix based on actual recorded mimetype
        content_type = audio_file.content_type or 'audio/webm'
        ext = content_type.split('/')[-1].split(';')[0]
        if ext not in ('webm', 'mp4', 'ogg', 'wav'):
            ext = 'webm'

        temp_file_path = None
        try:
            client = SarvamAI(api_subscription_key=api_key)

            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as f:
                response = client.speech_to_text.transcribe(
                    file=f,
                    model="saaras:v3",
                    mode="transcribe"
                )

            transcript = getattr(response, 'transcript', '') or (
                response.get('transcript', '') if isinstance(response, dict) else ''
            )
            return Response({"transcript": transcript}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Sarvam Speech-to-Text Error: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to transcribe audio: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
