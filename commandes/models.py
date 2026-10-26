import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from panier.models import Panier
from produits.models import Produit

logger = logging.getLogger(__name__)


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
    cgv_acceptees_le = models.DateTimeField("CGV acceptées le", null=True, blank=True)

    # Livraison
    livreur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livraisons', limit_choices_to={'est_livreur': True},
        verbose_name="livreur",
    )
    date_expedition = models.DateTimeField("date d'expédition", null=True, blank=True)
    date_livraison = models.DateTimeField("date de livraison", null=True, blank=True)

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
        statut_change = ancien is not None and self.statut != ancien

        if statut_change:
            maintenant = timezone.now()
            if self.statut == 'expediee' and not self.date_expedition:
                self.date_expedition = maintenant
            if self.statut == 'livree':
                self.date_livraison = maintenant
                if not self.date_expedition:
                    self.date_expedition = maintenant

        super().save(*args, **kwargs)

        # Passage à « Annulée » : le stock est remis à disposition
        if self.statut == 'annulee' and ancien not in (None, 'annulee'):
            self._remettre_en_stock()
        # Le client est prévenu quand sa commande part et quand elle arrive
        if statut_change and self.statut in ('expediee', 'livree'):
            self._notifier_client()
        self._statut_initial = self.statut

    def _remettre_en_stock(self):
        for ligne in self.lignes.exclude(produit__isnull=True):
            Produit.objects.filter(pk=ligne.produit_id).update(stock=F('stock') + ligne.quantite)

    def _notifier_client(self):
        if self.statut == 'expediee':
            sujet = f"Votre commande {self.reference} est en route"
            corps = "Votre commande vient d'être confiée à notre livreur. Elle sera bientôt chez vous."
        else:
            sujet = f"Votre commande {self.reference} a été livrée"
            corps = "Votre commande vient de vous être remise. Merci pour votre confiance !"
        livreur = ""
        if self.livreur and self.livreur.first_name:
            livreur = f"\nVotre livreur : {self.livreur.first_name}\n"
        message = (
            f"Bonjour {self.utilisateur.first_name},\n\n{corps}\n{livreur}\n"
            f"Référence : {self.reference}\n\nL'équipe Maison Lumière"
        )
        try:
            send_mail(sujet, message, None, [self.utilisateur.email])
        except Exception:
            logger.exception("E-mail de suivi non envoyé pour la commande %s", self.reference)

    @property
    def en_cours(self):
        return self.statut in self.STATUTS_EN_COURS

    @property
    def peut_annuler(self):
        return self.statut == 'en_attente'

    @property
    def est_payee(self):
        return self.paiements.filter(statut='reussi').exists()

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