from .models import Panier


def panier(request):
    if not request.user.is_authenticated:
        return {'panier_quantite': 0}
    p = Panier.objects.filter(utilisateur=request.user).first()
    return {'panier_quantite': p.quantite_totale if p else 0}