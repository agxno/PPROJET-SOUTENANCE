from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from commandes.models import Commande
from utilisateurs.decorateurs import connexion_requise

from .forms import PaiementForm
from .models import Paiement


@connexion_requise
def payer(request, reference):
    commande = get_object_or_404(Commande, reference=reference, utilisateur=request.user)

    if commande.paiements.filter(statut='reussi').exists():
        messages.info(request, "Cette commande est déjà payée.")
        return redirect('commandes:detail', reference=commande.reference)
    if commande.statut != 'en_attente':
        messages.error(request, "Cette commande ne peut plus être payée.")
        return redirect('commandes:detail', reference=commande.reference)

    form = PaiementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if not settings.PAIEMENTS_SIMULATION:
            messages.error(
                request,
                "Le paiement en ligne n'est pas encore disponible. Contactez-nous pour régler votre commande.",
            )
            return redirect('commandes:detail', reference=commande.reference)

        # Les tentatives précédentes restées ouvertes sont closes
        commande.paiements.filter(statut='en_attente').update(statut='echoue')
        paiement = Paiement.objects.create(
            commande=commande,
            methode=form.cleaned_data['methode'],
            operateur=form.cleaned_data['operateur'],
            telephone=form.cleaned_data['telephone'],
            montant=commande.total,
        )
        return redirect('paiements:simulation', transaction_id=paiement.transaction_id)

    return render(request, 'paiements/payer.html', {
        'commande': commande,
        'form': form,
        'simulation': settings.PAIEMENTS_SIMULATION,
    })


def _charger_paiement(request, transaction_id):
    # Sans simulation (production), ces pages n'existent pas
    if not settings.PAIEMENTS_SIMULATION:
        raise Http404
    return get_object_or_404(
        Paiement.objects.select_related('commande'),
        transaction_id=transaction_id,
        commande__utilisateur=request.user,
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