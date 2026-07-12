from django.test import TestCase
from django.urls import reverse


class SchemeDetailTemplateTests(TestCase):
    def test_scheme_detail_page_does_not_render_official_portal_button(self):
        response = self.client.get(
            reverse("scheme_detail", kwargs={"pk": "11111111-1111-1111-1111-111111111111"})
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Official Portal")
