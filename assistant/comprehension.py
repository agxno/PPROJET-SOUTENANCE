import re

from django.urls import reverse

from produits.models import Categorie, Produit

from . import outils
from .outils import _racine, normaliser

NOMBRES = {'un': 1, 'une': 1, 'deux': 2, 'trois': 3, 'quatre': 4, 'cinq': 5}

AIDE = (
    "Je peux chercher un bijou, ouvrir une page du site, ajouter un article à votre panier "
    "ou suivre votre commande. Par exemple : montre-moi les bagues, quelles sont les promotions, "
    "ou où en est ma commande ?"
)

# (mots-clés, page de la liste outils.PAGES, phrase)
PAGES_INFO = [
    (('rembours', 'retour', 'echange'), 'livraison_retours',
     "Les conditions de retour et de remboursement sont sur la page Livraison et retours. Je vous l'ouvre."),
    (('livraison', 'livrer', 'delai', 'frais de port'), 'livraison_retours',
     "Les informations de livraison sont sur la page Livraison et retours. Je vous l'ouvre."),
    (('faq', 'foire', 'questions frequentes'), 'faq', "Voici les questions fréquentes."),
    (('contact', 'joindre', 'ecrire', 'telephone', 'appeler'), 'contact',
     "Je vous ouvre la page de contact, vous pourrez nous écrire."),
    (('cgv', 'condition'), 'cgv', "Je vous ouvre les conditions générales de vente."),
    (('propos', 'histoire', 'qui etes', 'presentation'), 'a_propos', "Je vous ouvre la page À propos."),
]

PAGES_SIMPLES = [
    (('panier',), 'panier', "Je vous ouvre votre panier."),
    (('favori', 'coup de coeur'), 'favoris', "Voici vos favoris."),
    (('adresse',), 'mes_adresses', "Je vous ouvre vos adresses."),
    (('mon compte', 'mes informations', 'profil'), 'compte', "Je vous ouvre votre compte."),
    (('commande', 'historique'), 'mes_commandes', "Voici vos commandes."),
    (('accueil', 'page principale'), 'accueil', "Retour à l'accueil."),
]


def _a(texte, *racines):
    """Vrai si le texte (déjà normalisé) contient un mot qui commence par l'une des racines."""
    return any(re.search(r'\b' + re.escape(r), texte) for r in racines)


def _fcfa(valeur):
    return f"{int(valeur):,}".replace(',', ' ') + " francs CFA"


def _decrire(resume):
    texte = f"{resume['nom']} à {_fcfa(resume['prix_fcfa'])}"
    if resume.get('remise_pct'):
        texte += f", avec {resume['remise_pct']} pour cent de réduction"
    if not resume['disponible']:
        texte += ", actuellement épuisé"
    return texte


def _quantite(texte):
    for mot in texte.split():
        if mot.isdigit():
            return max(1, min(int(mot), 5))
        if mot in NOMBRES:
            return NOMBRES[mot]
    return 1


def _produit_de_la_page(page):
    correspondance = re.match(r'^/boutique/(?P<slug>[-\w]+)/$', page or '')
    if correspondance:
        return Produit.objects.disponibles().filter(slug=correspondance.group('slug')).first()
    return None


def _produits_cites(texte):
    """Produits dont le nom (ou le mot distinctif du nom) est prononcé. Garde les meilleurs scores."""
    mots_texte = {_racine(m) for m in texte.split() if len(m) > 2}
    candidats = []
    for produit in outils._catalogue():
        nom = normaliser(produit.nom)
        if not nom:
            continue
        if re.search(r'\b' + re.escape(nom) + r'\b', texte):
            candidats.append((1000 + len(nom), produit))
            continue
        categorie = {_racine(m) for m in normaliser(produit.categorie.nom).split()}
        distinctifs = [_racine(m) for m in nom.split() if len(m) > 2 and _racine(m) not in categorie]
        if distinctifs and all(m in mots_texte for m in distinctifs):
            candidats.append((sum(len(m) for m in distinctifs), produit))
    if not candidats:
        return []
    meilleur = max(score for score, _ in candidats)
    return [p for score, p in candidats if score == meilleur]


def _categorie_citee(texte):
    mots_texte = {_racine(m) for m in texte.split() if len(m) > 2}
    for categorie in Categorie.objects.all():
        racines = [_racine(m) for m in normaliser(categorie.nom).split() if len(m) > 2]
        if racines and all(r in mots_texte for r in racines):
            return categorie
    return None


def _ajouter_au_panier(request, texte, courant, actions):
    produits = _produits_cites(texte) or ([courant] if courant else [])
    if not produits:
        return "Quel bijou voulez-vous ajouter ? Par exemple : ajoute la bague Aurore au panier."
    if len(produits) > 1:
        return "J'hésite entre " + " et ".join(p.nom for p in produits[:3]) + ". Lequel voulez-vous ?"

    produit = produits[0]
    resultat = outils.outil_ajouter_au_panier(
        {'nom': produit.nom, 'quantite': _quantite(texte)}, request, actions
    )
    erreur = resultat.get('erreur')
    if erreur == 'connexion_requise':
        outils._definir_navigation(actions, reverse('utilisateurs:connexion'))
        return "Le panier est réservé aux clients connectés. Je vous ouvre la page de connexion."
    if erreur == 'epuise':
        return f"{produit.nom} est actuellement épuisé."
    if erreur:
        return "Je n'ai pas pu ajouter cet article. Pouvez-vous préciser le nom du bijou ?"

    articles = resultat['articles_dans_le_panier']
    phrase = f"C'est fait : {produit.nom} est dans votre panier. Vous avez {articles} article"
    phrase += "s." if articles > 1 else "."
    if resultat.get('stock_limite'):
        phrase += " Le stock est limité, j'ai ajouté le maximum disponible."
    return phrase


def _suivre_commande(request, actions):
    resultat = outils.outil_suivre_commande({}, request, actions)
    erreur = resultat.get('erreur')
    if erreur == 'connexion_requise':
        outils._definir_navigation(actions, reverse('utilisateurs:connexion'))
        return "Connectez-vous pour que je consulte vos commandes. Je vous ouvre la page de connexion."
    if erreur:
        return "Je ne trouve aucune commande sur votre compte."
    phrase = (
        f"Votre dernière commande, passée le {resultat['date']}, est {resultat['statut'].lower()}, "
        f"pour un total de {_fcfa(resultat['total_fcfa'])}."
    )
    if resultat.get('paiement'):
        phrase += " Le paiement n'est pas encore effectué."
    if resultat.get('livreur'):
        phrase += f" Votre livreur est {resultat['livreur']}."
    return phrase


def repondre(request, message, page=''):
    """Comprend une demande en français et renvoie (réponse, actions), sans IA externe."""
    texte = normaliser(message)
    actions = []
    if not texte:
        return "Je n'ai rien entendu. Pouvez-vous répéter ?", actions
    courant = _produit_de_la_page(page)

    # Politesse et aide
    if len(texte.split()) <= 3 and _a(texte, 'bonjour', 'salut', 'bonsoir', 'hello', 'coucou'):
        return ("Bonjour ! Je peux chercher un bijou, ouvrir une page, ou vous aider avec votre panier "
                "et vos commandes. Que souhaitez-vous ?"), actions
    if _a(texte, 'merci'):
        return "Avec plaisir ! Autre chose ?", actions
    if _a(texte, 'aide', 'aider', 'que peux', 'que sais', 'tu fais', 'comment ca marche', 'comment utiliser'):
        return AIDE, actions

    # Questions sur le paiement : on informe
    if _a(texte, 'paiement', 'payer') and _a(texte, 'moyen', 'mode', 'accept', 'comment', 'quel'):
        return ("Vous pouvez payer par mobile money, avec Orange, MTN, Moov ou Wave, ou par carte bancaire, "
                "sur la page sécurisée de notre prestataire de paiement."), actions

    # Actions que l'assistant ne fait jamais : il ouvre la bonne page
    if _a(texte, 'pay', 'paie', 'valid', 'commander', 'acheter', 'finalis', 'regler', 'reglement'):
        outils._definir_navigation(actions, reverse('panier:voir'))
        return ("Je ne peux pas payer ni valider une commande à votre place. Je peux ajouter les articles "
                "à votre panier, puis vous terminez vous-même en toute sécurité. Je vous ouvre le panier."), actions
    if _a(texte, 'annul'):
        outils._definir_navigation(actions, reverse('commandes:liste'))
        return ("Je ne peux pas annuler une commande à votre place. Je vous ouvre vos commandes, "
                "vous y trouverez le bouton d'annulation."), actions
    if _a(texte, 'mot de passe', 'mdp'):
        outils._definir_navigation(actions, reverse('utilisateurs:mot_de_passe_oublie'))
        return "Je vous ouvre la page pour réinitialiser votre mot de passe.", actions

    # Ajout au panier
    if _a(texte, 'ajout', 'rajout', 'mets', 'mettre', 'prends', 'prendre', 'garde') and _a(texte, 'panier', 'la', 'le', 'les'):
        if _a(texte, 'panier') or _produits_cites(texte) or courant:
            return _ajouter_au_panier(request, texte, courant, actions), actions

    # Suivi de commande
    if _a(texte, 'commande') and (
        _a(texte, 'etat', 'statut', 'suivi', 'suivre', 'arriv', 'livr', 'en est', 'avanc')
        or re.search(r'\bou\b', texte)
    ):
        return _suivre_commande(request, actions), actions

    # Pages d'information
    for racines, cle, phrase in PAGES_INFO:
        if _a(texte, *racines):
            outils._definir_navigation(actions, reverse(outils.PAGES[cle]))
            return phrase, actions

    # Promotions et nouveautés (avec un aperçu)
    if _a(texte, 'promo', 'solde', 'reduction', 'remise', 'bon plan', 'pas cher', 'moins cher'):
        resultat = outils.outil_rechercher({'promotions': True}, request, actions)
        outils._definir_navigation(actions, reverse('produits:promotions'))
        if not resultat['total']:
            return "Il n'y a pas de promotion en ce moment. Je vous ouvre quand même la page.", actions
        exemples = ", ".join(_decrire(p) for p in resultat['produits'][:2])
        pluriel = "s" if resultat['total'] > 1 else ""
        return (f"Il y a {resultat['total']} article{pluriel} en promotion, par exemple {exemples}. "
                "Je vous ouvre la page des promotions."), actions
    if _a(texte, 'nouveau', 'nouveaute', 'derniere creation', 'recent'):
        resultat = outils.outil_rechercher({'nouveautes': True}, request, actions)
        outils._definir_navigation(actions, reverse('produits:nouveautes'))
        if not resultat['total']:
            return "Il n'y a pas de nouveauté pour le moment. Je vous ouvre quand même la page.", actions
        exemples = ", ".join(p['nom'] for p in resultat['produits'][:3])
        return f"Parmi les nouveautés : {exemples}. Je vous ouvre la page des nouveautés.", actions

    # Un produit précis
    produits = _produits_cites(texte)
    question_prix = _a(texte, 'combien', 'prix', 'cout', 'tarif', 'dispo', 'stock', 'reste')
    if not produits and courant and question_prix:
        produits = [courant]
    if produits:
        if len(produits) > 1:
            return "J'hésite entre " + " et ".join(p.nom for p in produits[:3]) + ". Lequel voulez-vous ?", actions
        produit = produits[0]
        phrase = _decrire(outils._resume(produit)) + "."
        if not question_prix:
            outils._definir_navigation(actions, produit.get_absolute_url())
            phrase += " Je vous ouvre sa fiche."
        return phrase, actions

    # Une catégorie
    categorie = _categorie_citee(texte)
    if categorie:
        resultat = outils.outil_rechercher({'categorie': categorie.nom}, request, actions)
        outils._definir_navigation(actions, f"{reverse('produits:liste')}?categorie={categorie.slug}")
        if not resultat['total']:
            return f"Je n'ai pas de {categorie.nom.lower()} disponible pour le moment.", actions
        exemples = ", ".join(_decrire(p) for p in resultat['produits'][:2])
        return (f"Dans la catégorie {categorie.nom}, j'ai {resultat['total']} modèle"
                f"{'s' if resultat['total'] > 1 else ''}, par exemple {exemples}. Je vous ouvre la page."), actions

    # Pages simples
    for racines, cle, phrase in PAGES_SIMPLES:
        if _a(texte, *racines):
            outils._definir_navigation(actions, reverse(outils.PAGES[cle]))
            return phrase, actions
    if _a(texte, 'boutique', 'catalogue', 'bijou', 'produit', 'collection', 'tout voir'):
        outils._definir_navigation(actions, reverse('produits:liste'))
        return "Voici toute la boutique.", actions

    return "Je n'ai pas bien compris. " + AIDE, actions