from django.contrib import admin

from . import cinetpay
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'commande', 'fournisseur', 'montant', 'statut', 'date_creation',
    )
    list_filter = ('statut', 'fournisseur')
    search_fields = ('transaction_id', 'commande__reference')
    date_hierarchy = 'date_creation'
    readonly_fields = (
        'commande', 'fournisseur', 'methode', 'operateur', 'telephone', 'montant',
        'statut', 'transaction_id', 'reference_externe', 'date_creation', 'date_paiement',
    )
    actions = ['verifier_cinetpay', 'valider_manuellement']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Vérifier auprès de CinetPay")
    def verifier_cinetpay(self, request, queryset):
        compteur = 0
        for paiement in queryset.filter(fournisseur='cinetpay').exclude(statut__in=('reussi', 'a_rembourser')):
            cinetpay.synchroniser(paiement)
            compteur += 1
        self.message_user(request, f"{compteur} paiement(s) vérifié(s) auprès de CinetPay.")

    @admin.action(description="Valider manuellement (virement, paiement à la livraison...)")
    def valider_manuellement(self, request, queryset):
        valides = 0
        for paiement in queryset.exclude(statut__in=('reussi', 'a_rembourser')):
            if paiement.marquer_reussi():
                valides += 1
        self.message_user(request, f"{valides} paiement(s) validé(s).")