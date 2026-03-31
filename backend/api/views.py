from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.core.exceptions import ValidationError

from . import serializers, models
from .filters import RecipeFilter
from .paginators import FollowPageNumberPagination, NoPagination
from user.models import Follow
import logging

logger = logging.getLogger(__name__)


User = get_user_model()


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Вьюсет рецепта.

    Переопределяет методы создания и обновления.
    """

    queryset = models.Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset_class.request = self.request
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return serializers.RecipeCreateSerializer
        return serializers.RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        recipe = create_serializer.save()

        read_serializer = serializers.RecipeReadSerializer(
            recipe,
            context={'request': request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        update_serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=kwargs.pop('partial', False))
        update_serializer.is_valid(raise_exception=True)
        updated_recipe = update_serializer.save()

        read_serializer = serializers.RecipeReadSerializer(
            updated_recipe,
            context={'request': request}
        )
        return Response(read_serializer.data)

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny],
        url_name='get-link',
        url_path='get-link',
    )
    def get_link(self, request, pk):
        """Action для получения короткой ссылки"""
        recipe = self.get_object()

        short_url = f"{request.build_absolute_uri('/')}s/{recipe.id}/"
        return Response(
            {"short-link": short_url}
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_name='shopping_cart',
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk):
        """Action для добавления и удаления товаров из корзины"""
        recipe = get_object_or_404(models.Recipe, id=pk)
        purchase, created = models.Purchase.objects.get_or_create(
            user=request.user
        )
        if request.method == 'POST':
            if recipe in purchase.recipes.all():
                return Response({'error': 'Рецепт уже добавлен в корзину'},
                                status=status.HTTP_400_BAD_REQUEST)
            purchase.recipes.add(recipe)
            serializer = serializers.RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not purchase.recipes.filter(id=recipe.pk).exists():
                return Response({'error': 'Рецепта в корзине нет'},
                                status=status.HTTP_400_BAD_REQUEST)
            purchase.recipes.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthenticated],
            url_name='download_shopping_cart',
            url_path='download_shopping_cart',)
    def download_shopping_cart(self, request):
        """Action для скачивания корзины с товарами"""
        response = HttpResponse(content_type='text/plain')
        filename = f'shopping_list_{request.user.username}.txt'
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"'
        )

        purchase, created = models.Purchase.objects.get_or_create(
            user=request.user
        )
        ingredients_dict = dict()
        for recipe in purchase.recipes.all():
            recipe_ingredients = recipe.recipe_ingredient.all()
            for ingredient in recipe_ingredients:
                key = f"{ingredient.ingredient.name}"
                measurement_unit = ingredient.ingredient.measurement_unit
                if key in ingredients_dict:
                    ingredients_dict[key]['amount'] += ingredient.amount
                else:
                    ingredients_dict[key] = {
                        'name': ingredient.ingredient.name,
                        'amount': ingredient.amount,
                        'measurement_unit': measurement_unit
                    }

        response.write('СПИСОК ПОКУПОК\n')
        response.write('=' * 50 + '\n\n')

        for ingr in ingredients_dict.values():
            response.write(f'• {ingr["name"]}: {ingr["amount"]}')
            response.write(f' {ingr["measurement_unit"]}\n')
        return response

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated],
            url_name='favorite',
            url_path='favorite',)
    def favorite(self, request, pk):
        """Action для добавления и удаления рецептов из избранного"""
        recipe = get_object_or_404(models.Recipe, id=pk)
        favourited, created = models.Saved.objects.get_or_create(
            user=request.user
        )
        if request.method == 'POST':
            if recipe in favourited.recipes.all():
                return Response({'error': 'Рецепт уже в избранном!'},
                                status=status.HTTP_400_BAD_REQUEST)
            favourited.recipes.add(recipe)
            serializer = serializers.RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            if not favourited.recipes.filter(id=recipe.pk).exists():
                return Response({'error': 'Рецепта в избранном нет'},
                                status=status.HTTP_400_BAD_REQUEST)
            favourited.recipes.remove(recipe)
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для тегов без пагинации"""

    serializer_class = serializers.TagSerializer
    queryset = models.Tag.objects.all()
    http_method_names = ('get',)
    pagination_class = NoPagination


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для ингрибиентов без пагинации"""

    serializer_class = serializers.IngredientSerializer
    queryset = models.Ingredient.objects.all()
    http_method_names = ('get',)
    pagination_class = NoPagination


class UserViewSet(DjoserUserViewSet):
    """Вьюсет пользователей"""

    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        if self.action in ('list', 'retrieve'):
            return User.objects.all()
        if self.action == 'me' and self.request.user.is_authenticated:
            return User.objects.filter(id=self.request.user.id)
        raise NotAuthenticated()

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_name='me',
    )
    def me(self, request, *args, **kwargs):
        """Данные о себе"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['put', 'delete'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request, *args, **kwargs):
        """Action для добавления и удаления аватара"""
        instance = request.user

        if request.method == 'PUT':
            serializer = serializers.AvatarSerializer(instance,
                                                      data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == 'DELETE':
            if instance.avatar:
                instance.avatar.delete()
                instance.avatar = None
                instance.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        """Action для добавления и удаления пользователя из подписок"""
        person = get_object_or_404(User, pk=id)
        subscribes, created = Follow.objects.get_or_create(
            follower=request.user
        )
        if request.method == 'POST':
            if subscribes.following.filter(id=id).exists():
                return Response({'error': 'Пользователь уже у вас в друзьях!'})
            subscribes.following.add(person)
            serializer = serializers.FollowSerializer(
                person,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            if not subscribes.following.filter(id=id).exists():
                return Response({'error': 'Пользователь нет у вас в друзьях!'})
            subscribes.following.remove(person)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Action для получения своих подписок"""
        logger.error("method subscriptions")
        logger.error(f"Query params: {request.query_params}")
        recipes_limit = request.query_params.get('recipes_limit')
        logger.error(f"recipes_limit: {recipes_limit}")
        subs = Follow.objects.filter(follower=request.user)
        users = []
        for follow in subs:
            following_users = follow.following.all()
            users.extend(following_users)
        users = list(set(users))

        paginator = FollowPageNumberPagination()

        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                raise ValidationError

        context = {'request': request, 'recipes_limit': recipes_limit}
        page = paginator.paginate_queryset(users, request)
        if page is not None:
            serializer = serializers.FollowSerializer(
                page,
                many=True,
                context=context
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = serializers.FollowSerializer(
            users,
            many=True,
            context=context
        )

        return Response(serializer.data)


def redirect_to_recipe(request, recipe_id):
    """Редирект с короткой ссылки на полный URL рецепта"""
    recipe = get_object_or_404(models.Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe.id}/')
