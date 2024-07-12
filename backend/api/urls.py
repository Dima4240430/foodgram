from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    GetShortLink,
    IngredientsViewSet,
    RecipeViewSet,
    TagsViewSet,
    UserViewSet,
)

app_name = 'api'
router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('tags', TagsViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename="ingredients")
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:recipe_id>/get-link/', GetShortLink.as_view()),
    path('', include(router.urls)),
]
