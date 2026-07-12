from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from schemes.models import Scheme
from eligibility.models import EligibilityCheck

User = get_user_model()


class EligibilityReportTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="citizen",
            email="citizen@schemex.gov.in",
            password="citizenpassword"
        )
        self.client.force_authenticate(user=self.user)

        # Create active schemes: one eligible (state=all), one ineligible (state=assam)
        self.eligible_scheme = Scheme.objects.create(
            name="Eligible Scheme",
            description="You qualify for this.",
            is_active=True,
            state="all"
        )
        self.ineligible_scheme = Scheme.objects.create(
            name="Ineligible Scheme",
            description="You don't qualify.",
            is_active=True,
            state="assam"
        )

    def test_download_eligibility_report(self):
        # 1. Run eligibility check (user defaults state to empty, so only 'all' matches)
        check_url = reverse("eligibility-check")
        response = self.client.post(check_url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Call download report
        report_url = reverse("eligibility-report")
        report_response = self.client.get(report_url)
        self.assertEqual(report_response.status_code, status.HTTP_200_OK)
        self.assertEqual(report_response["Content-Type"], "text/plain; charset=utf-8")

        # 3. Verify report content only contains eligible schemes
        content = report_response.content.decode("utf-8")
        self.assertIn("Eligible Scheme", content)
        self.assertNotIn("Ineligible Scheme", content)
