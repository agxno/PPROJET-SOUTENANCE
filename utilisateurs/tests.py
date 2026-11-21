import re

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from config.fabriques import MOT_DE_PASSE, creer_livreur, creer_utilisateur

from .models import Utilisateur

EMAIL_TEST = override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')


@EMAIL_TEST
class InscriptionEtActivationTests(TestCase):
    donnees = {
        'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@example.com',
        'telephone': '0102030405', 'password1': MOT_DE_PASSE, 'password2': MOT_DE_PASSE,
    }

    def _lien_activation(self):
        return re.search(r'https?://\S+/activation/\S+', mail.outbox[0].body).group(0)

    def test_inscription_cree_un_compte_inactif_et_envoie_un_email(self):
        reponse = self.client.post(reverse('utilisateurs:inscription'), self.donnees)
        utilisateur = Utilisateur.objects.get(email='ada@example.com')
        self.assertFalse(utilisateur.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(reponse, reverse('utilisateurs:activation_envoyee'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['ada@example.com'])

    def test_le_lien_active_le_compte_puis_devient_invalide(self):
        self.client.post(reverse('utilisateurs:inscription'), self.donnees)
        lien = self._lien_activation()
        chemin = '/' + lien.split('/', 3)[3]
        reponse = self.client.get(chemin)
        utilisateur = Utilisateur.objects.get(email='ada@example.com')
        self.assertTrue(utilisateur.is_active)
        self.assertRedirects(reponse, reverse('utilisateurs:tableau_bord'))
        # Le jeton inclut is_active : il ne sert qu'une fois
        self.client.logout()
        self.client.get(chemin)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_compte_non_active_ne_peut_pas_se_connecter(self):
        self.client.post(reverse('utilisateurs:inscription'), self.donnees)
        self.client.post(reverse('utilisateurs:connexion'),
                         {'username': 'ada@example.com', 'password': MOT_DE_PASSE})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_email_deja_utilise_est_refuse(self):
        creer_utilisateur('ada@example.com')
        self.client.post(reverse('utilisateurs:inscription'), self.donnees)
        self.assertEqual(Utilisateur.objects.filter(email='ada@example.com').count(), 1)

    def test_mot_de_passe_trop_simple_est_refuse(self):
        donnees = dict(self.donnees, password1='12345678', password2='12345678')
        self.client.post(reverse('utilisateurs:inscription'), donnees)
        self.assertFalse(Utilisateur.objects.filter(email='ada@example.com').exists())


class SecuriteComptesTests(TestCase):
    def test_mot_de_passe_stocke_hache_jamais_en_clair(self):
        u = creer_utilisateur()
        self.assertNotEqual(u.password, MOT_DE_PASSE)
        self.assertNotIn(MOT_DE_PASSE, u.password)
        self.assertTrue(u.check_password(MOT_DE_PASSE))

    def test_connexion_par_email(self):
        u = creer_utilisateur('awa@example.com')
        self.assertTrue(self.client.login(username='awa@example.com', password=MOT_DE_PASSE))
        self.assertEqual(int(self.client.session['_auth_user_id']), u.pk)

    def test_visiteur_redirige_vers_la_connexion_pour_acceder_au_compte(self):
        reponse = self.client.get(reverse('utilisateurs:tableau_bord'))
        self.assertEqual(reponse.status_code, 302)
        self.assertIn('/connexion/', reponse['Location'])

    def test_livreur_redirige_vers_son_espace_apres_connexion(self):
        livreur = creer_livreur('livreur@example.com')
        reponse = self.client.post(reverse('utilisateurs:connexion'),
                                   {'username': livreur.email, 'password': MOT_DE_PASSE})
        self.assertRedirects(reponse, reverse('livraisons:tableau'))

    def test_creation_superutilisateur(self):
        admin = Utilisateur.objects.create_superuser(email='admin@example.com', password=MOT_DE_PASSE)
        self.assertTrue(admin.is_staff and admin.is_superuser)
        self.assertFalse(admin.est_livreur)

    def test_session_expire_apres_inactivite_configuree(self):
        from django.conf import settings
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, 24 * 3600)
