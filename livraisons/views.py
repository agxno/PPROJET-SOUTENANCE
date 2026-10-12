from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from commandes.models import Commande

from .decorateurs import livreur_requis

A_LIVRER = ('en_preparation', 'expediee')


def _mes_commandes(request):
    return Commande.objects.filter(livreur=request.user).prefetch_related('lignes')


def _commande(request, reference):
    return get_object_or_404(_mes_commandes(request), reference=reference)


@livreur_requis
def tableau(request):
    commandes = _mes_commandes(request)
    onglet = request.GET.get('onglet', 'a_livrer')
    if onglet == 'livrees':
        liste = commandes.filter(statut='livree').order_by('-date_livraison')
    else:
        onglet = 'a_livrer'
        liste = commandes.filter(statut__in=A_LIVRER).order_by('date_creation')
    return render(request, 'livraisons/tableau.html', {
        'commandes': liste,
        'onglet': onglet,
        'nb_a_livrer': commandes.filter(statut__in=A_LIVRER).count(),
        'nb_livrees': commandes.filter(statut='livree').count(),
    })


@livreur_requis
def detail(request, reference):
    return render(request, 'livraisons/detail.html', {'commande': _commande(request, reference)})


@require_POST
@livreur_requis
def changer_statut(request, reference):
    commande = _commande(request, reference)
    action = request.POST.get('action')

    if not commande.est_payee:
        messages.error(
            request,
            "Le paiement de cette commande n'est pas confirmé. Contactez l'administration avant de livrer.",
        )
    elif action == 'en_route' and commande.statut == 'en_preparation':
        commande.statut = 'expediee'
        commande.save()
        messages.success(request, "Bonne route ! Le client a été prévenu.")
    elif action == 'livree' and commande.statut == 'expediee':
        commande.statut = 'livree'
        commande.save()
        messages.success(request, "Livraison enregistrée. Merci !")
    else:
        messages.error(request, "Cette action n'est pas possible pour cette commande.")
    return redirect('livraisons:detail', reference=commande.reference)