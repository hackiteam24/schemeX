from django.test import TestCase
from django.urls import reverse


class ApplicationFormTemplateTests(TestCase):
    def test_application_page_includes_selected_scheme_field(self):
        response = self.client.get(
            reverse("application_form"),
            {"scheme": "11111111-1111-1111-1111-111111111111"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="selectedSchemeId"')

# Create your tests here.
