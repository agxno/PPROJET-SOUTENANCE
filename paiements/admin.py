from django.contrib import admin

from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'commande', 'methode', 'operateur',
        'montant', 'statut', 'date_creation',
    )
    list_filter = ('statut', 'methode', 'operateur')
    search_fields = ('transaction_id', 'commande__reference', 'telephone')
    date_hierarchy = 'date_creation'
    readonly_fields = (
        'commande', 'methode', 'operateur', 'telephone', 'montant',
        'statut', 'transaction_id', 'date_creation', 'date_paiement',
    )
    actions = ['valider_manuellement']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Valider manuellement (virement, paiement à la livraison...)")
    def valider_manuellement(self, request, queryset):
        valides = 0
        for paiement in queryset.exclude(statut='reussi'):
            if paiement.marquer_reussi():
                valides += 1
        self.message_user(request, f"{valides} paiement(s) validé(s).")