"""
Seeds the `Scheme` table (used by the /api/schemes/ browse + search page)
directly from the Schemes.csv dataset from data.gov.in / MyScheme hosted on Hugging Face.

Run after adding/editing the dataset:
    python manage.py seed_schemes

Safe to re-run: existing rows are matched by (name, state) and updated in
place rather than duplicated.
"""

import csv
import urllib.request
from pathlib import Path
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from schemes.models import Scheme

DATASET_DIR = Path(__file__).resolve().parents[3] / "chatbots" / "datasets"
CSV_PATH = DATASET_DIR / "Schemes.csv"
CSV_URL = "https://huggingface.co/datasets/smartduketech/indian-government-schemes-2025/resolve/main/Schemes.csv"

STATE_CODE_MAP = {
    'Andaman and Nicobar Islands': 'andaman',
    'Andhra Pradesh': 'andhra',
    'Arunachal Pradesh': 'arunachal',
    'Assam': 'assam',
    'Bihar': 'bihar',
    'Central': 'all',
    'Chandigarh': 'chandigarh',
    'Chhattisgarh': 'chhattisgarh',
    'Dadra & Nagar Haveli and Daman & Diu': 'dadra_nagar_haveli',
    'Delhi': 'delhi',
    'Goa': 'goa',
    'Gujarat': 'gujarat',
    'Haryana': 'haryana',
    'Himachal Pradesh': 'hp',
    'Jammu and Kashmir': 'jk',
    'Jharkhand': 'jharkhand',
    'Karnataka': 'karnataka',
    'Kerala': 'kerala',
    'Ladakh': 'ladakh',
    'Lakshadweep': 'lakshadweep',
    'Madhya Pradesh': 'mp',
    'Maharashtra': 'maharashtra',
    'Manipur': 'manipur',
    'Meghalaya': 'meghalaya',
    'Mizoram': 'mizoram',
    'Nagaland': 'nagaland',
    'Odisha': 'odisha',
    'Puducherry': 'puducherry',
    'Punjab': 'punjab',
    'Rajasthan': 'rajasthan',
    'Sikkim': 'sikkim',
    'Tamil Nadu': 'tamilnadu',
    'Telangana': 'telangana',
    'Tripura': 'tripura',
    'Uttar Pradesh': 'up',
    'Uttarakhand': 'uttarakhand',
    'West Bengal': 'wb',
}

CATEGORY_MAP = {
    'Agriculture': 'agriculture',
    'Housing & Shelter': 'housing',
    'Health & Wellness': 'health',
    'Education & Learning': 'education',
    'Skills & Employment': 'employment',
    'Women and Child': 'women',
    'Social welfare & Empowerment': 'social_welfare',
    'Banking': 'banking',
    'Business & Entrepreneurship': 'business_entrepreneurship',
    'Financial Services and Insurance': 'financial_services',
    'IT & Communications': 'it_communications',
    'Law & Justice': 'law_justice',
    'Public Safety': 'public_safety',
    'Rural & Environment': 'rural_environment',
    'Science': 'science',
    'Sports & Culture': 'sports_culture',
    'Transport & Infrastructure': 'transport_infrastructure',
    'Travel & Tourism': 'travel_tourism',
    'Utility & Sanitation': 'utility_sanitation',
}


class Command(BaseCommand):
    help = "Seeds/updates the Scheme table from MyScheme CSV dataset."

    def handle(self, *args, **options):
        if not DATASET_DIR.exists():
            DATASET_DIR.mkdir(parents=True, exist_ok=True)

        if not CSV_PATH.exists():
            self.stdout.write(f"Downloading dataset from {CSV_URL}...")
            try:
                req = urllib.request.Request(
                    CSV_URL,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req) as response, open(CSV_PATH, "wb") as f:
                    f.write(response.read())
                self.stdout.write(self.style.SUCCESS("Dataset downloaded successfully."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to download dataset: {e}"))
                return

        created, updated = 0, 0

        self.stdout.write("Parsing schemes from CSV and updating database...")
        
        with open(CSV_PATH, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            
            # Use transaction to speed up insertions
            with transaction.atomic():
                for row in reader:
                    name = row.get("name", "").strip()
                    if not name:
                        continue

                    # Truncate name if it exceeds CharField max_length=255
                    if len(name) > 255:
                        name = name[:252] + "..."

                    # Map state
                    raw_state = row.get("state")
                    state = STATE_CODE_MAP.get(raw_state, raw_state.lower().replace(" & ", "_").replace(" ", "_") if raw_state else "all")

                    # Map category
                    raw_cat = row.get("category", "")
                    if raw_cat and raw_cat != "null":
                        parts = [p.strip() for p in raw_cat.split(",") if p.strip()]
                        if parts:
                            category = CATEGORY_MAP.get(parts[0], parts[0].lower().replace(" & ", "_").replace(" ", "_"))
                        else:
                            category = "social_welfare"
                    else:
                        category = "social_welfare"

                    # Combine ministry and department
                    ministry = row.get("ministry", "")
                    dept = row.get("department", "")
                    if ministry and ministry != "null" and dept and dept != "null":
                        department = f"{ministry.strip()} - {dept.strip()}"
                    elif dept and dept != "null":
                        department = dept.strip()
                    elif ministry and ministry != "null":
                        department = ministry.strip()
                    else:
                        department = ""

                    if len(department) > 150:
                        department = department[:147] + "..."

                    # Parse eligibility parameters
                    try:
                        min_age = int(row.get("eligibility_age_min")) if row.get("eligibility_age_min") not in (None, "", "null") else None
                    except ValueError:
                        min_age = None

                    try:
                        max_age = int(row.get("eligibility_age_max")) if row.get("eligibility_age_max") not in (None, "", "null") else None
                    except ValueError:
                        max_age = None

                    try:
                        max_income = Decimal(row.get("eligibility_income_max")) if row.get("eligibility_income_max") not in (None, "", "null") else None
                    except (InvalidOperation, ValueError, TypeError):
                        max_income = None

                    gender = row.get("eligibility_gender", "").lower().strip()
                    if gender in ("male", "female", "other"):
                        gender_limit = gender
                    else:
                        gender_limit = ""

                    bpl_required = row.get("eligibility_bpl", "").lower().strip() in ("yes", "true", "1")

                    caste = row.get("eligibility_caste", "").lower().strip()
                    if caste == "null" or caste == "all":
                        caste_categories = ""
                    else:
                        caste_categories = caste

                    if len(caste_categories) > 255:
                        caste_categories = caste_categories[:255]

                    # Official link logic
                    official_link = row.get("official_url") or row.get("apply_url") or ""
                    official_link = official_link.strip()
                    if official_link and not (official_link.startswith("http://") or official_link.startswith("https://")):
                        if "." in official_link:
                            official_link = "https://" + official_link
                        else:
                            official_link = ""

                    if len(official_link) > 200:
                        official_link = official_link[:200]

                    defaults = {
                        "category": category,
                        "department": department,
                        "description": row.get("description", "").strip() or row.get("eligibility_text", "").strip(),
                        "benefits": row.get("benefits", "").strip(),
                        "eligibility_criteria": row.get("eligibility_text", "").strip() or row.get("description", "").strip(),
                        "required_documents": row.get("documents_required", "").strip(),
                        "how_to_apply": row.get("application_process", "").strip(),
                        "official_link": official_link,
                        "min_age": min_age,
                        "max_age": max_age,
                        "gender_limit": gender_limit,
                        "max_income": max_income,
                        "bpl_required": bpl_required,
                        "caste_categories": caste_categories,
                        "is_active": True,
                    }

                    scheme, was_created = Scheme.objects.get_or_create(
                        name=name,
                        state=state,
                        defaults=defaults,
                    )

                    if was_created:
                        created += 1
                    else:
                        for key, val in defaults.items():
                            setattr(scheme, key, val)
                        scheme.save()
                        updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed: {created} schemes created, {updated} schemes updated in the database."
            )
        )