from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationFlowTests(TestCase):
    def test_register_creates_user_logs_in_and_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newuser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertTrue(get_user_model().objects.filter(username="newuser").exists())
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            get_user_model().objects.get(username="newuser").id,
        )

    def test_login_redirects_to_dashboard(self):
        get_user_model().objects.create_user(username="existing", password="StrongPass123!")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": "existing", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("dashboard:home"))

    def test_invalid_login_shows_clean_error(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "missing", "password": "wrong"},
        )

        self.assertContains(response, "The username or password you entered is incorrect.")

    def test_anonymous_login_page_does_not_render_sidebar(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertNotContains(response, 'class="sidebar"')
        self.assertContains(response, 'class="auth-card"')

    def test_authenticated_dashboard_renders_sidebar(self):
        get_user_model().objects.create_user(username="existing", password="StrongPass123!")
        self.client.login(username="existing", password="StrongPass123!")

        response = self.client.get(reverse("dashboard:home"))

        self.assertContains(response, 'class="sidebar"')
