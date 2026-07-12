from django.conf import settings
from django.db import models

from applications.models import Application
from common.models import TimeStampedUUIDModel


def document_upload_path(instance, filename):
    return f"documents/{instance.uploaded_by_id}/{filename}"


class Document(TimeStampedUUIDModel):
    """A file (ID proof, income certificate, etc.) uploaded by a citizen."""

    class DocumentType(models.TextChoices):
        AADHAAR = "aadhaar", "Aadhaar Card"
        PAN = "pan", "PAN Card"
        INCOME_CERTIFICATE = "income_certificate", "Income Certificate"
        CASTE_CERTIFICATE = "caste_certificate", "Caste Certificate"
        RESIDENCE_PROOF = "residence_proof", "Residence Proof"
        BANK_PASSBOOK = "bank_passbook", "Bank Passbook"
        RATION_CARD = "ration_card", "Ration Card"
        PHOTO = "photo", "Passport Photo"
        OTHER = "other", "Other"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
        help_text="Optional link to the application this document supports.",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_path)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING
    )
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents_document"
        ordering = ["-upload_date"]
        indexes = [
            models.Index(fields=["document_type"]),
            models.Index(fields=["verification_status"]),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.uploaded_by.username}"
