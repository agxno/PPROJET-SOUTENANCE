from django.contrib import admin

from .models import Favori


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'produit', 'date_ajout')
    search_fields = ('utilisateur__email', 'produit__nom')
    date_hierarchy = 'date_ajout'
    readonly_fields = ('utilisateur', 'produit', 'date_ajout')

    def has_add_permission(self, request):
        return False