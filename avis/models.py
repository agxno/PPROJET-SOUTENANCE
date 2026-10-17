from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Avis(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('publie', 'Publié'),
        ('masque', 'Masqué'),
    ]

    produit = models.ForeignKey('produits.Produit', on_delete=models.CASCADE, related_name='avis')
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='avis'
    )
    commande = models.ForeignKey(
        'commandes.Commande', on_delete=models.SET_NULL, null=True, blank=True, related_name='avis'
    )
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    titre = models.CharField("titre", max_length=120)
    commentaire = models.TextField(max_length=2000)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avis"
        verbose_name_plural = "avis"
        ordering = ['-date_creation']
        constraints = [
            models.UniqueConstraint(
                fields=['produit', 'utilisateur'], name='un_avis_par_produit_et_client'
            ),
        ]

    def __str__(self):
        return f"{self.produit.nom} : {self.note}/5 par {self.utilisateur.email}"

    @property
    def etoiles(self):
        return "★" * self.note + "☆" * (5 - self.note)

    @property
    def auteur(self):
        prenom = (self.utilisateur.first_name or '').strip()
        nom = (self.utilisateur.last_name or '').strip()
        if prenom and nom:
            return f"{prenom} {nom[0]}."
        return prenom or "Client"