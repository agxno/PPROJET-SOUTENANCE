from django.conf import settings
from django.db import models


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favoris'
    )
    produit = models.ForeignKey('produits.Produit', on_delete=models.CASCADE, related_name='favoris')
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "favori"
        verbose_name_plural = "favoris"
        ordering = ['-date_ajout']
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'produit'], name='un_favori_par_produit_et_client'
            ),
        ]

    def __str__(self):
        return f"{self.utilisateur.email} : {self.produit.nom}"