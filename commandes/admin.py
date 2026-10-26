from django.contrib import admin

from .models import Commande, LigneCommande


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    can_delete = False
    fields = ('nom_produit', 'reference_produit', 'prix_unitaire', 'quantite')
    readonly_fields = ('nom_produit', 'reference_produit', 'prix_unitaire', 'quantite')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'utilisateur', 'date_creation', 'total', 'statut', 'livreur')
    list_editable = ('statut', 'livreur')
    list_filter = ('statut', 'livreur', 'date_creation')
    search_fields = ('reference', 'utilisateur__email', 'livraison_nom', 'livreur__email')
    date_hierarchy = 'date_creation'
    inlines = [LigneCommandeInline]
    readonly_fields = (
        'reference', 'utilisateur', 'total', 'cgv_acceptees_le', 'date_creation', 'date_modification',
        'date_expedition', 'date_livraison',
        'livraison_prenom', 'livraison_nom', 'livraison_adresse',
        'livraison_ville', 'livraison_telephone',
    )
    actions = ['marquer_en_preparation', 'marquer_expediee', 'marquer_livree']

    def has_add_permission(self, request):
        # Les commandes se créent depuis le site, jamais à la main
        return False

    def _changer_statut(self, request, queryset, statut, libelle):
        compteur = 0
        for commande in queryset.exclude(statut='annulee'):
            commande.statut = statut
            commande.save()
            compteur += 1
        self.message_user(request, f"{compteur} commande(s) marquée(s) comme {libelle}.")

    @admin.action(description="Marquer comme en préparation")
    def marquer_en_preparation(self, request, queryset):
        self._changer_statut(request, queryset, 'en_preparation', 'en préparation')

    @admin.action(description="Marquer comme expédiée")
    def marquer_expediee(self, request, queryset):
        self._changer_statut(request, queryset, 'expediee', 'expédiées')

    @admin.action(description="Marquer comme livrée")
    def marquer_livree(self, request, queryset):
        self._changer_statut(request, queryset, 'livree', 'livrées')