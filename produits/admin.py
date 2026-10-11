from django.contrib import admin

from .models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    prepopulated_fields = {'slug': ('nom',)}
    search_fields = ('nom',)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'reference', 'categorie', 'prix', 'prix_promo',
        'stock', 'statut_du_stock', 'actif',
    )
    list_filter = ('categorie', 'actif')
    list_editable = ('stock', 'actif')
    search_fields = ('nom', 'reference')
    exclude = ('slug',)

    @admin.display(description="statut du stock")
    def statut_du_stock(self, obj):
        return {'rupture': 'Rupture', 'faible': 'Stock faible', 'en_stock': 'En stock'}[obj.statut_stock]