from bs4 import BeautifulSoup
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.test.client import RequestFactory
from unittest.mock import Mock
from model_mommy import mommy

from .models import User, Client as AttentClient, PeriscopeDashboard

from .views import index


class VisualizerViewsTest(TestCase):
    def setUp(self):
        self.client = mommy.make(
            AttentClient,
            name='Client Name',
            website='something.com',
            email_domain='something.com',
            extra_info={
                "periscope_api_key": "xyz"
            }
            # dashboard__name='adsf' # Inanc's suggestion: one shot all relations
        )

        self.user = mommy.make(
            User,
            first_name='Some',
            last_name='Thing',
            email='some@something.com',
            is_staff=False,
            is_active=True,
            client=self.client
        )

        self.periscope_dashboard_visible_1 = mommy.make(
            PeriscopeDashboard,
            periscope_dashboard_id=1,
            dashboard_name='Dashboard Visible 1',
            is_visible=True,
            client=self.client
        )

        self.periscope_dashboard_visible_2 = mommy.make(
            PeriscopeDashboard,
            periscope_dashboard_id=12,
            dashboard_name='Dashboard Visible 2',
            is_visible=True,
            client=self.client
        )

        self.periscope_dashboard_invisible = mommy.make(
            PeriscopeDashboard,
            periscope_dashboard_id=123,
            dashboard_name='Dashboard Invisible',
            is_visible=False,
            client=self.client
        )

        self.url = reverse('index')
        self.factory = RequestFactory()

    def test_home_no_login(self):
        client = Client()

        response = client.get(self.url)
        self.assertEqual(200, response.status_code, "Status Code: Success")
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.title.string, 'Attent')

        links = soup.find_all('a')
        self.assertEqual(len(links), 1, "One Link Only")
        self.assertEqual(links[0].get('href'), "/sociallogin/google-oauth2/", "Link URL")
        self.assertContains(response, "Sign In With Google")

    def test_home_login_no_dashboard_selection(self):
        request = self.factory.get(self.url)
        request.user = self.user

        response = index(request)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please Select A Dashboard")
        self.assertContains(response, self.user.first_name, msg_prefix="User's First Name's Existence")
        self.assertContains(response, self.user.last_name, msg_prefix="User's Last Name's Existence")
        self.assertContains(response, self.periscope_dashboard_visible_1.dashboard_name)
        self.assertContains(response, self.periscope_dashboard_visible_2.dashboard_name)
        self.assertNotContains(response, self.periscope_dashboard_invisible.dashboard_name)

    def test_home_login_dashboard_selection(self):
        request = self.factory.get(self.url)
        request.user = self.user
        request.GET = {
            'dashboard_id': '1'
        }

        response = index(request)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'iframe')
        self.assertNotContains(response, "Please Select A Dashboard")
        self.assertContains(response, self.user.first_name, msg_prefix="User's First Name's Existence")
        self.assertContains(response, self.user.last_name, msg_prefix="User's Last Name's Existence")
        self.assertContains(response, self.periscope_dashboard_visible_1.dashboard_name)
        self.assertContains(response, self.periscope_dashboard_visible_2.dashboard_name)
        self.assertNotContains(response, self.periscope_dashboard_invisible.dashboard_name)

        soup = BeautifulSoup(response.content, 'html.parser')
        active_link_set = soup.find_all('a', class_="item active")
        self.assertEqual(len(active_link_set), 1, "One Active Link")
        self.assertEqual(active_link_set[0].string.strip(), 'Dashboard Visible 1')


class PeriscopeDashboardModelTest(TestCase):
    pass
