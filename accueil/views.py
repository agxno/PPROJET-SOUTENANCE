from django.contrib import messages
from django.shortcuts import redirect, render

from avis.models import Avis
from produits.models import Categorie, Produit

from .forms import ContactForm


def accueil(request):
    return render(request, 'accueil/accueil.html', {
        'categories': Categorie.objects.all()[:4],
        'nouveautes': Produit.objects.disponibles().order_by('-date_creation')[:4],
        'temoignages': (
            Avis.objects.filter(statut='publie', note__gte=4)
            .select_related('produit', 'utilisateur')[:3]
        ),
    })


def a_propos(request):
    return render(request, 'accueil/a_propos.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre message a bien été envoyé. Nous vous répondrons rapidement.")
            return redirect('accueil:contact')
    else:
        form = ContactForm()
    return render(request, 'accueil/contact.html', {'form': form})