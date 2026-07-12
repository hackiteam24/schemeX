from applications.models import Application
from documents.models import Document
from eligibility.models import EligibilityCheck
from eligibility.services import get_user_eligibility_recommendations
from profiles.services import get_completion_status


def user_is_admin(user):
    return user.is_staff or getattr(user, "role", None) == "admin"


def build_profile_tasks(completion):
    labels = {
        "personal": "Personal Information",
        "contact": "Contact Details",
        "economic": "Economic Info",
        "bank": "Bank Details",
        "documents": "Upload Documents",
    }
    return [
        {"name": labels[key], "completed": completed}
        for key, completed in completion["sections"].items()
    ]


def build_activity_feed(applications, documents, eligibility_checks):
    activities = []

    for app in applications.order_by("-updated_at")[:4]:
        activities.append(
            {
                "icon": "file-signature",
                "title": app.scheme.name,
                "description": f"Application is {app.get_status_display().lower()}",
                "time": app.updated_at.isoformat(),
                "status": (
                    "pending"
                    if app.status in (Application.Status.PENDING, Application.Status.UNDER_REVIEW)
                    else "success"
                    if app.status == Application.Status.APPROVED
                    else "rejected"
                ),
                "statusText": app.get_status_display(),
            }
        )

    for doc in documents.order_by("-upload_date")[:4]:
        activities.append(
            {
                "icon": "file-pdf" if doc.file.name.lower().endswith(".pdf") else "file-image",
                "title": doc.get_document_type_display(),
                "description": f"Uploaded and is {doc.get_verification_status_display().lower()}",
                "time": doc.upload_date.isoformat(),
                "status": (
                    "pending"
                    if doc.verification_status == Document.VerificationStatus.PENDING
                    else "success"
                    if doc.verification_status == Document.VerificationStatus.VERIFIED
                    else "rejected"
                ),
                "statusText": doc.get_verification_status_display(),
            }
        )

    latest_check = eligibility_checks.order_by("-checked_date").first()
    if latest_check:
        eligible_count = eligibility_checks.filter(
            eligibility_result=EligibilityCheck.Result.ELIGIBLE
        ).count()
        activities.append(
            {
                "icon": "user-check",
                "title": "Eligibility Check",
                "description": f"Found {eligible_count} eligible scheme(s)",
                "time": latest_check.checked_date.isoformat(),
                "status": "success",
                "statusText": "Completed",
            }
        )

    return sorted(activities, key=lambda item: item["time"], reverse=True)[:4]


def build_missing_document_tasks(user):
    user_docs = list(Document.objects.filter(uploaded_by=user))
    uploaded_names = {
        doc.get_document_type_display().lower()
        for doc in user_docs
    }
    uploaded_file_names = {
        doc.file.name.rsplit("/", 1)[-1].lower()
        for doc in user_docs
        if doc.file
    }

    missing = []
    for application in Application.objects.filter(applicant=user).select_related("scheme"):
        for required_doc in application.scheme.required_documents_list:
            required_lower = required_doc.lower()
            already_uploaded = any(required_lower in name for name in uploaded_names | uploaded_file_names)
            if not already_uploaded:
                missing.append(
                    {
                        "scheme": application.scheme.name,
                        "task": f"Upload {required_doc}",
                        "days": "Pending",
                        "urgency": "warning",
                    }
                )

    return missing[:5]


def get_dashboard_data(user):
    is_admin = user_is_admin(user)

    if is_admin:
        # Admin dashboard counts
        total_apps = Application.objects.count()
        pending_count = Application.objects.filter(
            status__in=(Application.Status.PENDING, Application.Status.UNDER_REVIEW)
        ).count()
        approved_count = Application.objects.filter(status=Application.Status.APPROVED).count()
        
        # Admin activity feed (latest across all users)
        activities = []
        for app in Application.objects.select_related("scheme", "applicant").order_by("-updated_at")[:4]:
            activities.append({
                "icon": "file-signature",
                "title": f"{app.applicant.username} - {app.scheme.name}",
                "description": f"Application is {app.get_status_display().lower()}",
                "time": app.updated_at.isoformat(),
                "status": (
                    "pending"
                    if app.status in (Application.Status.PENDING, Application.Status.UNDER_REVIEW)
                    else "success"
                    if app.status == Application.Status.APPROVED
                    else "rejected"
                ),
                "statusText": app.get_status_display(),
            })

        for doc in Document.objects.select_related("uploaded_by").order_by("-upload_date")[:4]:
            activities.append({
                "icon": "file-pdf" if doc.file.name.lower().endswith(".pdf") else "file-image",
                "title": f"{doc.uploaded_by.username} - {doc.get_document_type_display()}",
                "description": f"Uploaded and is {doc.get_verification_status_display().lower()}",
                "time": doc.upload_date.isoformat(),
                "status": (
                    "pending"
                    if doc.verification_status == Document.VerificationStatus.PENDING
                    else "success"
                    if doc.verification_status == Document.VerificationStatus.VERIFIED
                    else "rejected"
                ),
                "statusText": doc.get_verification_status_display(),
            })

        activities = sorted(activities, key=lambda item: item["time"], reverse=True)[:4]

        return {
            "first_name": user.first_name or user.username,
            "stats": [
                0,  # No recommendations for admin
                total_apps,
                pending_count,
                approved_count,
            ],
            "profile_completion": {
                "percentage": 100,
                "remaining_count": 0,
                "tasks": [],
            },
            "recommended_schemes": [],
            "activities": activities,
            "deadlines": [],
        }

    # Citizen dashboard logic
    applications = Application.objects.filter(applicant=user).select_related("scheme")
    documents = Document.objects.filter(uploaded_by=user)
    eligibility_checks = EligibilityCheck.objects.filter(user=user).select_related("scheme")

    recommended = get_user_eligibility_recommendations(user, limit=3)
    profile = getattr(user, "profile", None)
    completion = (
        get_completion_status(user, profile)
        if profile
        else {
            "percentage": 0,
            "remaining_count": 5,
            "sections": {
                "personal": False,
                "contact": False,
                "economic": False,
                "bank": False,
                "documents": False,
            },
        }
    )

    app_count = applications.count()
    pending_count = applications.filter(
        status__in=(Application.Status.PENDING, Application.Status.UNDER_REVIEW)
    ).count()
    approved_count = applications.filter(status=Application.Status.APPROVED).count()

    return {
        "first_name": user.first_name or user.username,
        "stats": [
            len(recommended),
            app_count,
            pending_count,
            approved_count,
        ],
        "profile_completion": {
            "percentage": completion["percentage"],
            "remaining_count": completion["remaining_count"],
            "tasks": build_profile_tasks(completion),
        },
        "recommended_schemes": recommended,
        "activities": build_activity_feed(applications, documents, eligibility_checks),
        "deadlines": build_missing_document_tasks(user),
    }
