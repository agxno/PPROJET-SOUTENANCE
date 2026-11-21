from django.test import TestCase
from django.urls import reverse

from config.fabriques import creer_produit

from .models import Produit


class RegleDePrixEtStockTests(TestCase):
    def test_prix_promo_remplace_le_prix_normal(self):
        p = creer_produit(prix=50000, prix_promo=40000)
        self.assertTrue(p.en_promotion)
        self.assertEqual(p.prix_actuel, 40000)
        self.assertEqual(p.remise, 20)

    def test_prix_promo_superieur_au_prix_est_ignore(self):
        p = creer_produit(prix=50000, prix_promo=60000)
        self.assertFalse(p.en_promotion)
        self.assertEqual(p.prix_actuel, 50000)

    def test_statuts_de_stock(self):
        self.assertEqual(creer_produit(stock=0).statut_stock, 'rupture')
        self.assertEqual(creer_produit(stock=2).statut_stock, 'faible')
        self.assertEqual(creer_produit(stock=20).statut_stock, 'en_stock')

    def test_slug_genere_a_partir_du_nom_et_de_la_reference(self):
        p = creer_produit(nom='Bague Aurore', reference='BAG-001')
        self.assertEqual(p.slug, 'bague-aurore-bag-001')


class CatalogueTests(TestCase):
    def test_produit_masque_absent_de_la_boutique(self):
        visible = creer_produit(nom='Visible')
        creer_produit(nom='Cache', actif=False)
        self.assertEqual(list(Produit.objects.disponibles()), [visible])

    def test_page_boutique_et_recherche(self):
        creer_produit(nom='Collier Lune')
        creer_produit(nom='Bracelet Soleil')
        reponse = self.client.get(reverse('produits:liste'), {'q': 'Lune'})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, 'Collier Lune')
        self.assertNotContains(reponse, 'Bracelet Soleil')

    def test_pagination_par_6_produits(self):
        for i in range(8):
            creer_produit(nom=f'Produit {i}')
        reponse = self.client.get(reverse('produits:liste'))
        self.assertEqual(len(reponse.context['page_obj']), 6)

    def test_fiche_produit_masque_introuvable(self):
        p = creer_produit(actif=False)
        self.assertEqual(self.client.get(p.get_absolute_url()).status_code, 404)
