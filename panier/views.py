from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from produits.models import Produit
from utilisateurs.decorateurs import connexion_requise

from .models import LignePanier, Panier


def _entier(valeur, defaut=1):
    try:
        return int(valeur)
    except (TypeError, ValueError):
        return defaut


@connexion_requise
def voir(request):
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    lignes = list(panier.lignes_actives)
    return render(request, 'panier/panier.html', {
        'lignes': lignes,
        'total': sum(l.sous_total for l in lignes),
        'quantite_totale': sum(l.quantite for l in lignes),
        'probleme_stock': any(not l.disponible for l in lignes),
    })


@require_POST
@connexion_requise
def ajouter(request, produit_id):
    produit = get_object_or_404(Produit.objects.disponibles(), pk=produit_id)

    suivant = request.POST.get('suivant', '')
    if not url_has_allowed_host_and_scheme(
        suivant, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        suivant = produit.get_absolute_url()

    if produit.en_rupture:
        messages.error(request, f"« {produit.nom} » est actuellement épuisé.")
        return redirect(suivant)

    quantite = max(1, _entier(request.POST.get('quantite')))
    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    ligne, _ = LignePanier.objects.get_or_create(
        panier=panier, produit=produit, defaults={'quantite': 0}
    )

    nouvelle = ligne.quantite + quantite
    if nouvelle > produit.stock:
        nouvelle = produit.stock
        messages.warning(
            request, f"Stock limité : {produit.stock} exemplaire(s) disponible(s) pour « {produit.nom} »."
        )
    else:
        messages.success(request, f"« {produit.nom} » a été ajouté à votre panier.")

    ligne.quantite = nouvelle
    ligne.save()
    return redirect(suivant)


@require_POST
@connexion_requise
def modifier(request, ligne_id):
    ligne = get_object_or_404(LignePanier, pk=ligne_id, panier__utilisateur=request.user)
    quantite = _entier(request.POST.get('quantite'), defaut=ligne.quantite)

    if quantite <= 0:
        ligne.delete()
        messages.success(request, "Article retiré du panier.")
    elif ligne.produit.stock <= 0:
        messages.error(request, f"« {ligne.produit.nom} » est épuisé : retirez-le de votre panier.")
    else:
        if quantite > ligne.produit.stock:
            quantite = ligne.produit.stock
            messages.warning(request, f"Stock limité : {quantite} exemplaire(s) disponible(s).")
        else:
            messages.success(request, "Quantité mise à jour.")
        ligne.quantite = quantite
        ligne.save()
    return redirect('panier:voir')


@require_POST
@connexion_requise
def retirer(request, ligne_id):
    ligne = get_object_or_404(LignePanier, pk=ligne_id, panier__utilisateur=request.user)
    ligne.delete()
    messages.success(request, "Article retiré du panier.")
    return redirect('panier:voir')