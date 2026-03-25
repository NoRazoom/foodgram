from django_filters import rest_framework as filter

from . import models


class RecipeFilter(filter.FilterSet):
    is_favorited = filter.BooleanFilter(method='f_is_favorited',
                                        field_name='is_favorited')
    is_in_shopping_cart = filter.BooleanFilter(
        method='f_is_in_shopping_cart',
        field_name='is_in_shopping_cart')
    author = filter.NumberFilter(field_name='author__id')
    tags = filter.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=models.Tag.objects.all(),
        to_field_name='slug')

    class Meta:
        model = models.Recipe
        fields = ['is_favorited', 'is_in_shopping_cart',
                  'author', 'tags']

    def f_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            saved, _ = models.Saved.objects.get_or_create(
                user=self.request.user)
            favorite_ids = saved.recipes.values_list('id', flat=True)
            # id__in - проверка вхождения в список
            return queryset.filter(id__in=favorite_ids)
        return queryset

    def f_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            shop, _ = models.Purchase.objects.get_or_create(
                user=self.request.user)
            shop_ids = shop.recipes.values_list('id', flat=True)
            return queryset.filter(id__in=shop_ids)
        return queryset
