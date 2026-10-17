from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from produits.models import Produit

from .forms import AvisForm
from .models import Avis
from .services import commande_livree


@login_required
def laisser(request, slug):
    produit = get_object_or_404(Produit.objects.disponibles(), slug=slug)

    if Avis.objects.filter(produit=produit, utilisateur=request.user).exists():
        messages.info(request, "Vous avez déjà donné votre avis sur ce produit. Merci !")
        return redirect(produit)

    commande = commande_livree(request.user, produit)
    if commande is None:
        messages.info(request, "Vous pourrez donner votre avis une fois cet article livré.")
        return redirect(produit)

    form = AvisForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        avis = form.save(commit=False)
        avis.produit = produit
        avis.utilisateur = request.user
        avis.commande = commande
        try:
            avis.save()
        except IntegrityError:
            messages.info(request, "Vous avez déjà donné votre avis sur ce produit. Merci !")
        else:
            messages.success(request, "Merci ! Votre avis sera publié après modération.")
        return redirect(produit)

    return render(request, 'avis/formulaire.html', {
        'produit': produit,
        'commande': commande,
        'form': form,
    })