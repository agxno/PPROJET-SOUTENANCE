import json
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from config.fabriques import MOT_DE_PASSE, creer_commande, creer_utilisateur

from .models import Paiement


def nouveau_paiement(commande):
    return Paiement.objects.create(
        commande=commande, fournisseur='cinetpay', methode='en_ligne', montant=commande.total
    )


class ValidationDuPaiementTests(TestCase):
    def test_identifiant_de_transaction_genere(self):
        paiement = nouveau_paiement(creer_commande())
        self.assertRegex(paiement.transaction_id, r'^PAY-[0-9A-F]{12}$')

    def test_paiement_reussi_passe_la_commande_en_preparation(self):
        commande = creer_commande()
        paiement = nouveau_paiement(commande)
        self.assertTrue(paiement.marquer_reussi())
        commande.refresh_from_db(); paiement.refresh_from_db()
        self.assertEqual(paiement.statut, 'reussi')
        self.assertEqual(commande.statut, 'en_preparation')
        self.assertTrue(commande.est_payee)

    def test_validation_idempotente(self):
        commande = creer_commande()
        paiement = nouveau_paiement(commande)
        paiement.marquer_reussi()
        commande.statut = 'expediee'; commande.save()
        self.assertTrue(paiement.marquer_reussi())  # rappel : ne change rien
        commande.refresh_from_db()
        self.assertEqual(commande.statut, 'expediee')

    def test_paiement_sur_commande_annulee_est_a_rembourser(self):
        commande = creer_commande()
        paiement = nouveau_paiement(commande)
        commande.statut = 'annulee'; commande.save()
        self.assertFalse(paiement.marquer_reussi())
        paiement.refresh_from_db(); commande.refresh_from_db()
        self.assertEqual(paiement.statut, 'a_rembourser')
        self.assertEqual(commande.statut, 'annulee')

    def test_second_paiement_sur_commande_deja_payee_est_a_rembourser(self):
        commande = creer_commande()
        premier, second = nouveau_paiement(commande), nouveau_paiement(commande)
        premier.marquer_reussi()
        self.assertFalse(second.marquer_reussi())
        second.refresh_from_db()
        self.assertEqual(second.statut, 'a_rembourser')

    def test_echec_et_signalement(self):
        paiement = nouveau_paiement(creer_commande())
        paiement.signaler_a_verifier()
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, 'a_verifier')


class WebhookTests(TestCase):
    def test_le_webhook_ne_croit_pas_son_contenu_et_revérifie_aupres_de_cinetpay(self):
        commande = creer_commande()
        paiement = nouveau_paiement(commande)
        notification = SimpleNamespace(merchant_transaction_id=paiement.transaction_id)
        with mock.patch('paiements.views.cinetpay.lire_notification', return_value=notification), \
             mock.patch('paiements.views.cinetpay.synchroniser') as synchroniser:
            reponse = self.client.post(
                reverse('paiements:webhook_cinetpay'),
                data=json.dumps({'statut': 'SUCCESS'}), content_type='application/json',
            )
        self.assertEqual(reponse.status_code, 200)
        synchroniser.assert_called_once()
        commande.refresh_from_db()
        # La notification annonce un succès, mais sans confirmation de CinetPay rien n'est validé
        self.assertEqual(commande.statut, 'en_attente')

    def test_notification_illisible_refusee(self):
        with mock.patch('paiements.views.cinetpay.lire_notification', side_effect=ValueError):
            reponse = self.client.post(reverse('paiements:webhook_cinetpay'), data='nimporte quoi',
                                       content_type='text/plain')
        self.assertEqual(reponse.status_code, 400)

    def test_transaction_inconnue(self):
        notification = SimpleNamespace(merchant_transaction_id='PAY-INCONNU00000')
        with mock.patch('paiements.views.cinetpay.lire_notification', return_value=notification):
            reponse = self.client.post(reverse('paiements:webhook_cinetpay'), data='{}',
                                       content_type='application/json')
        self.assertEqual(reponse.status_code, 404)

    def test_webhook_refuse_les_requetes_get(self):
        self.assertEqual(self.client.get(reverse('paiements:webhook_cinetpay')).status_code, 405)


class PageDePaiementTests(TestCase):
    def test_paiement_d_une_commande_d_autrui_refuse(self):
        commande = creer_commande()
        creer_utilisateur('intrus@example.com')
        self.client.login(username='intrus@example.com', password=MOT_DE_PASSE)
        reponse = self.client.get(reverse('paiements:payer', args=[commande.reference]))
        self.assertEqual(reponse.status_code, 404)

    def test_page_de_paiement_n_expose_pas_de_details_techniques(self):
        commande = creer_commande()
        self.client.login(username=commande.utilisateur.email, password=MOT_DE_PASSE)
        reponse = self.client.get(reverse('paiements:payer', args=[commande.reference]))
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, 'SITE_URL')
        self.assertNotContains(reponse, 'Clé API')
