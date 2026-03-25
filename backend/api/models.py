from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()

TAG_MAX_LENGTH = 50
INGRIDIENT_MAX_LENGTH = 50
MEASURE_MAX_LENGTH = 40
RECIPE_NAME_MAX_LENGTH = 256


class Tag(models.Model):
    """Модель тега для рецептов"""

    name = models.CharField('Тэг', max_length=TAG_MAX_LENGTH)
    slug = models.SlugField('Слаг', unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингридиента"""

    name = models.CharField('Ингридиент', max_length=INGRIDIENT_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASURE_MAX_LENGTH
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        # указание собственной промежуточной таблицы связи M:N
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient')
    )
    text = models.TextField('Описание')
    name = models.CharField('Рецепт', max_length=RECIPE_NAME_MAX_LENGTH)
    tags = models.ManyToManyField(Tag)
    image = models.ImageField(
        'Картинка',
        upload_to='recipes/',
        blank=True,
        null=True
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
        default_related_name = 'recipe'
        ordering = ['id']

    def __str__(self):
        return self.name


class Saved(models.Model):
    """Сохраненные рецепты пользователя в избранное"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        unique=True
    )
    recipes = models.ManyToManyField(Recipe)


class Purchase(models.Model):
    """Корзина пользователя"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipes = models.ManyToManyField(Recipe, related_name='recipes')


class RecipeIngredient(models.Model):
    """Количество ингридиентов для рецепта"""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
