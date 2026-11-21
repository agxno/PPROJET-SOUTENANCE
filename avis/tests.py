from django.test import TestCase
from django.urls import reverse

from config.fabriques import MOT_DE_PASSE, creer_commande, creer_produit, creer_utilisateur

from .models import Avis

DONNEES = {'note': 5, 'titre': 'Magnifique', 'commentaire': 'Un très beau bijou, bien emballé.'}


class AvisTests(TestCase):
    def setUp(self):
        self.utilisateur = creer_utilisateur('client@example.com')
        self.produit = creer_produit()
        self.commande = creer_commande(self.utilisateur, self.produit)
        self.client.login(username='client@example.com', password=MOT_DE_PASSE)
        self.url = reverse('avis:laisser', args=[self.produit.slug])

    def livrer(self):
        self.commande.statut = 'livree'
        self.commande.save()

    def test_avis_refuse_tant_que_le_produit_n_est_pas_livre(self):
        self.client.post(self.url, DONNEES)
        self.assertFalse(Avis.objects.exists())

    def test_avis_accepte_apres_livraison_et_en_attente_de_moderation(self):
        self.livrer()
        self.client.post(self.url, DONNEES)
        avis = Avis.objects.get()
        self.assertEqual(avis.statut, 'en_attente')
        self.assertEqual(avis.utilisateur, self.utilisateur)

    def test_un_seul_avis_par_produit_et_par_client(self):
        self.livrer()
        self.client.post(self.url, DONNEES)
        self.client.post(self.url, DONNEES)
        self.assertEqual(Avis.objects.count(), 1)

    def test_seuls_les_avis_publies_sont_comptes(self):
        self.livrer()
        self.client.post(self.url, DONNEES)
        self.assertFalse(Avis.objects.filter(produit=self.produit, statut='publie').exists())
        Avis.objects.update(statut='publie')
        self.assertEqual(Avis.objects.filter(produit=self.produit, statut='publie').count(), 1)

    def test_visiteur_redirige_vers_la_connexion(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url, DONNEES).status_code, 302)
        self.assertFalse(Avis.objects.exists())
