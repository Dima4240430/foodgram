from django.contrib.auth import get_user_model
from django.http import HttpResponse, Http404
from djoser.views import UserViewSet
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS,
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter, get_short_url
from .pagination import CustomPagination
from .permissions import IsOwnerAdminOrReadOnly
from .serializers import (
    CreateUserSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeSerializer,
    RecipeWriteSerializer,
    RecipesShortSerializer,
    ShortLinkSerialiser,
    SubscribedSerislizer,
    SubscriptionsSerializer,
    TagSerializer,
    UserAvatarSerialiser
)
from recipes.models import (
    Favourite,
    Ingredient,
    IngredientInRecipe,
    Link,
    Recipe,
    ShoppingCart,
    Tag
)
from user.models import Subscribe

User = get_user_model()


class UsersViewSet(UserViewSet):

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    permission_classes = (IsOwnerAdminOrReadOnly,)
    lookup_field = 'id'

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsOwnerAdminOrReadOnly,)
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'subscribe':
            return SubscribedSerislizer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=["get"],
        permission_classes=(AllowAny,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscribe.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionsSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionsSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
        url_name='subscribe'
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(
            User,
            id=id
        )
        change__status = Subscribe.objects.filter(
            user=user.id, author=author.id)
        serializer = SubscribedSerislizer(
            data={'user': user.id, 'author': author.id},
            context={'request': request})

        if request.method == 'POST':
            if user == author:
                return Response(
                    'Вы пытаетесь подписаться на себя!!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if change__status.exists():
                return Response(
                    f'Вы уже подписаны на {author}',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.is_valid()
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if change__status.exists():
            change__status.delete()
            return Response(
                f'Вы отписались от {author}',
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            f'Вы не подписаны на {author}',
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['GET', 'PUT'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
        url_name='avatar'
    )
    def apply_avatar(self, request):
        serializer = UserAvatarSerialiser(
            self.request.user, data=request.data)
        if request.method == 'PUT':
            if serializer.is_valid() and 'avatar' in request.data:
                serializer.save()
                return Response(
                    serializer.data,
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        elif request.method == 'GET':
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @apply_avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientsViewSet(ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    fields = ['^name']


class TagsViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsOwnerAdminOrReadOnly,)


class GetShortLink(APIView):
    repmission_classes = (AllowAny,)

    def get(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        short_url = get_short_url()
        link_obj, _ = Link.objects.get_or_create(
            recipe=recipe,
            defaults={'base_link': recipe.get_absolute_url(),
                      'short_link': short_url}
        )
        serializer = ShortLinkSerialiser(link_obj)
        return Response(serializer.data)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerAdminOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def general_method(self, request, pk, model):
        # управление подписками и списком покупок
        user = request.user
        if request.method == 'POST':
            try:
                recipe = get_object_or_404(Recipe, id=pk)
            except Http404:
                return Response(
                    'Рецепт не найден',
                    status=status.HTTP_404_NOT_FOUND
                )

            if model.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': f'"{recipe.name}" уже добавлен в корзину.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(
                user=user,
                recipe=recipe
            )
            serializer = RecipesShortSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        if request.method == 'DELETE':
            try:
                recipe = get_object_or_404(
                    Recipe,
                    id=pk
                )
            except Http404:
                return Response(
                    'Такого рецепта не существует',
                    status=status.HTTP_404_NOT_FOUND
                )
            obj = model.objects.filter(
                user=user,
                recipe=recipe
            )
            if obj.exists():
                obj.delete()
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'errors': f'В избранном нет рецепта \"{recipe.name}\"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        return self.general_method(request, pk, ShoppingCart)

    @staticmethod
    def ingredients_to_txt(ingredients):
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f" ({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(sum=Sum('amount'))
        shopping_list = self.ingredients_to_txt(ingredients)
        return HttpResponse(shopping_list, content_type='text/plain')

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=[IsAuthenticated],
            url_path='favorite',
            url_name='favorite',)
    def favorite(self, request, pk):
        return self.general_method(request, pk, Favourite)
