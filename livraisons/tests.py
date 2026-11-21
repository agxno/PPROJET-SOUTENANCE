from django.test import TestCase
from django.urls import reverse

from config.fabriques import MOT_DE_PASSE, creer_commande, creer_livreur, creer_utilisateur
from paiements.models import Paiement


def payer(commande):
    Paiement.objects.create(
        commande=commande, fournisseur='cinetpay', methode='en_ligne', montant=commande.total
    ).marquer_reussi()
    commande.refresh_from_db()


class EspaceLivreurTests(TestCase):
    def setUp(self):
        self.livreur = creer_livreur('livreur@example.com')
        self.commande = creer_commande()
        self.commande.livreur = self.livreur
        self.commande.save()

    def connecter(self, email='livreur@example.com'):
        self.client.login(username=email, password=MOT_DE_PASSE)

    def changer(self, action):
        return self.client.post(
            reverse('livraisons:changer_statut', args=[self.commande.reference]), {'action': action}
        )

    def test_visiteur_redirige_vers_la_connexion(self):
        reponse = self.client.get(reverse('livraisons:tableau'))
        self.assertEqual(reponse.status_code, 302)

    def test_client_ordinaire_refuse(self):
        creer_utilisateur('client@example.com')
        self.connecter('client@example.com')
        self.assertEqual(self.client.get(reverse('livraisons:tableau')).status_code, 403)

    def test_le_livreur_voit_ses_commandes(self):
        self.connecter()
        reponse = self.client.get(reverse('livraisons:tableau'))
        self.assertEqual(reponse.status_code, 200)

    def test_le_livreur_ne_voit_pas_la_commande_d_un_autre_livreur(self):
        creer_livreur('autre@example.com')
        self.connecter('autre@example.com')
        reponse = self.client.get(reverse('livraisons:detail', args=[self.commande.reference]))
        self.assertEqual(reponse.status_code, 404)

    def test_impossible_de_livrer_une_commande_non_payee(self):
        self.connecter()
        self.changer('en_route')
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, 'en_attente')

    def test_cycle_complet_en_route_puis_livree(self):
        payer(self.commande)
        self.connecter()
        self.changer('en_route')
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, 'expediee')
        self.changer('livree')
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, 'livree')

    def test_transition_invalide_refusee(self):
        payer(self.commande)
        self.connecter()
        self.changer('livree')  # pas encore « en route »
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, 'en_preparation')

    def test_l_etat_ne_change_qu_en_post(self):
        payer(self.commande)
        self.connecter()
        reponse = self.client.get(reverse('livraisons:changer_statut', args=[self.commande.reference]))
        self.assertEqual(reponse.status_code, 405)
