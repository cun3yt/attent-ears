from bs4 import BeautifulSoup
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.test.client import RequestFactory
from unittest.mock import Mock
from model_mommy import mommy

from .models import User, Client as AttentClient

from .views import index


class VisualizerViewsTest(TestCase):
    def setUp(self):
        self.client = mommy.make(
            AttentClient,
            name='Client Name',
            website='something.com',
            email_domain='something.com',
            extra_info={}
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

        self.factory = RequestFactory()

    def test_home_no_login(self):
        client = Client()

        response = client.get(reverse('index'))
        self.assertEqual(200, response.status_code, "Status Code: Success")
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.title.string, 'Attent')

        links = soup.find_all('a')
        self.assertEqual(len(links), 1, "One Link Only")
        self.assertEqual(links[0].get('href'), "/sociallogin/google-oauth2/", "Link URL")
        self.assertContains(response, "Sign In With Google")

    def test_home_login(self):
        request = self.factory.get(reverse('index'))
        request.user = self.user

        response = index(request)

        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Please Select A Dashboard")
        self.assertContains(response, self.user.first_name, msg_prefix="User's First Name's Existence")
        self.assertContains(response, self.user.last_name, msg_prefix="User's Last Name's Existence")
