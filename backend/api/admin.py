from django.contrib import admin
from django.db.models import Count

from . import models


class RecipeModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'saved_count']
    search_fields = ['name', 'author__username']
    list_filter = ['tags__id']

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            saved_count=Count('saved')
        )

    def saved_count(self, obj):
        return obj.saved_count

    saved_count.short_description = 'Добавлений в избранное: '


class IngredientModelAdmin(admin.ModelAdmin):
    search_fields = ['name']


admin.site.register(models.Tag)
admin.site.register(models.Ingredient, IngredientModelAdmin)
admin.site.register(models.Recipe, RecipeModelAdmin)
admin.site.register(models.Saved)
admin.site.register(models.Purchase)
