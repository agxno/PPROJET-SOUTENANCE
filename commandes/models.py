from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F

from panier.models import Panier
from produits.models import Produit


class PanierVide(Exception):
    pass


class StockInsuffisant(Exception):
    def __init__(self, problemes):
        super().__init__("Stock insuffisant")
        self.problemes = problemes


class Commande(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    STATUTS_EN_COURS = ('en_attente', 'en_preparation', 'expediee')

    reference = models.CharField(max_length=20, unique=True, null=True, blank=True, editable=False)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='commandes'
    )
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    total = models.DecimalField("total (FCFA)", max_digits=12, decimal_places=0, default=0)

    # Adresse de livraison copiée au moment de la commande (elle ne change plus ensuite)
    livraison_prenom = models.CharField("prénom", max_length=100)
    livraison_nom = models.CharField("nom", max_length=100)
    livraison_adresse = models.CharField("adresse", max_length=255)
    livraison_ville = models.CharField("ville", max_length=100)
    livraison_telephone = models.CharField("téléphone", max_length=20)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        ordering = ['-date_creation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._statut_initial = self.statut if self.pk else None

    def __str__(self):
        return self.reference or f"Commande #{self.pk}"

    def clean(self):
        if self.pk and self._statut_initial == 'annulee' and self.statut != 'annulee':
            raise ValidationError({'statut': "Une commande annulée ne peut pas être rouverte."})

    def save(self, *args, **kwargs):
        ancien = self._statut_initial
        super().save(*args, **kwargs)
        # Passage à « Annulée » : le stock est remis à disposition
        if self.statut == 'annulee' and ancien not in (None, 'annulee'):
            self._remettre_en_stock()
        self._statut_initial = self.statut

    def _remettre_en_stock(self):
        for ligne in self.lignes.exclude(produit__isnull=True):
            Produit.objects.filter(pk=ligne.produit_id).update(stock=F('stock') + ligne.quantite)

    @property
    def en_cours(self):
        return self.statut in self.STATUTS_EN_COURS

    @property
    def peut_annuler(self):
        return self.statut == 'en_attente'

    @classmethod
    def creer_depuis_panier(cls, utilisateur, adresse):
        """Transforme le panier en commande : vérifie le stock, le décompte, vide le panier."""
        with transaction.atomic():
            panier = Panier.objects.select_for_update().filter(utilisateur=utilisateur).first()
            lignes = []
            if panier is not None:
                lignes = [l for l in panier.lignes.select_related('produit') if l.produit.actif]
            if not lignes:
                raise PanierVide()

            # Produits verrouillés pendant la vérification (utile surtout avec MySQL)
            produits = {
                p.pk: p for p in
                Produit.objects.select_for_update().filter(pk__in=[l.produit_id for l in lignes])
            }

            problemes = []
            for ligne in lignes:
                produit = produits[ligne.produit_id]
                if produit.stock < ligne.quantite:
                    problemes.append(
                        f"« {produit.nom} » : stock insuffisant "
                        f"({produit.stock} disponible(s), {ligne.quantite} demandé(s))."
                    )
            if problemes:
                raise StockInsuffisant(problemes)

            commande = cls.objects.create(
                utilisateur=utilisateur,
                livraison_prenom=adresse.prenom,
                livraison_nom=adresse.nom,
                livraison_adresse=adresse.adresse,
                livraison_ville=adresse.ville,
                livraison_telephone=adresse.telephone,
            )

            total = 0
            for ligne in lignes:
                produit = produits[ligne.produit_id]
                prix = produit.prix_actuel
                LigneCommande.objects.create(
                    commande=commande,
                    produit=produit,
                    nom_produit=produit.nom,
                    reference_produit=produit.reference,
                    prix_unitaire=prix,
                    quantite=ligne.quantite,
                )
                Produit.objects.filter(pk=produit.pk).update(stock=F('stock') - ligne.quantite)
                total += prix * ligne.quantite

            commande.total = total
            commande.reference = f"ML-{commande.date_creation:%Y}-{commande.pk:06d}"
            commande.save(update_fields=['total', 'reference'])

            panier.lignes.filter(pk__in=[l.pk for l in lignes]).delete()
        return commande


class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(
        Produit, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_commande'
    )
    # Copies figées : la commande reste lisible même si le produit change ou disparaît
    nom_produit = models.CharField("produit", max_length=150)
    reference_produit = models.CharField("référence", max_length=30)
    prix_unitaire = models.DecimalField("prix unitaire (FCFA)", max_digits=10, decimal_places=0)
    quantite = models.PositiveIntegerField("quantité", default=1)

    class Meta:
        verbose_name = "ligne de commande"
        verbose_name_plural = "lignes de commande"

    def __str__(self):
        return f"{self.quantite} x {self.nom_produit}"

    @property
    def sous_total(self):
        return self.prix_unitaire * self.quantite