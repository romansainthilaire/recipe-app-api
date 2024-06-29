"""Tests for ingredient API."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving ingredients."""
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name="Kale")
        Ingredient.objects.create(user=self.user, name="Vanilla")
        response = self.client.get(INGREDIENTS_URL)
        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(user=user2, name="Salt")
        ingredient = Ingredient.objects.create(user=self.user, name="Pepper")
        response = self.client.get(INGREDIENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], ingredient.name)
        self.assertEqual(response.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Cilantro")
        payload = {"name": "Coriander"}
        url = detail_url(ingredient.id)
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name="Lettuce")
        url = detail_url(ingredient.id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(user=self.user).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Apples")
        ingredient2 = Ingredient.objects.create(user=self.user, name="Basil")
        ingredient3 = Ingredient.objects.create(user=self.user, name="Turkey")
        recipe1 = Recipe.objects.create(
            title="Apple Crumble",
            time_minutes=5,
            price=Decimal("4.50"),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title="Pesto Sauce",
            time_minutes=15,
            price=Decimal("3.50"),
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)
        serializer3 = IngredientSerializer(ingredient3)
        self.assertIn(serializer1.data, response.data)
        self.assertIn(serializer2.data, response.data)
        self.assertNotIn(serializer3.data, response.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients returns a unique list."""
        ingredient = Ingredient.objects.create(user=self.user, name="Eggs")
        Ingredient.objects.create(user=self.user, name="Lentils")
        recipe1 = Recipe.objects.create(
            title="Eggs Benedict",
            time_minutes=60,
            price=Decimal("7.00"),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title="Herb Eggs",
            time_minutes=20,
            price=Decimal("4.00"),
            user=self.user
        )
        recipe1.ingredients.add(ingredient)
        recipe2.ingredients.add(ingredient)
        response = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})
        self.assertEqual(len(response.data), 1)
