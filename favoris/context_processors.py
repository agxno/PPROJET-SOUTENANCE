from .models import Favori


def favoris(request):
    if not request.user.is_authenticated:
        return {'favoris_ids': set(), 'favoris_quantite': 0}
    ids = set(
        Favori.objects.filter(utilisateur=request.user, produit__actif=True)
        .values_list('produit_id', flat=True)
    )
    return {'favoris_ids': ids, 'favoris_quantite': len(ids)}