import logging
import uuid

from django.db import models, transaction
from django.utils import timezone

from commandes.models import Commande

logger = logging.getLogger(__name__)


class Paiement(models.Model):
    METHODES = [
        ('en_ligne', 'Paiement en ligne'),
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
        ('a_verifier', 'À vérifier'),
        ('a_rembourser', 'À rembourser'),
    ]
    # Les deux derniers prestataires ne servent plus : on garde leur nom
    # pour que les anciens paiements de test restent lisibles.
    FOURNISSEURS = [
        ('cinetpay', 'CinetPay'),
        ('simulation', 'Simulation (ancien)'),
        ('kadev', 'Kadev Pay (ancien)'),
    ]

    commande = models.ForeignKey(Commande, on_delete=models.PROTECT, related_name='paiements')
    fournisseur = models.CharField(max_length=20, choices=FOURNISSEURS, default='cinetpay')
    methode = models.CharField("moyen de paiement", max_length=20, choices=METHODES)
    operateur = models.CharField("opérateur", max_length=20, choices=OPERATEURS, blank=True)
    telephone = models.CharField("téléphone", max_length=20, blank=True)
    montant = models.DecimalField("montant (FCFA)", max_digits=12, decimal_places=0)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    transaction_id = models.CharField(max_length=40, unique=True, editable=False)
    reference_externe = models.CharField(
        "référence du prestataire", max_length=60, unique=True, null=True, blank=True,
        help_text="Référence chez un ancien prestataire (non utilisée par CinetPay).",
    )
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
        Renvoie False si l'argent est reçu mais que la commande n'est plus payable
        (annulée ou déjà payée) : le paiement passe alors « À rembourser »."""
        with transaction.atomic():
            paiement = Paiement.objects.select_for_update().get(pk=self.pk)
            if paiement.statut == 'reussi':
                self.statut = 'reussi'
                return True

            commande = Commande.objects.select_for_update().get(pk=paiement.commande_id)
            doublon = commande.paiements.filter(statut='reussi').exclude(pk=paiement.pk).exists()
            if commande.statut == 'annulee' or doublon:
                paiement.statut = 'a_rembourser'
                paiement.save(update_fields=['statut'])
                self.statut = 'a_rembourser'
                logger.error(
                    "Paiement %s reçu pour la commande %s (annulée ou déjà payée) : à rembourser.",
                    paiement.transaction_id, commande.reference,
                )
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

    def signaler_a_verifier(self):
        """Paiement suspect : à contrôler à la main."""
        if self.statut in ('en_attente', 'echoue'):
            self.statut = 'a_verifier'
            self.save(update_fields=['statut'])