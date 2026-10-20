from datetime import timedelta

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.urls import reverse
from django.utils import timezone

from accueil.models import MessageContact
from avis.models import Avis
from commandes.models import Commande, LigneCommande
from paiements.models import Paiement
from produits.models import Produit
from utilisateurs.models import Utilisateur

# Une commande est comptée dans le chiffre d'affaires dès qu'elle est payée
STATUTS_PAYES = ('en_preparation', 'expediee', 'livree')


def donnees_tableau():
    maintenant = timezone.localtime()
    minuit = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    debut_mois = minuit.replace(day=1)
    debut_serie = minuit - timedelta(days=29)

    # ----- Chiffre d'affaires -----
    payees = Commande.objects.filter(statut__in=STATUTS_PAYES)
    cumul = payees.aggregate(somme=Sum('total'), nb=Count('id'))
    ca_total = cumul['somme'] or 0
    nb_payees = cumul['nb']
    mois = payees.filter(date_creation__gte=debut_mois).aggregate(somme=Sum('total'), nb=Count('id'))
    panier_moyen = round(ca_total / nb_payees) if nb_payees else 0

    # ----- Clients -----
    clients = Utilisateur.objects.filter(is_staff=False, est_livreur=False)

    # ----- Commandes par statut -----
    compte = {l['statut']: l['n'] for l in Commande.objects.values('statut').annotate(n=Count('id'))}
    maximum = max(compte.values(), default=0) or 1
    statuts = [
        {
            'code': code,
            'libelle': libelle,
            'n': compte.get(code, 0),
            'pct': round(100 * compte.get(code, 0) / maximum),
        }
        for code, libelle in Commande.STATUTS
    ]

    # ----- Ventes des 30 derniers jours (calculées en Python : indépendant du moteur de base) -----
    par_jour = {}
    for date, total in payees.filter(date_creation__gte=debut_serie).values_list('date_creation', 'total'):
        jour = timezone.localtime(date).date()
        par_jour[jour] = par_jour.get(jour, 0) + total
    serie = [
        {
            'jour': debut_serie.date() + timedelta(days=i),
            'montant': par_jour.get(debut_serie.date() + timedelta(days=i), 0),
        }
        for i in range(30)
    ]
    maximum_ventes = max((s['montant'] for s in serie), default=0) or 1
    for s in serie:
        s['pct'] = max(2, int(100 * s['montant'] / maximum_ventes)) if s['montant'] else 0

    # ----- Top 5 des produits -----
    top = list(
        LigneCommande.objects.filter(commande__statut__in=STATUTS_PAYES)
        .values('nom_produit', 'reference_produit')
        .annotate(
            total_vendu=Sum('quantite'),
            chiffre=Sum(ExpressionWrapper(
                F('prix_unitaire') * F('quantite'),
                output_field=DecimalField(max_digits=14, decimal_places=0),
            )),
        )
        .order_by('-total_vendu', '-chiffre')[:5]
    )

    # ----- Stock à surveiller -----
    stock = list(Produit.objects.filter(actif=True, stock__lte=F('seuil_alerte')).order_by('stock', 'nom')[:8])
    ruptures = Produit.objects.filter(actif=True, stock__lte=0).count()

    # ----- À traiter -----
    alertes = []

    def ajouter(n, libelle, nom_url, filtre=''):
        if n:
            alertes.append({'n': n, 'libelle': libelle, 'url': reverse(nom_url) + filtre})

    ajouter(
        Commande.objects.filter(statut='en_preparation', livreur__isnull=True).count(),
        "Commandes payées sans livreur", 'admin:commandes_commande_changelist', '?statut__exact=en_preparation',
    )
    ajouter(
        Paiement.objects.filter(statut='a_rembourser').count(),
        "Paiements à rembourser", 'admin:paiements_paiement_changelist', '?statut__exact=a_rembourser',
    )
    ajouter(
        Paiement.objects.filter(statut='a_verifier').count(),
        "Paiements à vérifier", 'admin:paiements_paiement_changelist', '?statut__exact=a_verifier',
    )
    ajouter(
        Avis.objects.filter(statut='en_attente').count(),
        "Avis à modérer", 'admin:avis_avis_changelist', '?statut__exact=en_attente',
    )
    ajouter(
        MessageContact.objects.filter(traite=False).count(),
        "Messages non traités", 'admin:accueil_messagecontact_changelist', '?traite__exact=0',
    )
    ajouter(ruptures, "Produits en rupture de stock", 'admin:produits_produit_changelist')

    return {
        'ca_total': ca_total,
        'nb_payees': nb_payees,
        'ca_mois': mois['somme'] or 0,
        'nb_mois': mois['nb'],
        'panier_moyen': panier_moyen,
        'nb_clients': clients.count(),
        'nb_nouveaux': clients.filter(date_joined__gte=debut_serie).count(),
        'statuts': statuts,
        'serie': serie,
        'top': top,
        'stock': stock,
        'alertes': alertes,
    }