from django.contrib import admin
from . import models


class UserModelAdmin(admin.ModelAdmin):
    search_fields = ['username', 'email']


admin.site.register(models.User, UserModelAdmin)
admin.site.register(models.Follow)
