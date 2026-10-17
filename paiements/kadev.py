import hashlib
import hmac
import json
import logging
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

from django.conf import settings

from .models import Paiement

logger = logging.getLogger(__name__)

URL_VERIFICATION = "https://pay.kadev.ci/api/v1/transactions/verify/"
STATUTS_ECHEC = {'failed', 'cancelled', 'canceled', 'abandoned', 'expired'}


def signature_valide(corps, signature):
    """Vérifie la signature HMAC-SHA512 du webhook avec le Secret Webhook."""
    if not settings.KADEV_WEBHOOK_SECRET or not signature:
        return False
    attendue = hmac.new(
        settings.KADEV_WEBHOOK_SECRET.encode('utf-8'), corps, hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(attendue, signature.strip().lower())


def verifier(reference):
    """Interroge l'API Kadev Pay (appel serveur, clé secrète) et renvoie les données."""
    requete = urllib.request.Request(
        URL_VERIFICATION + urllib.parse.quote(reference, safe=''),
        headers={
            'Authorization': f'Bearer {settings.KADEV_SECRET_KEY}',
            'Accept': 'application/json',
            'User-Agent': 'MaisonLumiere/1.0',
        },
    )
    with urllib.request.urlopen(requete, timeout=15) as reponse:
        corps = json.loads(reponse.read().decode('utf-8'))
    if not isinstance(corps, dict):
        return {}
    donnees = corps.get('data')
    return donnees if isinstance(donnees, dict) else corps


def etat(paiement):
    return 'attente' if paiement.statut == 'en_attente' else paiement.statut


def _montant(valeur):
    try:
        return Decimal(str(valeur))
    except (InvalidOperation, TypeError):
        return None


def _metadata(donnees):
    brut = donnees.get('metadata') or {}
    if isinstance(brut, str):
        try:
            brut = json.loads(brut)
        except ValueError:
            brut = {}
    return brut if isinstance(brut, dict) else {}


def trouver_paiement(donnees):
    """Retrouve notre paiement : d'abord par les métadonnées envoyées à l'ouverture, puis par la référence Kadev."""
    paiements = Paiement.objects.select_related('commande').filter(fournisseur='kadev')
    identifiant = _metadata(donnees).get('paiement')
    if identifiant:
        paiement = paiements.filter(transaction_id=identifiant).first()
        if paiement:
            return paiement
    reference = donnees.get('reference')
    if reference:
        return paiements.filter(reference_externe=reference).first()
    return None


def lier_reference(paiement, reference):
    """Associe la référence Kadev au paiement. Une référence ne peut servir qu'une seule fois."""
    if not reference or paiement.reference_externe == reference:
        return True
    if Paiement.objects.filter(reference_externe=reference).exclude(pk=paiement.pk).exists():
        return False
    paiement.reference_externe = reference
    paiement.save(update_fields=['reference_externe'])
    return True


def appliquer(paiement, donnees):
    """Met à jour le paiement d'après les données Kadev.
    Renvoie : 'reussi', 'echoue', 'a_verifier', 'a_rembourser' ou 'attente'."""
    if paiement.statut in ('reussi', 'a_rembourser'):
        return paiement.statut

    statut = str(donnees.get('status', '')).lower()
    reference = str(donnees.get('reference') or '')

    if statut == 'paid':
        montant = _montant(donnees.get('amount'))
        if montant is None or montant < paiement.montant:
            logger.error(
                "Paiement %s : montant reçu (%s) inférieur au montant attendu (%s).",
                paiement.transaction_id, donnees.get('amount'), paiement.montant,
            )
            paiement.signaler_a_verifier()
            return etat(paiement)
        if not lier_reference(paiement, reference):
            logger.error(
                "Paiement %s : la référence %s a déjà servi pour un autre paiement.",
                paiement.transaction_id, reference,
            )
            paiement.signaler_a_verifier()
            return etat(paiement)
        paiement.marquer_reussi()
        return etat(paiement)

    if statut in STATUTS_ECHEC:
        paiement.marquer_echoue()
    return etat(paiement)


def synchroniser(paiement):
    """Demande à Kadev Pay le statut de la transaction (si on connaît sa référence)."""
    if not paiement.reference_externe or paiement.statut in ('reussi', 'a_rembourser'):
        return etat(paiement)
    try:
        donnees = verifier(paiement.reference_externe)
    except Exception:
        logger.exception("Vérification Kadev Pay impossible pour %s", paiement.reference_externe)
        return etat(paiement)
    donnees.setdefault('reference', paiement.reference_externe)
    return appliquer(paiement, donnees)