"""
Tests for the user API.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", response.data)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test error returned if password less than 5 chars."""
        payload = {
            "email": "test@example.com",
            "password": "pw",
            "name": "Test Name"
        }
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(get_user_model().objects.filter(email=payload["email"]).exists())

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": user_details["password"]
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        user_details = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": user_details["password"] + "tcrstdgts"
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        user_details = {
            "email": "test@example.com",
            "password": "testpass123",
            "name": "Test Name"
        }
        create_user(**user_details)
        payload = {
            "email": user_details["email"],
            "password": ""
        }
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("token", response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(email="test@example.com", password="testpass123", name="Test Name")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            "name": self.user.name,
            "email": self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the endpoint."""
        response = self.client.post(ME_URL, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            "name": "Updated Name",
            "password": "newpass123"
        }
        response = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload["name"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
