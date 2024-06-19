"""
Serializers for recipe API.
"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""

    class Meta:
        model = Recipe
        exclude = ["user", "description"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Serializer for recipe detail view."""

    class Meta:
        model = Recipe
        exclude = ["user"]
        read_only_fields = ["id"]
