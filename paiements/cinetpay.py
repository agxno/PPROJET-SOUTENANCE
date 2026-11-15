import json
import logging
from functools import lru_cache

from django.conf import settings
from django.urls import reverse

from cinetpay import (
    CinetPayClient,
    ClientConfig,
    CountryCredentials,
    PaymentRequest,
    is_final_status,
    parse_notification,
)

logger = logging.getLogger(__name__)

PAYS = "CI"
MONTANT_MIN = 100
MONTANT_MAX = 2_500_000


@lru_cache(maxsize=1)
def _client():
    return CinetPayClient(ClientConfig(
        credentials={
            PAYS: CountryCredentials(
                api_key=settings.CINETPAY_API_KEY_CI,
                api_password=settings.CINETPAY_API_PASSWORD_CI,
            ),
        },
        debug=settings.DEBUG,
    ))


def etat(paiement):
    return 'attente' if paiement.statut == 'en_attente' else paiement.statut


def initialiser(paiement):
    """Crée la transaction chez CinetPay et renvoie l'adresse de sa page de paiement."""
    commande = paiement.commande
    utilisateur = commande.utilisateur
    retour = settings.SITE_URL + reverse('paiements:retour', args=[paiement.transaction_id])
    notification = settings.SITE_URL + reverse('paiements:webhook_cinetpay')

    reponse = _client().payment.initialize(
        PaymentRequest(
            currency="XOF",
            merchant_transaction_id=paiement.transaction_id,
            amount=int(paiement.montant),
            lang="fr",
            designation=f"Commande {commande.reference}",
            client_email=utilisateur.email,
            client_first_name=utilisateur.first_name or commande.livraison_prenom,
            client_last_name=utilisateur.last_name or commande.livraison_nom,
            success_url=retour,
            failed_url=retour,
            notify_url=notification,
            channel="PUSH",
        ),
        PAYS,
    )
    return reponse.payment_url


def lire_notification(corps, post=None):
    try:
        donnees = json.loads(corps)
    except ValueError:
        donnees = dict(post or {})
    return parse_notification(donnees)


def synchroniser(paiement):
    """Demande à CinetPay le vrai statut du paiement et met à jour la commande.
    Renvoie : 'reussi', 'echoue', 'a_verifier', 'a_rembourser' ou 'attente'."""
    if paiement.statut in ('reussi', 'a_rembourser'):
        return paiement.statut

    try:
        reponse = _client().payment.get_status(paiement.transaction_id, PAYS)

        # ─── LOGS DE DEBUG (à retirer en production) ───
        logger.info(
            "[CINETPAY] Réponse brute pour %s : %r",
            paiement.transaction_id, reponse
        )
        logger.info(
            "[CINETPAY] status=%r | code=%r | data=%r",
            getattr(reponse, 'status', None),
            getattr(reponse, 'code', None),
            getattr(reponse, 'data', None),
        )
        # ────────────────────────────────────────────────

        statut = getattr(reponse, 'status', None)
        code = getattr(reponse, 'code', None)

    except Exception:
        logger.exception("Vérification CinetPay impossible pour %s", paiement.transaction_id)
        return etat(paiement)

    # ─── Vérification du succès (multi-format) ───
    # CinetPay renvoie parfois "SUCCESS", parfois "ACCEPTED",
    # parfois code == "00". On accepte tous les cas.
    if statut in ('SUCCESS', 'ACCEPTED', '00') or code == '00':
        logger.info("[CINETPAY] Paiement %s CONFIRMÉ", paiement.transaction_id)
        paiement.marquer_reussi()
    elif statut and is_final_status(statut):
        logger.info("[CINETPAY] Paiement %s ÉCHOUÉ (statut=%s)", paiement.transaction_id, statut)
        paiement.marquer_echoue()
    else:
        logger.info(
            "[CINETPAY] Paiement %s en attente (statut=%s, code=%s)",
            paiement.transaction_id, statut, code
        )

    return etat(paiement)