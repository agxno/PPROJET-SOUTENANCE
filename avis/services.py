from django.db.models import Avg, Count

from commandes.models import LigneCommande


def _lignes_livrees(utilisateur, produit):
    return LigneCommande.objects.filter(
        produit=produit, commande__utilisateur=utilisateur, commande__statut='livree'
    )


def a_recu_le_produit(utilisateur, produit):
    return _lignes_livrees(utilisateur, produit).exists()


def commande_livree(utilisateur, produit):
    """Dernière commande livrée contenant ce produit (ou None)."""
    ligne = (
        _lignes_livrees(utilisateur, produit)
        .select_related('commande')
        .order_by('-commande__date_livraison', '-commande__pk')
        .first()
    )
    return ligne.commande if ligne else None


def contexte_avis(produit, utilisateur):
    """Données d'affichage des avis pour la fiche d'un produit."""
    publies = produit.avis.filter(statut='publie').select_related('utilisateur')
    stats = publies.aggregate(moyenne=Avg('note'), total=Count('id'))
    moyenne = round(stats['moyenne'], 1) if stats['moyenne'] else None
    entiere = round(stats['moyenne']) if stats['moyenne'] else 0

    contexte = {
        'avis_publies': publies[:20],
        'avis_total': stats['total'],
        'avis_moyenne': moyenne,
        'avis_etoiles': "★" * entiere + "☆" * (5 - entiere),
        'peut_donner_avis': False,
        'avis_existant': None,
    }
    if utilisateur.is_authenticated:
        existant = produit.avis.filter(utilisateur=utilisateur).first()
        contexte['avis_existant'] = existant
        if existant is None:
            contexte['peut_donner_avis'] = a_recu_le_produit(utilisateur, produit)
    return contexte