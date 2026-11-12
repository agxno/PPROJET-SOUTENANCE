from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render

from avis.services import contexte_avis

from .models import Categorie, Produit

PRODUITS_PAR_PAGE = 6


def _catalogue(request, produits, titre, intro, recherche=False, page_type='boutique'):
    categories = Categorie.objects.all()
    slug = request.GET.get('categorie', '')
    q = request.GET.get('q', '').strip()
    prix = request.GET.get('prix', '').strip()
    stock = request.GET.get('stock', '') == '1'
    promo = request.GET.get('promo', '') == '1'

    categorie_active = categories.filter(slug=slug).first() if slug else None
    if categorie_active:
        produits = produits.filter(categorie=categorie_active)
    if q:
        produits = produits.filter(
            Q(nom__icontains=q) | Q(description__icontains=q) | Q(reference__icontains=q)
        )

    # Filtre prix
    if prix:
        if prix.endswith('+'):
            try:
                min_prix = int(prix[:-1])
                produits = produits.filter(prix__gte=min_prix)
            except ValueError:
                pass
        elif '-' in prix:
            try:
                min_prix, max_prix = prix.split('-', 1)
                produits = produits.filter(prix__gte=int(min_prix), prix__lte=int(max_prix))
            except ValueError:
                pass

    # Filtre stock
    if stock:
        produits = produits.filter(stock__gt=0)

    # Filtre promo
    if promo:
        produits = produits.promotions()

    # Annotations pour les notes (moyenne + nombre d'avis publiés)
    produits = produits.select_related('categorie').annotate(
        note_moyenne=Avg('avis__note', filter=Q(avis__statut='publie')),
        nombre_avis=Count('avis', filter=Q(avis__statut='publie')),
    )

    page_obj = Paginator(produits, PRODUITS_PAR_PAGE).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'produits/liste.html', {
        'titre': titre,
        'intro': intro,
        'recherche': recherche,
        'categories': categories,
        'categorie_active': categorie_active,
        'q': q,
        'prix_actif': prix,
        'stock_actif': stock,
        'promo_actif': promo,
        'page_obj': page_obj,
        'qs': params.urlencode(),
        'page_type': page_type,
    })


def liste(request):
    return _catalogue(
        request, Produit.objects.disponibles(),
        "La boutique", "Découvrez toutes nos créations.",
        recherche=True, page_type='boutique',
    )


def nouveautes(request):
    return _catalogue(
        request, Produit.objects.disponibles().nouveautes(),
        "Nouveautés", "Les dernières créations de la maison.",
        page_type='nouveautes',
    )


def promotions(request):
    return _catalogue(
        request, Produit.objects.disponibles().promotions(),
        "Promotions", "Offres en cours sur une sélection de bijoux.",
        page_type='promotions',
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