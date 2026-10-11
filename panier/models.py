from django.conf import settings
from django.db import models
from django.db.models import Sum


class Panier(models.Model):
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='panier'
    )
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "panier"
        verbose_name_plural = "paniers"

    def __str__(self):
        return f"Panier de {self.utilisateur}"

    @property
    def lignes_actives(self):
        return self.lignes.filter(produit__actif=True).select_related('produit')

    @property
    def quantite_totale(self):
        return self.lignes.filter(produit__actif=True).aggregate(total=Sum('quantite'))['total'] or 0


class LignePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(
        'produits.Produit', on_delete=models.CASCADE, related_name='lignes_panier'
    )
    quantite = models.PositiveIntegerField(default=1)
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ligne de panier"
        verbose_name_plural = "lignes de panier"
        ordering = ['date_ajout']
        constraints = [
            models.UniqueConstraint(fields=['panier', 'produit'], name='une_ligne_par_produit'),
        ]

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom}"

    @property
    def sous_total(self):
        return self.produit.prix_actuel * self.quantite

    @property
    def disponible(self):
        return 0 < self.quantite <= self.produit.stock