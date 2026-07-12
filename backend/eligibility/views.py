from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EligibilityCheck
from .serializers import EligibilityCheckSerializer
from .services import check_schemes_for_user


class EligibilityCheckViewSet(viewsets.ModelViewSet):
    """
    /api/eligibility/            GET own check history; admins can pass ?all=1
    /api/eligibility/check/      POST runs eligibility checks against active schemes
    /api/eligibility/report/     GET downloads eligibility check report for user
    """

    serializer_class = EligibilityCheckSerializer
    from common.permissions import IsOwnerOrAdmin
    permission_classes = (IsAuthenticated, IsOwnerOrAdmin)

    def get_queryset(self):
        user = self.request.user
        qs = EligibilityCheck.objects.select_related("user", "scheme")
        is_admin = user.is_staff or getattr(user, "role", None) == "admin"
        if is_admin and self.request.query_params.get("all"):
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["post"])
    def check(self, request):
        results = check_schemes_for_user(request.user, request.data)
        
        # Sort: eligible first, then by confidence desc
        results.sort(key=lambda r: (not r["eligible"], -r["confidence"]))
        
        # Keep all eligible, limit total results to 50 to avoid browser rendering freeze
        eligible_count = sum(1 for r in results if r["eligible"])
        limit = max(50, eligible_count)
        limited_results = results[:limit]
        
        return Response({"results": limited_results}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def report(self, request):
        user = request.user
        results = check_schemes_for_user(user, persist=False, update_profile=False)
        eligible_schemes = [r for r in results if r["eligible"]]
        
        report_lines = [
            "==================================================",
            "              SCHEMEX ELIGIBILITY REPORT",
            "==================================================",
            f"User: {user.username}",
            f"Email: {user.email}",
            f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "--------------------------------------------------",
            f"Found {len(eligible_schemes)} eligible scheme(s) for your profile.",
            "==================================================",
            "",
        ]
        
        for idx, scheme in enumerate(eligible_schemes, 1):
            report_lines.extend([
                f"{idx}. {scheme['name']}",
                f"   Category: {scheme['category'].replace('_', ' ').title()}",
                f"   Match Score: {scheme['match_score']}",
                "   Reasons for Eligibility:"
            ])
            for reason in scheme["reasons"]:
                report_lines.append(f"     - {reason}")
            
            if scheme.get("required_documents"):
                report_lines.append("   Required Documents:")
                for doc in scheme["required_documents"]:
                    report_lines.append(f"     - {doc}")
            report_lines.extend(["", "--------------------------------------------------", ""])
            
        report_text = "\n".join(report_lines)
        response = HttpResponse(report_text, content_type="text/plain; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="SchemeX_Eligibility_Report.txt"'
        return response
