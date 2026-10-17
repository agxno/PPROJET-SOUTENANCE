from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from avis.services import contexte_avis

from .models import Categorie, Produit

PRODUITS_PAR_PAGE = 6


def _catalogue(request, produits, titre, intro, recherche=False):
    categories = Categorie.objects.all()
    slug = request.GET.get('categorie', '')
    q = request.GET.get('q', '').strip()

    categorie_active = categories.filter(slug=slug).first() if slug else None
    if categorie_active:
        produits = produits.filter(categorie=categorie_active)
    if q:
        produits = produits.filter(
            Q(nom__icontains=q) | Q(description__icontains=q) | Q(reference__icontains=q)
        )

    page_obj = Paginator(produits.select_related('categorie'), PRODUITS_PAR_PAGE).get_page(
        request.GET.get('page')
    )
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'produits/liste.html', {
        'titre': titre,
        'intro': intro,
        'recherche': recherche,
        'categories': categories,
        'categorie_active': categorie_active,
        'q': q,
        'page_obj': page_obj,
        'qs': params.urlencode(),
    })


def liste(request):
    return _catalogue(
        request, Produit.objects.disponibles(),
        "La boutique", "Découvrez toutes nos créations.", recherche=True,
    )


def nouveautes(request):
    return _catalogue(
        request, Produit.objects.disponibles().nouveautes(),
        "Nouveautés", "Les dernières créations de la maison.",
    )


def promotions(request):
    return _catalogue(
        request, Produit.objects.disponibles().promotions(),
        "Promotions", "Offres en cours sur une sélection de bijoux.",
    )


def detail(request, slug):
    produit = get_object_or_404(
        Produit.objects.disponibles().select_related('categorie'), slug=slug
    )
    similaires = (
        Produit.objects.disponibles()
        .filter(categorie=produit.categorie)
        .exclude(pk=produit.pk)[:4]
    )
    contexte = {'produit': produit, 'similaires': similaires}
    contexte.update(contexte_avis(produit, request.user))
    return render(request, 'produits/detail.html', contexte)