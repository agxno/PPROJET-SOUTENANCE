from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from panier.models import Panier
from utilisateurs.decorateurs import connexion_requise
from utilisateurs.forms import AdresseForm

from .courriels import envoyer_confirmation
from .models import Commande, PanierVide, StockInsuffisant

FILTRES = {
    'en_cours': Commande.STATUTS_EN_COURS,
    'livrees': ('livree',),
    'annulees': ('annulee',),
}


def _entier(valeur, defaut=0):
    try:
        return int(valeur)
    except (TypeError, ValueError):
        return defaut


def _commande(request, reference):
    return get_object_or_404(
        Commande.objects.prefetch_related('lignes'),
        reference=reference, utilisateur=request.user,
    )


def _page_commande(request, reference, **extra):
    commande = _commande(request, reference)
    contexte = {
        'commande': commande,
        'paiement': commande.paiements.filter(statut='reussi').first(),
    }
    contexte.update(extra)
    return render(request, 'commandes/detail.html', contexte)


@connexion_requise
def valider(request):
    panier = Panier.objects.filter(utilisateur=request.user).first()
    lignes = list(panier.lignes_actives) if panier else []
    if not lignes:
        messages.info(request, "Votre panier est vide.")
        return redirect('panier:voir')

    adresses = list(request.user.adresses.all())
    form = AdresseForm()

    if request.method == 'POST':
        if request.POST.get('action') == 'ajouter_adresse':
            form = AdresseForm(request.POST)
            if form.is_valid():
                adresse = form.save(commit=False)
                adresse.utilisateur = request.user
                adresse.save()
                messages.success(request, "Adresse ajoutée.")
                return redirect('commandes:valider')
        else:
            adresse = request.user.adresses.filter(pk=_entier(request.POST.get('adresse'))).first()
            if adresse is None:
                messages.error(request, "Choisissez une adresse de livraison.")
            elif request.POST.get('accepte_cgv') != 'on':
                messages.error(
                    request, "Vous devez accepter les conditions générales de vente pour commander."
                )
            else:
                try:
                    commande = Commande.creer_depuis_panier(request.user, adresse)
                except PanierVide:
                    messages.info(request, "Votre panier est vide.")
                    return redirect('panier:voir')
                except StockInsuffisant as erreur:
                    for probleme in erreur.problemes:
                        messages.error(request, probleme)
                    return redirect('panier:voir')

                # Preuve de l'acceptation des CGV
                commande.cgv_acceptees_le = timezone.now()
                commande.save(update_fields=['cgv_acceptees_le'])

                try:
                    envoyer_confirmation(request, commande)
                    messages.success(
                        request, f"Un e-mail de confirmation a été envoyé à {request.user.email}."
                    )
                except Exception:
                    messages.warning(request, "Votre commande est enregistrée, mais l'e-mail de confirmation n'a pas pu être envoyé.")
                # Étape suivante : le paiement
                return redirect('paiements:payer', reference=commande.reference)

    return render(request, 'commandes/valider.html', {
        'lignes': lignes,
        'total': sum(l.sous_total for l in lignes),
        'adresses': adresses,
        'form': form,
        'probleme_stock': any(not l.disponible for l in lignes),
    })


@connexion_requise
def liste(request):
    commandes = Commande.objects.filter(utilisateur=request.user)
    filtre = request.GET.get('statut', '')
    if filtre in FILTRES:
        commandes = commandes.filter(statut__in=FILTRES[filtre])
    else:
        filtre = ''
    return render(request, 'commandes/liste.html', {'commandes': commandes, 'filtre': filtre})


@connexion_requise
def detail(request, reference):
    return _page_commande(request, reference)


@connexion_requise
def confirmation(request, reference):
    return _page_commande(request, reference, confirmation=True)


@require_POST
@connexion_requise
def annuler(request, reference):
    commande = _commande(request, reference)
    if commande.peut_annuler:
        commande.statut = 'annulee'
        commande.save()
        messages.success(request, "Votre commande a été annulée.")
    else:
        messages.error(request, "Cette commande ne peut plus être annulée.")
    return redirect('commandes:detail', reference=commande.reference)