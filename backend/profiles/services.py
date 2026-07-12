PROFILE_COMPLETION_SECTIONS = {
    "personal": ("first_name", "last_name", "gender", "date_of_birth", "category", "marital_status"),
    "contact": ("email", "phone_number"),
    "economic": ("annual_income", "income_source", "bpl_status", "occupation"),
    "bank": ("bank_name", "account_number", "ifsc_code", "account_type"),
}


def has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def get_field_value(user, profile, field):
    if hasattr(user, field):
        return getattr(user, field)
    return getattr(profile, field)


def get_completion_status(user, profile):
    """Calculate profile completion from real account/profile/document data."""
    sections = {}

    for section, fields in PROFILE_COMPLETION_SECTIONS.items():
        sections[section] = all(has_value(get_field_value(user, profile, field)) for field in fields)

    sections["documents"] = user.documents.exists()

    completed_count = sum(1 for completed in sections.values() if completed)
    total_count = len(sections)

    return {
        "sections": sections,
        "percentage": int((completed_count / total_count) * 100) if total_count else 0,
        "remaining_count": total_count - completed_count,
    }
