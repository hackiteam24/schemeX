import os
import json
import time
import zipfile
import tempfile
import threading
import logging
from django.conf import settings
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sarvamai import SarvamAI

from chatbots.views import call_sarvam, call_nvidia_nim
from common.permissions import IsAdminRole
from applications.models import Application
from .models import Document
from .serializers import DocumentSerializer, DocumentVerificationSerializer

logger = logging.getLogger(__name__)


def verify_document_background(document_id):
    """
    Background worker that runs Sarvam Document Intelligence and performs LLM validation.
    """
    from .models import Document
    
    try:
        # 1. Fetch document and setup API key
        document = Document.objects.get(id=document_id)
        api_key = settings.SARVAM_API_KEY
        if not api_key:
            document.rejection_reason = "Server Configuration Error: SARVAM_API_KEY is missing."
            document.verification_status = Document.VerificationStatus.REJECTED
            document.save()
            return
            
        client = SarvamAI(api_subscription_key=api_key)
        
        # 2. Initiate Sarvam Document Intelligence Job
        job = client.document_intelligence.create_job(
            language="en-IN", # Bilingual/English layout support
            output_format="md"
        )
        
        # Upload the file from media storage
        with document.file.open('rb') as f:
            job.upload_file(f)
        job.start()
        
        # 3. Wait for digitization to complete (max 60 seconds)
        start_time = time.time()
        completed = False
        while time.time() - start_time < 60:
            status_resp = client.document_intelligence.get_job_status(job_id=job.job_id)
            status_str = getattr(status_resp, 'status', '') or (status_resp.get('status', '') if isinstance(status_resp, dict) else '')
            if status_str == 'Completed':
                completed = True
                break
            elif status_str in ('Failed', 'Cancelled'):
                break
            time.sleep(3)
            
        if not completed:
            document.rejection_reason = "Document processing timed out or failed on Sarvam AI."
            document.verification_status = Document.VerificationStatus.REJECTED
            document.save()
            return
            
        # 4. Download and unpack digitized Markdown text
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
            temp_zip_path = temp_zip.name
            
        try:
            job.download_output(temp_zip_path)
            
            markdown_content = ""
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                for file_name in zip_ref.namelist():
                    if file_name.endswith('.md'):
                        with zip_ref.open(file_name) as md_file:
                            markdown_content = md_file.read().decode('utf-8')
                            break
        finally:
            if os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
                
        if not markdown_content:
            document.rejection_reason = "Extracted document text was empty."
            document.verification_status = Document.VerificationStatus.REJECTED
            document.save()
            return
            
        # 5. Build verification query for LLM
        user = document.uploaded_by
        doc_type_name = document.get_document_type_display()
        
        system_prompt = (
            "You are an automated document verification assistant for SchemeX.\n"
            "Analyze the digitized text extracted from the document to determine if it is authentic, "
            "matches the expected document type, and corresponds to the registered user profile.\n\n"
            f"Expected Document Type: {doc_type_name}\n"
            "Registered User details:\n"
            f"- Full Name: {user.first_name} {user.last_name}\n"
            f"- Username/ID: {user.username}\n\n"
            "Rules:\n"
            "1. Check if the document text matches the expected type.\n"
            "2. Check if the name on the document matches the user's name (allow minor spelling variations or middle-name differences).\n"
            "3. Make a solid judgment check. If there are contradictions or it belongs to someone else, reject it.\n\n"
            "Return ONLY a valid JSON object in this exact format (no codeblocks, no extra words):\n"
            "{\n"
            '  "is_verified": true,\n'
            '  "rejection_reason": ""\n'
            "}\n"
            "If verified is false, provide a clear reason for rejection in 'rejection_reason'."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Digitized text:\n\n{markdown_content}"}
        ]
        
        # 6. Execute Chat Completion
        if settings.AI_PROVIDER == "sarvam":
            llm_reply = call_sarvam(messages)
        else:
            llm_reply = call_nvidia_nim(messages)
            
        # 7. Clean and parse LLM JSON response
        llm_reply = llm_reply.strip()
        if llm_reply.startswith("```"):
            lines = llm_reply.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            llm_reply = "\n".join(lines).strip()
            
        result = json.loads(llm_reply)
        
        # 8. Save status
        if result.get("is_verified") is True:
            document.verification_status = Document.VerificationStatus.VERIFIED
            document.rejection_reason = ""
        else:
            document.verification_status = Document.VerificationStatus.REJECTED
            document.rejection_reason = result.get("rejection_reason", "AI verification failed.")
            
        document.save()
        
    except Exception as e:
        logger.error(f"Error during async document verification: {str(e)}", exc_info=True)
        try:
            doc = Document.objects.get(id=document_id)
            doc.rejection_reason = f"Verification engine failed: {str(e)}"
            doc.verification_status = Document.VerificationStatus.REJECTED
            doc.save()
        except:
            pass


def build_required_documents(user):
    uploaded_documents = Document.objects.filter(uploaded_by=user)
    uploaded_labels = {
        doc.get_document_type_display().lower()
        for doc in uploaded_documents
    }
    uploaded_file_names = {
        doc.file.name.rsplit("/", 1)[-1].lower()
        for doc in uploaded_documents
    }

    required = {}
    applications = Application.objects.filter(applicant=user).select_related("scheme")
    for application in applications:
        for document_name in application.scheme.required_documents_list:
            key = document_name.strip().lower()
            if not key:
                continue
            uploaded = any(key in label for label in uploaded_labels | uploaded_file_names)
            required[key] = {
                "name": document_name,
                "scheme": application.scheme.name,
                "uploaded": uploaded,
            }

    return list(required.values())


class DocumentListView(APIView):
    """GET /api/documents/ - the current user's documents (admins may pass ?all=1)."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        qs = Document.objects.select_related("uploaded_by", "application")
        is_admin = user.is_staff or getattr(user, "role", None) == "admin"
        if not (is_admin and request.query_params.get("all")):
            qs = qs.filter(uploaded_by=user)
        serializer = DocumentSerializer(qs, many=True, context={"request": request})
        payload = {"documents": serializer.data}
        if not is_admin:
            payload["required_documents"] = build_required_documents(user)
        return Response(payload)


class DocumentUploadView(APIView):
    """POST /api/documents/upload/ - multipart upload of a supporting document."""

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        data = request.data.copy()
        if "file" not in data and "document" in data:
            data["file"] = data["document"]

        doc_type = data.get("document_type")
        if doc_type:
            doc_type_str = str(doc_type).lower().strip()
            if "aadhaar" in doc_type_str or "adhar" in doc_type_str or "uidai" in doc_type_str:
                data["document_type"] = "aadhaar"
            elif "pan" in doc_type_str:
                data["document_type"] = "pan"
            elif "income" in doc_type_str:
                data["document_type"] = "income_certificate"
            elif "caste" in doc_type_str:
                data["document_type"] = "caste_certificate"
            elif "residence" in doc_type_str or "address" in doc_type_str or "domicile" in doc_type_str:
                data["document_type"] = "residence_proof"
            elif "bank" in doc_type_str or "passbook" in doc_type_str:
                data["document_type"] = "bank_passbook"
            elif "ration" in doc_type_str:
                data["document_type"] = "ration_card"
            elif "photo" in doc_type_str or "image" in doc_type_str:
                data["document_type"] = "photo"
            else:
                valid_keys = [choice[0] for choice in Document.DocumentType.choices]
                if doc_type_str not in valid_keys:
                    data["document_type"] = "other"
                else:
                    data["document_type"] = doc_type_str
        else:
            data["document_type"] = Document.DocumentType.OTHER

        serializer = DocumentSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        # Trigger AI automated document verification in a background thread
        threading.Thread(
            target=verify_document_background,
            args=(document.id,),
            daemon=True
        ).start()

        return Response(
            {"message": "Document uploaded successfully.", "document": DocumentSerializer(document, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    """GET/DELETE /api/documents/<id>/"""

    permission_classes = (IsAuthenticated,)

    def _get_document(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        user = request.user
        is_admin = user.is_staff or getattr(user, "role", None) == "admin"
        if document.uploaded_by_id != user.id and not is_admin:
            return None
        return document

    def get(self, request, pk):
        document = self._get_document(request, pk)
        if document is None:
            return Response({"message": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        return Response(DocumentSerializer(document, context={"request": request}).data)

    def delete(self, request, pk):
        document = self._get_document(request, pk)
        if document is None:
            return Response({"message": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        document.delete()
        return Response({"message": "Document deleted."}, status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadView(APIView):
    """GET /api/documents/<id>/download/ - returns a direct URL to the stored file."""

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        user = request.user
        is_admin = user.is_staff or getattr(user, "role", None) == "admin"
        if document.uploaded_by_id != user.id and not is_admin:
            return Response({"message": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        return Response({"download_url": request.build_absolute_uri(document.file.url)})


class DocumentVerifyView(APIView):
    """PATCH /api/documents/<id>/verify/ - admin-only verification workflow."""

    permission_classes = (IsAuthenticated, IsAdminRole)

    def patch(self, request, pk):
        document = get_object_or_404(Document, pk=pk)
        serializer = DocumentVerificationSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DocumentSerializer(document, context={"request": request}).data)
