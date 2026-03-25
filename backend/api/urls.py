from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


app_name = 'api'

api_v1_router = DefaultRouter()
api_v1_router.register(
    r'recipes',
    views.RecipeViewSet,
    basename='recipes'
)
api_v1_router.register(
    r'tags',
    views.TagViewSet,
    basename='tags'
)
api_v1_router.register(
    r'users',
    views.UserViewSet,
    basename='users'
)
api_v1_router.register(
    r'ingredients',
    views.IngredientViewSet,
    basename='ingredients'
)

urlpatterns = [
    path('', include(api_v1_router.urls)),
    # path('', include('djoser.urls')),
    # path('favorites/', views.FavoriteRecipesListView.as_view(), name='favorite'),
    path('auth/', include('djoser.urls.authtoken')),
]
