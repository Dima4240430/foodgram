from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    GetShortLink,
    IngredientsViewSet,
    RecipeViewSet,
    TagsViewSet,
    UsersViewSet,
)

app_name = 'api'
router = DefaultRouter()

router.register(r'users', UsersViewSet, basename='users')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'ingredients', IngredientsViewSet, basename="ingredients")
router.register(r'recipes', RecipeViewSet, basename="recipes")

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('recipes/<int:recipe_id>/get-link/', GetShortLink.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
