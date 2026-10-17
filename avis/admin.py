from django.contrib import admin

from .models import Avis


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('produit', 'utilisateur', 'etoiles_liste', 'extrait', 'date_creation', 'statut')
    list_editable = ('statut',)
    list_filter = ('statut', 'note', 'produit__categorie')
    search_fields = ('produit__nom', 'utilisateur__email', 'titre', 'commentaire')
    date_hierarchy = 'date_creation'
    ordering = ('statut', '-date_creation')  # les avis « En attente » en premier
    readonly_fields = ('produit', 'utilisateur', 'commande', 'note', 'date_creation')
    actions = ['approuver', 'masquer']

    def has_add_permission(self, request):
        return False

    @admin.display(description="note")
    def etoiles_liste(self, obj):
        return obj.etoiles

    @admin.display(description="avis")
    def extrait(self, obj):
        texte = f"{obj.titre} : {obj.commentaire}"
        return texte if len(texte) <= 70 else texte[:67] + "..."

    @admin.action(description="Approuver (publier)")
    def approuver(self, request, queryset):
        compteur = queryset.update(statut='publie')
        self.message_user(request, f"{compteur} avis publié(s).")

    @admin.action(description="Masquer")
    def masquer(self, request, queryset):
        compteur = queryset.update(statut='masque')
        self.message_user(request, f"{compteur} avis masqué(s).")