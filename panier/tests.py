from django.test import TestCase
from django.urls import reverse

from config.fabriques import MOT_DE_PASSE, creer_produit, creer_utilisateur, remplir_panier

from .models import LignePanier


class PanierTests(TestCase):
    def setUp(self):
        self.client_u = creer_utilisateur('client@example.com')
        self.client.login(username='client@example.com', password=MOT_DE_PASSE)

    def test_visiteur_ne_peut_pas_utiliser_le_panier(self):
        self.client.logout()
        produit = creer_produit()
        reponse = self.client.post(reverse('panier:ajouter', args=[produit.pk]))
        self.assertEqual(reponse.status_code, 302)
        self.assertIn('/connexion/', reponse['Location'])
        self.assertFalse(LignePanier.objects.exists())

    def test_ajout_au_panier(self):
        produit = creer_produit(stock=5)
        self.client.post(reverse('panier:ajouter', args=[produit.pk]), {'quantite': 2})
        ligne = LignePanier.objects.get()
        self.assertEqual(ligne.quantite, 2)

    def test_la_quantite_est_plafonnee_au_stock(self):
        produit = creer_produit(stock=3)
        self.client.post(reverse('panier:ajouter', args=[produit.pk]), {'quantite': 10})
        self.assertEqual(LignePanier.objects.get().quantite, 3)

    def test_produit_epuise_non_ajoutable(self):
        produit = creer_produit(stock=0)
        self.client.post(reverse('panier:ajouter', args=[produit.pk]))
        self.assertFalse(LignePanier.objects.exists())

    def test_produit_masque_non_ajoutable(self):
        produit = creer_produit(actif=False)
        reponse = self.client.post(reverse('panier:ajouter', args=[produit.pk]))
        self.assertEqual(reponse.status_code, 404)

    def test_sous_total_utilise_le_prix_promotionnel(self):
        produit = creer_produit(prix=50000, prix_promo=40000, stock=5)
        remplir_panier(self.client_u, (produit, 3))
        self.assertEqual(LignePanier.objects.get().sous_total, 120000)

    def test_un_client_ne_modifie_pas_le_panier_d_un_autre(self):
        autre = creer_utilisateur('autre@example.com')
        produit = creer_produit()
        remplir_panier(autre, (produit, 1))
        ligne = LignePanier.objects.get()
        reponse = self.client.post(reverse('panier:retirer', args=[ligne.pk]))
        self.assertEqual(reponse.status_code, 404)
        self.assertTrue(LignePanier.objects.filter(pk=ligne.pk).exists())
