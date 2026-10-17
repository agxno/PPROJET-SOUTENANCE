import json
import logging
import re

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from commandes.models import Commande
from utilisateurs.decorateurs import connexion_requise

from . import kadev
from .forms import MethodeForm, PaiementForm
from .models import Paiement

logger = logging.getLogger(__name__)


def _payer_kadev(request, commande, form):
    if not (settings.KADEV_PUBLIC_KEY and settings.KADEV_SECRET_KEY and settings.KADEV_WEBHOOK_SECRET):
        logger.error("Kadev Pay mal configuré : clés manquantes dans le fichier .env.")
        messages.error(
            request,
            "Le paiement en ligne n'est pas encore configuré. Contactez-nous pour régler votre commande.",
        )
        return redirect('commandes:detail', reference=commande.reference)

    # Les tentatives précédentes sont closes (un paiement tardif reste reconnu par son identifiant)
    commande.paiements.filter(statut='en_attente').update(statut='echoue')
    paiement = Paiement.objects.create(
        commande=commande,
        fournisseur='kadev',
        methode=form.cleaned_data['methode'],
        montant=commande.total,
    )
    return redirect('paiements:kadev', transaction_id=paiement.transaction_id)


@connexion_requise
def payer(request, reference):
    commande = get_object_or_404(Commande, reference=reference, utilisateur=request.user)

    if commande.paiements.filter(statut='reussi').exists():
        messages.info(request, "Cette commande est déjà payée.")
        return redirect('commandes:detail', reference=commande.reference)
    if commande.statut != 'en_attente':
        messages.error(request, "Cette commande ne peut plus être payée.")
        return redirect('commandes:detail', reference=commande.reference)

    kadev_actif = settings.PAIEMENTS_FOURNISSEUR == 'kadev'

    if kadev_actif:
        form = MethodeForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            return _payer_kadev(request, commande, form)
    else:
        form = PaiementForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            if not settings.PAIEMENTS_SIMULATION:
                messages.error(
                    request,
                    "Le paiement en ligne n'est pas encore disponible. Contactez-nous pour régler votre commande.",
                )
                return redirect('commandes:detail', reference=commande.reference)

            commande.paiements.filter(statut='en_attente').update(statut='echoue')
            paiement = Paiement.objects.create(
                commande=commande,
                fournisseur='simulation',
                methode=form.cleaned_data['methode'],
                operateur=form.cleaned_data['operateur'],
                telephone=form.cleaned_data['telephone'],
                montant=commande.total,
            )
            return redirect('paiements:simulation', transaction_id=paiement.transaction_id)

    return render(request, 'paiements/payer.html', {
        'commande': commande,
        'form': form,
        'kadev_actif': kadev_actif,
        'mode_test': kadev_actif and settings.KADEV_MODE_TEST,
        'simulation': settings.PAIEMENTS_SIMULATION,
    })


# ---------- Kadev Pay ----------

def _paiement_kadev(request, transaction_id):
    return get_object_or_404(
        Paiement.objects.select_related('commande'),
        transaction_id=transaction_id,
        commande__utilisateur=request.user,
        fournisseur='kadev',
    )


@connexion_requise
def kadev_checkout(request, transaction_id):
    """Page qui ouvre la fenêtre de paiement Kadev Pay."""
    paiement = _paiement_kadev(request, transaction_id)
    if paiement.statut != 'en_attente':
        return redirect('paiements:retour', transaction_id=paiement.transaction_id)

    commande = paiement.commande
    config = {
        'public_key': settings.KADEV_PUBLIC_KEY,
        'amount': int(paiement.montant),
        'email': request.user.email,
        'name': f"{commande.livraison_prenom} {commande.livraison_nom}",
        'phone': re.sub(r'\D', '', commande.livraison_telephone),
        'method': 'momo' if paiement.methode == 'mobile_money' else 'card',
        'metadata': {'paiement': paiement.transaction_id, 'commande': commande.reference},
        'confirm_url': reverse('paiements:kadev_confirmer', args=[paiement.transaction_id]),
        'retour_url': reverse('paiements:retour', args=[paiement.transaction_id]),
        'csrf': get_token(request),
    }
    return render(request, 'paiements/kadev_checkout.html', {
        'paiement': paiement, 'commande': commande, 'config': config,
    })


@require_POST
@connexion_requise
def kadev_confirmer(request, transaction_id):
    """Reçoit la référence Kadev du navigateur. Prise en compte uniquement en mode test
    (fausse monnaie) ; en production, seul le webhook signé valide un paiement."""
    paiement = _paiement_kadev(request, transaction_id)
    if settings.KADEV_MODE_TEST:
        try:
            reference = json.loads(request.body).get('reference')
        except (ValueError, AttributeError):
            reference = None
        if isinstance(reference, str) and 0 < len(reference) <= 60 and kadev.lier_reference(paiement, reference):
            kadev.synchroniser(paiement)
    return JsonResponse({'ok': True})


@connexion_requise
def retour(request, transaction_id):
    """Page où le client revient après la fenêtre de paiement."""
    paiement = _paiement_kadev(request, transaction_id)
    commande = paiement.commande

    if settings.KADEV_MODE_TEST:
        resultat = kadev.synchroniser(paiement)
    else:
        resultat = kadev.etat(paiement)

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


@csrf_exempt
@require_POST
def webhook_kadev(request):
    """Notification serveur à serveur de Kadev Pay, authentifiée par sa signature."""
    signature = request.META.get('HTTP_X_KADEVPAY_SIGNATURE', '')
    if not kadev.signature_valide(request.body, signature):
        return HttpResponse("Signature invalide.", status=401)

    try:
        evenement = json.loads(request.body)
    except ValueError:
        return HttpResponse("Contenu invalide.", status=400)

    if not isinstance(evenement, dict) or evenement.get('event') != 'payment.success':
        return HttpResponse("Événement ignoré.")

    donnees = evenement.get('data') or {}
    paiement = kadev.trouver_paiement(donnees)
    if paiement is None:
        logger.error(
            "Webhook Kadev Pay reçu sans paiement correspondant : %s",
            json.dumps(evenement, ensure_ascii=False)[:2000],
        )
        return HttpResponse("Paiement introuvable.")

    kadev.appliquer(paiement, donnees)
    return HttpResponse("Webhook traité avec succès.")


# ---------- Simulation (démonstration locale, mode DEBUG uniquement) ----------

def _charger_paiement(request, transaction_id):
    if not settings.PAIEMENTS_SIMULATION:
        raise Http404
    return get_object_or_404(
        Paiement.objects.select_related('commande'),
        transaction_id=transaction_id,
        commande__utilisateur=request.user,
        fournisseur='simulation',
    )


@connexion_requise
def simulation(request, transaction_id):
    paiement = _charger_paiement(request, transaction_id)
    if paiement.statut != 'en_attente':
        return redirect('commandes:detail', reference=paiement.commande.reference)
    return render(request, 'paiements/simulation.html', {'paiement': paiement})


@require_POST
@connexion_requise
def simulation_resultat(request, transaction_id):
    paiement = _charger_paiement(request, transaction_id)
    commande = paiement.commande
    if paiement.statut != 'en_attente':
        return redirect('commandes:detail', reference=commande.reference)

    if request.POST.get('resultat') == 'reussi':
        if paiement.marquer_reussi():
            messages.success(request, "Paiement reçu. Merci pour votre commande !")
            return redirect('commandes:confirmation', reference=commande.reference)
        messages.error(request, "Cette commande a été annulée : le paiement n'a pas été pris en compte.")
        return redirect('commandes:detail', reference=commande.reference)

    paiement.marquer_echoue()
    messages.error(request, "Le paiement a échoué. Vous pouvez réessayer.")
    return redirect('paiements:payer', reference=commande.reference)