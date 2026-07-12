from datetime import date
from decimal import Decimal, InvalidOperation

from schemes.models import Scheme

from .models import EligibilityCheck


def calculate_age(date_of_birth):
    if not date_of_birth:
        return None
    today = date.today()
    return today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )


def normalize_text(value):
    return str(value or "").strip().lower()


def parse_decimal(value, default=None):
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def answers_from_profile(profile):
    return {
        "age": calculate_age(profile.date_of_birth),
        "gender": profile.gender,
        "category": profile.category,
        "state": profile.state,
        "annualIncome": profile.annual_income,
        "bplStatus": profile.bpl_status,
        "ownsLand": profile.owns_land,
        "landArea": profile.land_area,
    }


def normalize_answers(data):
    age_raw = data.get("age")
    age = None
    if age_raw not in (None, ""):
        try:
            age = int(float(age_raw))
        except (ValueError, TypeError):
            age = None

    return {
        "age": age,
        "gender": normalize_text(data.get("gender")),
        "category": normalize_text(data.get("category")),
        "state": normalize_text(data.get("state")),
        "annual_income": parse_decimal(data.get("annualIncome")),
        "bpl_status": normalize_text(data.get("bplStatus")),
        "owns_land": normalize_text(data.get("ownsLand")),
        "land_area": parse_decimal(data.get("landArea"), Decimal("0")),
        "land_type": normalize_text(data.get("landType")),
        "marital_status": normalize_text(data.get("maritalStatus")),
        "district": normalize_text(data.get("district")),
        "pincode": normalize_text(data.get("pincode")),
        "occupation": normalize_text(data.get("occupation")),
        "income_source": normalize_text(data.get("incomeSource")),
    }


def update_profile_from_answers(profile, answers):
    if not profile:
        return

    field_map = {
        "gender": "gender",
        "category": "category",
        "state": "state",
        "annual_income": "annual_income",
        "bpl_status": "bpl_status",
        "owns_land": "owns_land",
        "land_area": "land_area",
        "land_type": "land_type",
        "marital_status": "marital_status",
        "district": "district",
        "pincode": "pincode",
        "occupation": "occupation",
        "income_source": "income_source",
    }

    changed_fields = []
    for source, target in field_map.items():
        value = answers.get(source)
        if value not in (None, ""):
            setattr(profile, target, value)
            changed_fields.append(target)

    if changed_fields:
        profile.save(update_fields=changed_fields + ["updated_at"])


def evaluate_scheme(scheme, answers):
    eligible = True
    reasons = []
    checks = 0
    matched = 0

    age = answers.get("age")
    gender = normalize_text(answers.get("gender"))
    category = normalize_text(answers.get("category"))
    state = normalize_text(answers.get("state"))
    annual_income = answers.get("annual_income")
    bpl_status = normalize_text(answers.get("bpl_status"))
    owns_land = normalize_text(answers.get("owns_land"))
    land_area = parse_decimal(answers.get("land_area"), Decimal("0"))

    if scheme.state and scheme.state.lower() != "all":
        checks += 1
        if state and scheme.state.lower() == state:
            matched += 1
            reasons.append(f"State residency matches ({state.upper()})")
        else:
            eligible = False
            reasons.append(f"Scheme is restricted to {scheme.state.upper()} state residents")

    if scheme.min_age is not None:
        checks += 1
        if age is not None and age >= scheme.min_age:
            matched += 1
            reasons.append(f"Age criteria met (minimum {scheme.min_age})")
        else:
            eligible = False
            reasons.append(f"Minimum age required is {scheme.min_age} years")

    if scheme.max_age is not None:
        checks += 1
        if age is not None and age <= scheme.max_age:
            matched += 1
            reasons.append(f"Age criteria met (maximum {scheme.max_age})")
        else:
            eligible = False
            reasons.append(f"Maximum age allowed is {scheme.max_age} years")

    if scheme.gender_limit:
        checks += 1
        if gender and scheme.gender_limit.lower() == gender:
            matched += 1
            reasons.append(f"Gender criteria met ({gender.capitalize()})")
        else:
            eligible = False
            reasons.append(f"Only available to {scheme.gender_limit} applicants")

    if scheme.max_income is not None:
        checks += 1
        if annual_income is not None and annual_income <= scheme.max_income:
            matched += 1
            reasons.append(f"Family income is within the Rs. {int(scheme.max_income):,} limit")
        else:
            eligible = False
            reasons.append(f"Family income exceeds the Rs. {int(scheme.max_income):,} ceiling")

    if scheme.bpl_required:
        checks += 1
        if bpl_status == "yes":
            matched += 1
            reasons.append("BPL criteria met")
        else:
            eligible = False
            reasons.append("Requires active BPL card holder status")

    if scheme.land_required:
        checks += 1
        if owns_land == "yes" and land_area > 0:
            matched += 1
            reasons.append(f"Land criteria met ({land_area} acres owned)")
        else:
            eligible = False
            reasons.append("Requires ownership of agricultural land")

    if scheme.caste_categories:
        checks += 1
        eligible_castes = [c.strip().lower() for c in scheme.caste_categories.split(",") if c.strip()]
        if category and category in eligible_castes:
            matched += 1
            reasons.append(f"Caste category criteria met ({category.upper()})")
        else:
            eligible = False
            reasons.append(f"Restricted to caste categories: {scheme.caste_categories.upper()}")

    confidence = int((matched / checks) * 100) if checks else 100
    if not eligible:
        confidence = min(confidence, 49)

    return {
        "eligible": eligible,
        "confidence": confidence,
        "reasons": reasons or ["No restrictive eligibility rules are configured for this scheme."],
    }


def serialize_result(scheme, evaluation):
    return {
        "id": str(scheme.id),
        "name": scheme.name,
        "name_hi": scheme.name,
        "category": scheme.category,
        "eligible": evaluation["eligible"],
        "confidence": evaluation["confidence"],
        "match_score": f"{evaluation['confidence']}% match",
        "reasons": evaluation["reasons"],
        "required_documents": scheme.required_documents_list,
    }


def check_schemes_for_user(user, raw_answers=None, persist=True, update_profile=True):
    profile = getattr(user, "profile", None)
    raw_answers = raw_answers or (answers_from_profile(profile) if profile else {})
    answers = normalize_answers(raw_answers)

    if update_profile:
        update_profile_from_answers(profile, answers)

    schemes = Scheme.objects.filter(is_active=True)
    state = answers.get("state")
    if state:
        from django.db.models import Q
        schemes = schemes.filter(Q(state__iexact="all") | Q(state__iexact=state))
    else:
        schemes = schemes.filter(state__iexact="all")

    results = []
    to_create = []

    for scheme in schemes:
        evaluation = evaluate_scheme(scheme, answers)
        results.append(serialize_result(scheme, evaluation))

        if persist:
            to_create.append(
                EligibilityCheck(
                    user=user,
                    scheme=scheme,
                    eligibility_result=(
                        EligibilityCheck.Result.ELIGIBLE
                        if evaluation["eligible"]
                        else EligibilityCheck.Result.NOT_ELIGIBLE
                    ),
                    reason="; ".join(evaluation["reasons"]),
                )
            )

    if persist and to_create:
        from django.db import transaction
        with transaction.atomic():
            EligibilityCheck.objects.filter(user=user).delete()
            EligibilityCheck.objects.bulk_create(to_create)

    return results


def get_user_eligibility_recommendations(user, limit=None):
    if not getattr(user, "is_authenticated", False) or not hasattr(user, "profile"):
        return []
    results = check_schemes_for_user(user, persist=False, update_profile=False)
    eligible = [result for result in results if result["eligible"]]
    eligible.sort(key=lambda item: item["confidence"], reverse=True)
    return eligible[:limit] if limit else eligible
