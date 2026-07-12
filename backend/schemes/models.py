from django.db import models

from common.models import TimeStampedUUIDModel


class Scheme(TimeStampedUUIDModel):
    """A government welfare scheme citizens can browse, check eligibility for, and apply to."""

    name = models.CharField("Scheme Name", max_length=255)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    department = models.CharField(max_length=150, blank=True)
    description = models.TextField()
    benefits = models.TextField(blank=True)
    eligibility_criteria = models.TextField(blank=True)
    required_documents = models.TextField(
        blank=True,
        help_text="Comma or newline separated list of documents needed to apply.",
    )
    how_to_apply = models.TextField(blank=True, help_text="Steps / process to apply for this scheme.")
    official_link = models.URLField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Structured Eligibility Parameters
    state = models.CharField(max_length=50, default="all", help_text="State code (e.g., ap, ts, tn, all)")
    min_age = models.IntegerField(null=True, blank=True)
    max_age = models.IntegerField(null=True, blank=True)
    gender_limit = models.CharField(max_length=20, blank=True, help_text="male, female, other, or blank for all")
    max_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bpl_required = models.BooleanField(default=False)
    land_required = models.BooleanField(default=False)
    caste_categories = models.CharField(max_length=255, blank=True, help_text="Comma-separated eligible categories (e.g., general,sc,st,obc,ews)")

    class Meta:
        db_table = "schemes_scheme"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return self.name

    @property
    def required_documents_list(self):
        if not self.required_documents:
            return []
        return [d.strip() for d in self.required_documents.replace("\n", ",").split(",") if d.strip()]