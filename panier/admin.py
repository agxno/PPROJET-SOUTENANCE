from django.contrib import admin

from .models import LignePanier, Panier


class LignePanierInline(admin.TabularInline):
    model = LignePanier
    extra = 0
    can_delete = False
    readonly_fields = ('produit', 'quantite', 'date_ajout')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'quantite_totale', 'date_modification')
    search_fields = ('utilisateur__email',)
    inlines = [LignePanierInline]