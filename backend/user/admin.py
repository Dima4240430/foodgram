from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Subscribe, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar',
        'role',)
    list_editable = ('role',)
    search_fields = ('username', 'email')
    list_filter = ()
    list_display_links = ('username',)
    empty_value_display = 'Не задано'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author',)
    list_editable = ('author',)
    search_fields = ('user', 'author')
    list_filter = ()
    list_display_links = ('user',)
    empty_value_display = 'Не задано'
