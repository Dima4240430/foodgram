from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favourite, Ingredient, IngredientInRecipe, Link,
                            Recipe, ShoppingCart, Tag)
from user.models import Subscribe, User

from .filters import IngredientFilter, RecipeFilter, get_short_url
from .pagination import CustomPagination
from .permissions import IsAdminOrReadOnly, IsOwnerAdminOrReadOnly
from .serializers import (CustomUserSerializer, IngredientSerializer,
                          RecipeSerializer, RecipesShortSerializer,
                          RecipeWriteSerializer, ShortLinkSerialiser,
                          SubscribedSerislizer, SubscriptionsSerializer,
                          TagSerializer, UserAvatarSerialiser)


class UserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination
    permission_classes = (IsAdminOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated,)
        return super().get_permissions()

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
        change_subscription_status = Subscribe.objects.filter(
            user=user.id,
            author=author.id
        )
        serializer = SubscribedSerislizer(
            data={'user': user.id, 'author': author.id},
            context={'request': request}
        )

        if request.method == 'POST':
            if user == author:
                return Response(
                    'Вы пытаетесь подписаться на себя!!',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if change_subscription_status.exists():
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
        if change_subscription_status.exists():
            change_subscription_status.delete()
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
        url_path="me/avatar",
        methods=["put", "delete"],
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request, *args, **kwargs):
        if request.method == "DELETE":
            request.user.avatar = None
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if 'avatar' not in request.data:
            return Response(
                {"detail": "Поле 'avatar' должно быть заполнено."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = UserAvatarSerialiser(
            data=request.data,
            instance=request.user
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
    permission_classes = (AllowAny,)

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

    def redirect_to_full_link(request, short_link):
        try:
            link_obj = Link.objects.get(
                short_link="http:/localhost/s/" + short_link
            )
            full_link = link_obj.base_link.replace('/api', '', 1)
            return redirect(full_link)
        except Link.DoesNotExist:
            return HttpResponse(
                'Ссылка не найдена', status=status.HTTP_404_NOT_FOUND)


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsOwnerAdminOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.general_method(
            request,
            pk,
            Favourite,
            'В избранном нет рецепта'
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self.general_method(
            request,
            pk,
            ShoppingCart,
            'В списке покупок нет рецепта'
        )

    def general_method(
            self,
            request,
            pk,
            model,
            error_message_get,
            error_message_post
    ):
        user = request.user
        try:
            recipe = get_object_or_404(Recipe, id=pk)
        except Http404:
            return Response(
                'Рецепт не найден',
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'POST':
            if model.objects.filter(
                user=user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': f'{error_message_post} \"{recipe.name}\"'},
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

        elif request.method == 'DELETE':
            obj = model.objects.filter(
                user=user,
                recipe=recipe
            )
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {'errors': f'{error_message_get} \"{recipe.name}\"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @staticmethod
    def ingredients_to_txt(ingredients):
        shopping_list = ''
        for ingredient in ingredients:
            shopping_list += (
                f"{ingredient['ingredient__name']}  - "
                f"{ingredient['sum']}"
                f"({ingredient['ingredient__measurement_unit']})\n"
            )
        return shopping_list

    @action(detail=False, methods=['GET'],
            permission_classes=(IsAuthenticated,),
            url_path='download_shopping_cart',
            url_name='download_shopping_cart',
            )
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["total_amount"]}'
            for ingredient in ingredients
        ])

        filename = f'{user.username}_shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class SubscriptionViewSet(ListAPIView):
    serializer_class = SubscriptionsSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return user.subscriber.all()
