"""Fabriques d'objets réutilisées par les tests des différentes applications."""
import itertools

from commandes.models import Commande
from panier.models import LignePanier, Panier
from produits.models import Categorie, Produit
from utilisateurs.models import Adresse, Utilisateur

MOT_DE_PASSE = 'UnMotDePasseSolide123!'
_compteur = itertools.count(1)


def creer_utilisateur(email=None, **extra):
    n = next(_compteur)
    email = email or f'client{n}@example.com'
    return Utilisateur.objects.create_user(
        email=email, password=MOT_DE_PASSE, first_name='Test', last_name=f'Client{n}', **extra
    )


def creer_livreur(email=None):
    return creer_utilisateur(email or f'livreur{next(_compteur)}@example.com', est_livreur=True)


def creer_produit(nom='Bague Test', prix=45000, stock=5, **extra):
    categorie, _ = Categorie.objects.get_or_create(nom='Bagues')
    n = next(_compteur)
    return Produit.objects.create(
        categorie=categorie, nom=nom, reference=extra.pop('reference', f'REF-{n:04d}'),
        prix=prix, stock=stock, **extra
    )


def creer_adresse(utilisateur):
    return Adresse.objects.create(
        utilisateur=utilisateur, prenom='Awa', nom='Kone', adresse='Rue 12, Cocody',
        ville='Abidjan', telephone='0102030405', par_defaut=True,
    )


def remplir_panier(utilisateur, *lignes):
    """lignes : couples (produit, quantite)."""
    panier, _ = Panier.objects.get_or_create(utilisateur=utilisateur)
    for produit, quantite in lignes:
        LignePanier.objects.create(panier=panier, produit=produit, quantite=quantite)
    return panier


def creer_commande(utilisateur=None, produit=None, quantite=1):
    utilisateur = utilisateur or creer_utilisateur()
    produit = produit or creer_produit()
    remplir_panier(utilisateur, (produit, quantite))
    return Commande.creer_depuis_panier(utilisateur, creer_adresse(utilisateur))
