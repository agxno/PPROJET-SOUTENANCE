from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Adresse, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'telephone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),
    )


@admin.register(Adresse)
class AdresseAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'prenom', 'nom', 'ville', 'par_defaut')
    list_filter = ('par_defaut',)
    search_fields = ('utilisateur__email', 'nom', 'ville')