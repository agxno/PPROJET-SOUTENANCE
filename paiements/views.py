import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from commandes.models import Commande
from utilisateurs.decorateurs import connexion_requise

from . import cinetpay
from .models import Paiement

logger = logging.getLogger(__name__)


def _cinetpay_configure():
    ok = bool(
        settings.SITE_URL.startswith('https://')
        and settings.CINETPAY_API_KEY_CI
        and settings.CINETPAY_API_PASSWORD_CI
    )
    if not ok:
        logger.warning(
            "CinetPay non configuré : SITE_URL=%r, clé=%r, mot de passe=%r",
            settings.SITE_URL,
            bool(settings.CINETPAY_API_KEY_CI),
            bool(settings.CINETPAY_API_PASSWORD_CI),
        )
    return ok


@connexion_requise
def payer(request, reference):
    commande = get_object_or_404(Commande, reference=reference, utilisateur=request.user)

    if commande.paiements.filter(statut='reussi').exists():
        messages.info(request, "Cette commande est déjà payée.")
        return redirect('commandes:detail', reference=commande.reference)
    if commande.statut != 'en_attente':
        messages.error(request, "Cette commande ne peut plus être payée.")
        return redirect('commandes:detail', reference=commande.reference)

    if request.method == 'POST':
        return _payer_cinetpay(request, commande)

    configure = _cinetpay_configure()
    return render(request, 'paiements/payer.html', {
        'commande': commande,
        'configure': configure,
        'mode_test': settings.CINETPAY_MODE_TEST,
        'debug_site_url': settings.SITE_URL,
        'debug_has_api_key': bool(settings.CINETPAY_API_KEY_CI),
        'debug_has_api_password': bool(settings.CINETPAY_API_PASSWORD_CI),
    })


def _payer_cinetpay(request, commande):
    if not _cinetpay_configure():
        logger.error("CinetPay mal configuré : SITE_URL (https) ou clés API manquantes dans .env.")
        messages.error(
            request,
            "Le paiement en ligne n'est pas encore configuré. Contactez-nous pour régler votre commande.",
        )
        return redirect('commandes:detail', reference=commande.reference)

    if not cinetpay.MONTANT_MIN <= commande.total <= cinetpay.MONTANT_MAX:
        messages.error(
            request,
            "Le montant de cette commande ne permet pas le paiement en ligne "
            "(entre 100 et 2 500 000 FCFA). Contactez-nous pour la régler.",
        )
        return redirect('commandes:detail', reference=commande.reference)

    # On vérifie le vrai statut des tentatives précédentes avant d'en ouvrir une nouvelle
    for ancien in commande.paiements.filter(statut='en_attente', fournisseur='cinetpay'):
        cinetpay.synchroniser(ancien)
    if commande.paiements.filter(statut='reussi').exists():
        messages.success(request, "Votre paiement a bien été reçu.")
        return redirect('commandes:confirmation', reference=commande.reference)
    commande.paiements.filter(statut='en_attente').update(statut='echoue')

    paiement = Paiement.objects.create(
        commande=commande, fournisseur='cinetpay', methode='en_ligne', montant=commande.total,
    )
    try:
        url = cinetpay.initialiser(paiement)
    except Exception as erreur:
        logger.exception("Échec de l'initialisation du paiement CinetPay")
        paiement.marquer_echoue()
        messages.error(
            request, "Le service de paiement est momentanément indisponible. Réessayez dans quelques instants."
        )
        if settings.DEBUG:
            messages.warning(
                request,
                f"Détail technique (visible en mode développement uniquement) : "
                f"{type(erreur).__name__} : {erreur}",
            )
        return redirect('paiements:payer', reference=commande.reference)
    return redirect(url)
    if not _cinetpay_configure():
        logger.error("CinetPay mal configuré : SITE_URL (https) ou clés API manquantes dans .env.")
        messages.error(
            request,
            "Le paiement en ligne n'est pas encore configuré. Contactez-nous pour régler votre commande.",
        )
        return redirect('commandes:detail', reference=commande.reference)

    if not cinetpay.MONTANT_MIN <= commande.total <= cinetpay.MONTANT_MAX:
        messages.error(
            request,
            "Le montant de cette commande ne permet pas le paiement en ligne "
            "(entre 100 et 2 500 000 FCFA). Contactez-nous pour la régler.",
        )
        return redirect('commandes:detail', reference=commande.reference)

    # On vérifie le vrai statut des tentatives précédentes avant d'en ouvrir une nouvelle
    for ancien in commande.paiements.filter(statut='en_attente', fournisseur='cinetpay'):
        cinetpay.synchroniser(ancien)
    if commande.paiements.filter(statut='reussi').exists():
        messages.success(request, "Votre paiement a bien été reçu.")
        return redirect('commandes:confirmation', reference=commande.reference)
    commande.paiements.filter(statut='en_attente').update(statut='echoue')

    paiement = Paiement.objects.create(
        commande=commande, fournisseur='cinetpay', methode='en_ligne', montant=commande.total,
    )
    try:
        url = cinetpay.initialiser(paiement)
    except Exception:
        logger.exception("Échec de l'initialisation du paiement CinetPay")
        paiement.marquer_echoue()
        messages.error(
            request, "Le service de paiement est momentanément indisponible. Réessayez dans quelques instants."
        )
        return redirect('paiements:payer', reference=commande.reference)
    return redirect(url)


@csrf_exempt
@require_POST
def webhook_cinetpay(request):
    """Notification serveur à serveur. Son contenu n'est jamais cru tel quel :
    il sert seulement à savoir quel paiement revérifier directement auprès de CinetPay."""
    try:
        reference = cinetpay.lire_notification(request.body, request.POST).merchant_transaction_id
    except Exception:
        logger.warning("Notification CinetPay illisible : %s", request.body[:1000])
        return HttpResponse(status=400)

    paiement = Paiement.objects.select_related('commande').filter(
        transaction_id=reference, fournisseur='cinetpay'
    ).first()
    if paiement is None:
        return HttpResponse(status=404)

    cinetpay.synchroniser(paiement)
    return HttpResponse("OK")


@connexion_requise
def retour(request, transaction_id):
    """Page où CinetPay renvoie le client : on revérifie le statut côté serveur."""
    paiement = get_object_or_404(
        Paiement.objects.select_related('commande'),
        transaction_id=transaction_id,
        commande__utilisateur=request.user,
        fournisseur='cinetpay',
    )
    commande = paiement.commande
    resultat = cinetpay.synchroniser(paiement)

    if resultat == 'reussi':
        messages.success(request, "Paiement reçu. Merci pour votre commande !")
        return redirect('commandes:confirmation', reference=commande.reference)
    if resultat == 'a_rembourser':
        messages.error(
            request,
            "Votre paiement a bien été reçu, mais votre commande n'est plus valable. "
            "Contactez-nous : nous vous rembourserons.",
        )
        return redirect('commandes:detail', reference=commande.reference)
    if resultat == 'a_verifier':
        messages.warning(
            request,
            "Votre paiement est en cours de vérification. Si votre commande n'est pas confirmée "
            "rapidement, contactez-nous.",
        )
        return redirect('commandes:detail', reference=commande.reference)
    if resultat == 'echoue':
        messages.error(request, "Le paiement n'a pas abouti. Vous pouvez réessayer.")
        return redirect('paiements:payer', reference=commande.reference)
    return render(request, 'paiements/en_cours.html', {'paiement': paiement, 'commande': commande})