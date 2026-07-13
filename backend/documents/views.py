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


def update_profile_from_document(user, extracted_data):
    if not extracted_data:
        return
        
    from profiles.models import Profile
    profile, _ = Profile.objects.get_or_create(
        user=user, defaults={"full_name": user.get_full_name() or user.username}
    )
    
    changed = False
    
    # 1. Personal Details
    full_name = extracted_data.get("fullName")
    if full_name and not profile.full_name:
        profile.full_name = full_name
        changed = True
        
    gender = extracted_data.get("gender")
    if gender and not profile.gender:
        normalized_gender = gender.strip().lower()
        if normalized_gender in ["male", "female", "other"]:
            profile.gender = normalized_gender
            changed = True
            
    category = extracted_data.get("category")
    if category and not profile.category:
        profile.category = category.strip().lower()
        changed = True
        
    aadhaar_number = extracted_data.get("aadhaarNumber") or extracted_data.get("aadhaar")
    if aadhaar_number and not profile.aadhaar_number:
        # Clean non-digits
        clean_aadhaar = "".join(filter(str.isdigit, str(aadhaar_number)))
        if len(clean_aadhaar) == 12:
            profile.aadhaar_number = clean_aadhaar
            changed = True
            
    # 2. Location Details
    state = extracted_data.get("state")
    if state and not profile.state:
        profile.state = state
        changed = True
        
    district = extracted_data.get("district")
    if district and not profile.district:
        profile.district = district
        changed = True
        
    tehsil = extracted_data.get("tehsil")
    if tehsil and not profile.tehsil:
        profile.tehsil = tehsil
        changed = True
        
    village = extracted_data.get("village")
    if village and not profile.village:
        profile.village = village
        changed = True
        
    pincode = extracted_data.get("pincode")
    if pincode and not profile.pincode:
        profile.pincode = pincode
        changed = True

    # 3. Economic/Land details
    annual_income_str = extracted_data.get("annualIncome")
    if annual_income_str:
        try:
            val = int(float(str(annual_income_str).replace(",", "").strip()))
            if val > 0 and profile.annual_income == 0:
                profile.annual_income = val
                changed = True
        except:
            pass

    # 4. Bank Details
    bank_name = extracted_data.get("bankName")
    if bank_name and not profile.bank_name:
        profile.bank_name = bank_name
        changed = True
        
    account_number = extracted_data.get("accountNumber")
    if account_number and not profile.account_number:
        profile.account_number = account_number
        changed = True
        
    ifsc_code = extracted_data.get("ifscCode")
    if ifsc_code and not profile.ifsc_code:
        profile.ifsc_code = ifsc_code.strip().upper()
        changed = True
        
    if changed:
        profile.save()


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
        job.upload_file(document.file.path)
        job.start()
        
        # 3. Wait for digitization to complete (uses SDK's built-in polling)
        job.wait_until_complete()
            
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
            '  "rejection_reason": "",\n'
            '  "extracted_data": {\n'
            '    "fullName": "...",\n'
            '    "gender": "male/female/other",\n'
            '    "category": "OBC/SC/ST/General",\n'
            '    "state": "...",\n'
            '    "district": "...",\n'
            '    "tehsil": "...",\n'
            '    "village": "...",\n'
            '    "pincode": "...",\n'
            '    "annualIncome": "...",\n'
            '    "bankName": "...",\n'
            '    "accountNumber": "...",\n'
            '    "ifscCode": "..."\n'
            '  }\n'
            "}\n"
            "If verified is false, set is_verified to false and provide a clear reason for rejection in 'rejection_reason'."
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
            
            # Automatically update citizen's Profile in the background!
            try:
                update_profile_from_document(document.uploaded_by, result.get("extracted_data"))
            except Exception as pe:
                logger.error(f"Failed to update profile from document: {str(pe)}")
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


def is_document_matching(uploaded_doc, required_name):
    req_clean = required_name.lower()
    doc_type = uploaded_doc.document_type.lower()
    doc_display = uploaded_doc.get_document_type_display().lower()
    file_name = uploaded_doc.file.name.lower() if uploaded_doc.file else ""
    
    # 1. Aadhaar Card keyword mapping
    if "aadhaar" in doc_type or "aadhaar" in doc_display:
        if "aadhaar" in req_clean or "identity" in req_clean or "age" in req_clean:
            return True
            
    # 2. PAN Card keyword mapping
    if "pan" in doc_type or "pan" in doc_display:
        if "pan" in req_clean or "identity" in req_clean or "age" in req_clean:
            return True
            
    # 3. Residence/Domicile Proof keyword mapping
    if "residence" in doc_type or "residence" in doc_display or "domicile" in doc_type or "domicile" in doc_display:
        if "residence" in req_clean or "address" in req_clean or "domicile" in req_clean:
            return True
            
    # 4. Caste Certificate keyword mapping
    if "caste" in doc_type or "caste" in doc_display:
        if "caste" in req_clean:
            return True
            
    # 5. Income Certificate keyword mapping
    if "income" in doc_type or "income" in doc_display:
        if "income" in req_clean:
            return True
            
    # 6. Bank Passbook keyword mapping
    if "bank" in doc_type or "bank" in doc_display or "passbook" in doc_type or "passbook" in doc_display:
        if "bank" in req_clean or "passbook" in req_clean or "account" in req_clean:
            return True
            
    # 7. Mobile/Telecom statement keyword mapping
    if "mobile" in doc_type or "mobile" in doc_display or "mobile" in file_name or "bill" in file_name or "statement" in file_name:
        if "mobile" in req_clean or "contact" in req_clean or "email" in req_clean or "e-mail" in req_clean:
            return True
            
    # 8. Passport Photograph keyword mapping
    if "photo" in doc_type or "photo" in doc_display:
        if "photo" in req_clean or "photograph" in req_clean:
            return True

    # Fallback to simple substring checks
    for term in [doc_type, doc_display, file_name]:
        if term and (term in req_clean or req_clean in term):
            return True
            
    return False


def build_required_documents(user, scheme_id=None):
    uploaded_documents = Document.objects.filter(uploaded_by=user)
    required = {}
    
    # Get active applications
    applications = Application.objects.filter(applicant=user).select_related("scheme")
    schemes = [app.scheme for app in applications]
    
    # If a specific scheme parameter is passed (e.g. from the apply flow redirection), include it
    if scheme_id:
        from schemes.models import Scheme
        try:
            scheme = Scheme.objects.get(id=scheme_id)
            if scheme not in schemes:
                schemes.append(scheme)
        except Scheme.DoesNotExist:
            pass
            
    for scheme in schemes:
        for document_name in scheme.required_documents_list:
            key = document_name.strip().lower()
            if not key:
                continue
            
            # Check if any uploaded document matches the required name using our smart matcher
            uploaded = any(is_document_matching(doc, document_name) for doc in uploaded_documents)
            
            required[key] = {
                "name": document_name,
                "scheme": scheme.name,
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
            scheme_id = request.query_params.get("scheme")
            payload["required_documents"] = build_required_documents(user, scheme_id=scheme_id)
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
