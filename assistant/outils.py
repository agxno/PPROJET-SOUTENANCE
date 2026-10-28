import json
import logging
import re
import unicodedata

from django.urls import reverse

from commandes.models import Commande
from panier.models import LignePanier, Panier
from produits.models import Produit

logger = logging.getLogger(__name__)

# Pages que l'assistant peut ouvrir. Le modèle ne fournit jamais d'adresse :
# il choisit un nom dans cette liste et c'est Django qui construit l'URL.
PAGES = {
    'accueil': 'accueil:accueil',
    'boutique': 'produits:liste',
    'nouveautes': 'produits:nouveautes',
    'promotions': 'produits:promotions',
    'panier': 'panier:voir',
    'favoris': 'favoris:liste',
    'compte': 'utilisateurs:tableau_bord',
    'mes_commandes': 'commandes:liste',
    'mes_adresses': 'utilisateurs:mes_adresses',
    'contact': 'accueil:contact',
    'faq': 'accueil:faq',
    'livraison_retours': 'accueil:livraison_retours',
    'cgv': 'accueil:cgv',
    'a_propos': 'accueil:a_propos',
}

OUTILS = [
    {
        "type": "function",
        "name": "rechercher_produits",
        "description": (
            "Cherche des bijoux dans le catalogue (mots-clés, catégorie, promotions, nouveautés). "
            "Renvoie jusqu'à 6 produits avec leur prix en FCFA et leur disponibilité."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "requete": {"type": "string", "description": "Mots-clés, par exemple « bague aurore »"},
                "categorie": {"type": "string", "description": "Nom de catégorie, par exemple Bagues"},
                "promotions": {"type": "boolean", "description": "Seulement les produits en promotion"},
                "nouveautes": {"type": "boolean", "description": "Seulement les nouveautés"},
            },
        },
    },
    {
        "type": "function",
        "name": "ouvrir_page",
        "description": "Ouvre une page du site pour le client.",
        "parameters": {
            "type": "object",
            "properties": {
                "page": {"type": "string", "enum": list(PAGES)},
            },
            "required": ["page"],
        },
    },
    {
        "type": "function",
        "name": "ouvrir_produit",
        "description": "Ouvre la fiche d'un produit à partir de son nom.",
        "parameters": {
            "type": "object",
            "properties": {
                "nom": {"type": "string", "description": "Nom du produit, par exemple « Bague Aurore »"},
            },
            "required": ["nom"],
        },
    },
    {
        "type": "function",
        "name": "ajouter_au_panier",
        "description": (
            "Ajoute un produit au panier du client connecté. À utiliser seulement si le client "
            "le demande clairement. Ne valide ni ne paie jamais la commande."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nom": {"type": "string", "description": "Nom du produit"},
                "quantite": {"type": "integer", "description": "Quantité, 1 par défaut, 5 au maximum"},
            },
            "required": ["nom"],
        },
    },
    {
        "type": "function",
        "name": "suivre_commande",
        "description": (
            "Donne l'état d'une commande du client connecté : la dernière par défaut, "
            "ou celle dont il donne la référence (ML-AAAA-NNNNNN)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reference": {"type": "string", "description": "Référence de la commande, facultative"},
            },
        },
    },
]


# ---------- Outils de recherche (tolérants aux accents, aux pluriels et aux erreurs de la dictée) ----------

def normaliser(texte):
    texte = unicodedata.normalize('NFD', texte or '')
    texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
    texte = re.sub(r'[^a-z0-9 ]+', ' ', texte.lower())
    return re.sub(r'\s+', ' ', texte).strip()


def _racine(mot):
    return mot[:-1] if len(mot) > 3 and mot[-1] in 'sx' else mot


def _mots(texte):
    return [_racine(m) for m in normaliser(texte).split() if len(m) > 2]


def _catalogue():
    return list(Produit.objects.disponibles().select_related('categorie')[:500])


def _resume(p):
    infos = {
        "nom": p.nom,
        "categorie": p.categorie.nom,
        "prix_fcfa": int(p.prix_actuel),
        "disponible": not p.en_rupture,
    }
    if p.en_promotion:
        infos["prix_normal_fcfa"] = int(p.prix)
        infos["remise_pct"] = p.remise
    if p.statut_stock == 'faible':
        infos["stock_faible"] = True
    return infos


def _resoudre(nom):
    """Retrouve les produits correspondant à un nom dicté (liste vide, un seul, ou plusieurs)."""
    produits = _catalogue()
    exacts = [p for p in produits if normaliser(p.nom) == normaliser(nom)]
    if len(exacts) == 1:
        return exacts
    mots = _mots(nom)
    if not mots:
        return []
    return [p for p in produits if all(m in normaliser(f"{p.nom} {p.reference}") for m in mots)]


def _definir_navigation(actions, url):
    actions[:] = [a for a in actions if a.get('type') != 'naviguer']
    actions.append({"type": "naviguer", "url": url})


# ---------- Exécution des outils ----------

def outil_rechercher(args, request, actions):
    produits = _catalogue()
    if args.get('promotions'):
        produits = [p for p in produits if p.en_promotion]
    if args.get('nouveautes'):
        produits = [p for p in produits if p.est_nouveau]
    categorie = _mots(args.get('categorie') or '')
    if categorie:
        produits = [p for p in produits if all(m in normaliser(p.categorie.nom) for m in categorie)]
    mots = _mots(args.get('requete') or '')
    if mots:
        produits = [
            p for p in produits
            if all(m in normaliser(f"{p.nom} {p.categorie.nom} {p.description}") for m in mots)
        ]
    return {"total": len(produits), "produits": [_resume(p) for p in produits[:6]]}


def outil_ouvrir_page(args, request, actions):
    nom = args.get('page')
    if nom not in PAGES:
        return {"erreur": "page_inconnue", "pages_possibles": list(PAGES)}
    _definir_navigation(actions, reverse(PAGES[nom]))
    return {"ok": True, "page": nom}


def outil_ouvrir_produit(args, request, actions):
    produits = _resoudre(args.get('nom', ''))
    if not produits:
        return {"erreur": "produit_introuvable"}
    if len(produits) > 1:
        return {"erreur": "plusieurs_produits", "candidats": [p.nom for p in produits[:5]]}
    _definir_navigation(actions, produits[0].get_absolute_url())
    return {"ok": True, "produit": produits[0].nom}


def outil_ajouter_au_panier(args, request, actions):
    if not request.user.is_authenticated:
        return {"erreur": "connexion_requise", "message": "Le client doit d'abord se connecter."}
    produits = _resoudre(args.get('nom', ''))
    if not produits:
        return {"erreur": "produit_introuvable"}
    if len(produits) > 1:
        return {"erreur": "plusieurs_produits", "candidats": [p.nom for p in produits[:5]]}
    produit = produits[0]
    if produit.en_rupture:
        return {"erreur": "epuise", "produit": produit.nom}

    try:
        quantite = int(args.get('quantite') or 1)
    except (TypeError, ValueError):
        quantite = 1
    quantite = max(1, min(quantite, 5))

    panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    ligne, _ = LignePanier.objects.get_or_create(panier=panier, produit=produit, defaults={'quantite': 0})
    souhaitee = ligne.quantite + quantite
    ligne.quantite = min(souhaitee, produit.stock)
    ligne.save()

    total = panier.quantite_totale
    actions.append({"type": "panier", "quantite": total})
    resultat = {
        "ok": True,
        "produit": produit.nom,
        "quantite_dans_le_panier": ligne.quantite,
        "articles_dans_le_panier": total,
    }
    if ligne.quantite < souhaitee:
        resultat["stock_limite"] = True
    return resultat


def outil_suivre_commande(args, request, actions):
    if not request.user.is_authenticated:
        return {"erreur": "connexion_requise", "message": "Le client doit d'abord se connecter."}
    commandes = Commande.objects.filter(utilisateur=request.user)
    reference = (args.get('reference') or '').strip().upper()
    commande = commandes.filter(reference=reference).first() if reference else commandes.first()
    if commande is None:
        return {"erreur": "commande_introuvable"}
    infos = {
        "reference": commande.reference,
        "statut": commande.get_statut_display(),
        "total_fcfa": int(commande.total),
        "date": commande.date_creation.strftime('%d/%m/%Y'),
    }
    if commande.statut == 'en_attente' and not commande.est_payee:
        infos["paiement"] = "pas encore effectué"
    if commande.livreur and commande.livreur.first_name:
        infos["livreur"] = commande.livreur.first_name
    if commande.date_livraison:
        infos["livree_le"] = commande.date_livraison.strftime('%d/%m/%Y')
    return infos


EXECUTEURS = {
    'rechercher_produits': outil_rechercher,
    'ouvrir_page': outil_ouvrir_page,
    'ouvrir_produit': outil_ouvrir_produit,
    'ajouter_au_panier': outil_ajouter_au_panier,
    'suivre_commande': outil_suivre_commande,
}


def executer(nom, arguments, request, actions):
    """Exécute un outil demandé par le modèle. Seuls les outils ci-dessus existent."""
    fonction = EXECUTEURS.get(nom)
    if fonction is None:
        return {"erreur": "outil_inconnu"}
    try:
        if isinstance(arguments, str):
            args = json.loads(arguments) if arguments.strip() else {}
        else:
            args = arguments or {}
    except ValueError:
        return {"erreur": "arguments_invalides"}
    if not isinstance(args, dict):
        args = {}
    try:
        return fonction(args, request, actions)
    except Exception:
        logger.exception("Erreur dans l'outil %s", nom)
        return {"erreur": "erreur_interne"}