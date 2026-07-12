from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminRole
from applications.models import Application
from .models import Document
from .serializers import DocumentSerializer, DocumentVerificationSerializer


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
