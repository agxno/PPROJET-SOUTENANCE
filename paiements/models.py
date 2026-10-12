import uuid

from django.db import models, transaction
from django.utils import timezone

from commandes.models import Commande


class Paiement(models.Model):
    METHODES = [
        ('mobile_money', 'Mobile money'),
        ('carte', 'Carte bancaire'),
    ]
    OPERATEURS = [
        ('orange', 'Orange Money'),
        ('mtn', 'MTN MoMo'),
        ('moov', 'Moov Money'),
        ('wave', 'Wave'),
    ]
    STATUTS = [
        ('en_attente', 'En attente'),
        ('reussi', 'Réussi'),
        ('echoue', 'Échoué'),
    ]

    commande = models.ForeignKey(Commande, on_delete=models.PROTECT, related_name='paiements')
    methode = models.CharField("moyen de paiement", max_length=20, choices=METHODES)
    operateur = models.CharField("opérateur", max_length=20, choices=OPERATEURS, blank=True)
    telephone = models.CharField("téléphone", max_length=20, blank=True)
    montant = models.DecimalField("montant (FCFA)", max_digits=12, decimal_places=0)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    transaction_id = models.CharField(max_length=40, unique=True, editable=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "paiement"
        verbose_name_plural = "paiements"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.transaction_id} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def marquer_reussi(self):
        """Valide le paiement et passe la commande en préparation.
        Renvoie False si la commande a été annulée entre-temps."""
        with transaction.atomic():
            paiement = Paiement.objects.select_for_update().get(pk=self.pk)
            if paiement.statut == 'reussi':
                self.statut = 'reussi'
                return True

            commande = Commande.objects.select_for_update().get(pk=paiement.commande_id)
            if commande.statut == 'annulee':
                paiement.statut = 'echoue'
                paiement.save(update_fields=['statut'])
                self.statut = 'echoue'
                return False

            paiement.statut = 'reussi'
            paiement.date_paiement = timezone.now()
            paiement.save(update_fields=['statut', 'date_paiement'])
            if commande.statut == 'en_attente':
                commande.statut = 'en_preparation'
                commande.save()

            self.statut = 'reussi'
            self.date_paiement = paiement.date_paiement
        return True

    def marquer_echoue(self):
        if self.statut == 'en_attente':
            self.statut = 'echoue'
            self.save(update_fields=['statut'])