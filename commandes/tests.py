import re

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from config.fabriques import (MOT_DE_PASSE, creer_adresse, creer_commande, creer_livreur,
                              creer_produit, creer_utilisateur, remplir_panier)
from panier.models import LignePanier
from produits.models import Produit

from .models import Commande, PanierVide, StockInsuffisant


class CreationDeCommandeTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur()
        self.adresse = creer_adresse(self.utilisateur)

    def test_creation_calcule_total_decompte_le_stock_et_vide_le_panier(self):
        p1 = creer_produit(prix=45000, stock=5)
        p2 = creer_produit(prix=50000, prix_promo=40000, stock=4)
        remplir_panier(self.utilisateur, (p1, 2), (p2, 1))
        commande = Commande.creer_depuis_panier(self.utilisateur, self.adresse)

        self.assertEqual(commande.total, 2 * 45000 + 40000)
        self.assertEqual(commande.statut, 'en_attente')
        self.assertEqual(commande.lignes.count(), 2)
        p1.refresh_from_db(); p2.refresh_from_db()
        self.assertEqual((p1.stock, p2.stock), (3, 3))
        self.assertFalse(LignePanier.objects.exists())

    def test_format_de_la_reference(self):
        commande = creer_commande(self.utilisateur)
        self.assertRegex(commande.reference, r'^ML-\d{4}-\d{6}$')

    def test_les_lignes_gardent_une_copie_figee_du_produit(self):
        produit = creer_produit(nom='Bague Aurore', prix=45000)
        commande = creer_commande(self.utilisateur, produit)
        produit.prix = 99999
        produit.nom = 'Autre nom'
        produit.save()
        ligne = commande.lignes.get()
        self.assertEqual(ligne.nom_produit, 'Bague Aurore')
        self.assertEqual(ligne.prix_unitaire, 45000)

    def test_adresse_de_livraison_copiee_dans_la_commande(self):
        commande = creer_commande(self.utilisateur)
        self.adresse.ville = 'Bouaké'
        self.adresse.save()
        commande.refresh_from_db()
        self.assertEqual(commande.livraison_ville, 'Abidjan')

    def test_panier_vide_refuse(self):
        with self.assertRaises(PanierVide):
            Commande.creer_depuis_panier(self.utilisateur, self.adresse)

    def test_stock_insuffisant_refuse_sans_rien_enregistrer(self):
        produit = creer_produit(stock=1)
        remplir_panier(self.utilisateur, (produit, 3))
        with self.assertRaises(StockInsuffisant):
            Commande.creer_depuis_panier(self.utilisateur, self.adresse)
        produit.refresh_from_db()
        self.assertEqual(produit.stock, 1)
        self.assertFalse(Commande.objects.exists())

    def test_produit_masque_ignore_dans_la_commande(self):
        actif = creer_produit(stock=5)
        cache = creer_produit(stock=5, actif=False)
        remplir_panier(self.utilisateur, (actif, 1), (cache, 1))
        commande = Commande.creer_depuis_panier(self.utilisateur, self.adresse)
        self.assertEqual(commande.lignes.count(), 1)


class RegleDeStatutTests(TestCase):
    def test_annulation_remet_le_stock(self):
        produit = creer_produit(stock=5)
        commande = creer_commande(produit=produit, quantite=2)
        produit.refresh_from_db(); self.assertEqual(produit.stock, 3)
        commande.statut = 'annulee'
        commande.save()
        produit.refresh_from_db(); self.assertEqual(produit.stock, 5)

    def test_commande_annulee_ne_peut_pas_etre_rouverte(self):
        commande = creer_commande()
        commande.statut = 'annulee'; commande.save()
        commande.statut = 'en_preparation'
        with self.assertRaises(ValidationError):
            commande.full_clean()

    def test_affectation_refusee_a_un_utilisateur_qui_n_est_pas_livreur(self):
        commande = creer_commande()
        commande.livreur = creer_utilisateur()
        with self.assertRaises(ValidationError) as ctx:
            commande.full_clean()
        self.assertIn('livreur', ctx.exception.message_dict)

    def test_affectation_acceptee_pour_un_livreur(self):
        commande = creer_commande()
        commande.livreur = creer_livreur()
        commande.full_clean()

    def test_dates_d_expedition_et_de_livraison_renseignees(self):
        commande = creer_commande()
        commande.statut = 'expediee'; commande.save()
        self.assertIsNotNone(commande.date_expedition)
        commande.statut = 'livree'; commande.save()
        self.assertIsNotNone(commande.date_livraison)

    def test_seule_une_commande_en_attente_peut_etre_annulee_par_le_client(self):
        commande = creer_commande()
        self.assertTrue(commande.peut_annuler)
        commande.statut = 'en_preparation'
        self.assertFalse(commande.peut_annuler)


class VuesCommandeTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur('client@example.com')
        self.client.login(username='client@example.com', password=MOT_DE_PASSE)

    def test_validation_refusee_sans_acceptation_des_cgv(self):
        produit = creer_produit()
        remplir_panier(self.utilisateur, (produit, 1))
        adresse = creer_adresse(self.utilisateur)
        self.client.post(reverse('commandes:valider'), {'adresse': adresse.pk})
        self.assertFalse(Commande.objects.exists())

    def test_validation_complete_cree_la_commande_et_redirige(self):
        produit = creer_produit()
        remplir_panier(self.utilisateur, (produit, 1))
        adresse = creer_adresse(self.utilisateur)
        self.client.post(reverse('commandes:valider'), {'adresse': adresse.pk, 'accepte_cgv': 'on'})
        commande = Commande.objects.get()
        self.assertIsNotNone(commande.cgv_acceptees_le)

    def test_un_client_ne_voit_pas_la_commande_d_un_autre(self):
        commande = creer_commande()  # appartient à un autre utilisateur
        reponse = self.client.get(reverse('commandes:detail', args=[commande.reference]))
        self.assertEqual(reponse.status_code, 404)

    def test_le_client_annule_sa_commande_en_attente(self):
        commande = creer_commande(self.utilisateur)
        self.client.post(reverse('commandes:annuler', args=[commande.reference]))
        commande.refresh_from_db()
        self.assertEqual(commande.statut, 'annulee')

    def test_le_client_ne_peut_pas_annuler_une_commande_deja_payee(self):
        commande = creer_commande(self.utilisateur)
        commande.statut = 'en_preparation'; commande.save()
        self.client.post(reverse('commandes:annuler', args=[commande.reference]))
        commande.refresh_from_db()
        self.assertEqual(commande.statut, 'en_preparation')
