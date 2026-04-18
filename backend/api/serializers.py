from rest_framework import serializers
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField

from recipe import models


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Пользователя.

    Добавляет поле подписки текущего пользователя на указанного.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar')

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.follower.filter(following=obj).exists()
        return False


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватарки"""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete(save=False)
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class RegistrationSerializer(UserCreateSerializer):
    """Сериализатор регистрации юзеров"""

    password = serializers.CharField(write_only=True, required=True)
    id = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class TagSerializer(serializers.ModelSerializer):
    """Cериализатор Тэга"""

    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингриедеинта"""

    class Meta:
        model = models.Ingredient
        fields = '__all__'


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор промежуточной таблицы рецепт-ингредиент для создания"""

    id = serializers.IntegerField()

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания Рецепта.

    Свзязывает атрибут ингридиетов с сериализатором промежуточной таблицы
    рецепт-ингридиент, а так же атрибут тэгов с таблицей тэгов
    через простую промежуточную таблицу.
    Поле автор 'прячется'.
    """

    ingredients = RecipeIngredientCreateSerializer(many=True,
                                                   required=False,
                                                   write_only=True)
    #  подставляем текущего пользователя
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=models.Tag.objects.all(),
        required=False
    )
    image = Base64ImageField()

    class Meta:
        model = models.Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time', 'author')

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])

        recipe = models.Recipe.objects.create(**validated_data)
        if tags:
            recipe.tags.set(tags)

        for ingredient in ingredients:
            if models.Ingredient.objects.filter(
                    id=ingredient.get('id')).exists():
                models.RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=models.Ingredient.objects.get(
                        id=ingredient.get('id')),
                    amount=ingredient.get('amount')
                )
            else:
                raise serializers.ValidationError(
                    'Такого ингредиента не существут!:(')

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])

        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        instance.save()

        if tags:
            instance.tags.set(tags)

        if ingredients:
            instance.recipe_ingredient.all().delete()
            for ingredient in ingredients:
                if models.Ingredient.objects.filter(
                        id=ingredient.get('id')).exists():
                    models.RecipeIngredient.objects.create(
                        recipe=instance,
                        ingredient=models.Ingredient.objects.get(
                            id=ingredient.get('id')),
                        amount=ingredient.get('amount')
                    )
                else:
                    raise serializers.ValidationError(
                        'Такого ингредиента не существут!:(')

        return instance


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор чтения промежуточной таблицы рецепт-ингридиент"""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Рецепта для чтения.

    Добавляет поля, отображающие взаимодействия пользователя с рецептом:
    - находится ли рецепт в избранном
    - находится ли рецепт в списке покупок.
    """

    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(many=True,
                                                 source='recipe_ingredient')

    class Meta:
        model = models.Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'owner'):
                return request.user.owner.recipes.filter(id=obj.id).exists()
            return False
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if hasattr(request.user, 'customer'):
                return request.user.customer.recipes.filter(id=obj.id).exists()
            return False
        return False


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта, упрощенный"""

    image = Base64ImageField()

    class Meta:
        model = models.Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписок"""

    email = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name',
            'is_subscribed', 'recipes',
            'recipes_count', 'avatar'
        )

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')

        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"get_recipes for {obj.username}")
        logger.error(f"recipes_limit from context: {recipes_limit}")
        logger.error(f"recipes_limit type: {type(recipes_limit)}")

        recipes = obj.recipes.all()
        if recipes_limit is not None:
            try:
                limit = int(recipes_limit)
                recipes = recipes[:limit]
            except (TypeError, ValueError):
                pass
        serializer = RecipeShortSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return request.user.follower.filter(following=obj).exists()

    def get_avatar(self, obj):
        # есть ли атрибут ссылки
        if obj.avatar and hasattr(obj.avatar, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
