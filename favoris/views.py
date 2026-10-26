from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from produits.models import Produit
from utilisateurs.decorateurs import connexion_requise

from .models import Favori


@connexion_requise(message="Connectez-vous pour retrouver vos favoris.")
def liste(request):
    produits = (
        Produit.objects.disponibles()
        .filter(favoris__utilisateur=request.user)
        .select_related('categorie')
        .order_by('-favoris__date_ajout')
    )
    return render(request, 'favoris/liste.html', {'produits': produits})


@require_POST
@connexion_requise(message="Connectez-vous pour enregistrer vos favoris.")
def basculer(request, produit_id):
    produit = get_object_or_404(Produit.objects.disponibles(), pk=produit_id)
    favori, cree = Favori.objects.get_or_create(utilisateur=request.user, produit=produit)
    if cree:
        messages.success(request, f"« {produit.nom} » a été ajouté à vos favoris.")
    else:
        favori.delete()
        messages.success(request, f"« {produit.nom} » a été retiré de vos favoris.")

    suivant = request.POST.get('suivant', '')
    if not url_has_allowed_host_and_scheme(
        suivant, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        suivant = reverse('favoris:liste')
    return redirect(suivant)