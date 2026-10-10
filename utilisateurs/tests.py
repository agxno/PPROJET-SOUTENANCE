from urllib.parse import urlparse

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Utilisateur


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ConfirmationEmailTests(TestCase):
	def test_inscription_requires_email_confirmation(self):
		response = self.client.post(reverse('utilisateurs:inscription'), {
			'first_name': 'Ada',
			'last_name': 'Lovelace',
			'email': 'ada@example.com',
			'telephone': '0102030405',
			'password1': 'UnMotDePasseSolide123!',
			'password2': 'UnMotDePasseSolide123!',
		})

		utilisateur = Utilisateur.objects.get(email='ada@example.com')
		self.assertFalse(utilisateur.is_active)
		self.assertNotIn('_auth_user_id', self.client.session)
		self.assertRedirects(response, reverse('utilisateurs:connexion'))
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, ['ada@example.com'])

		lien = next(
			line for line in mail.outbox[0].body.splitlines()
			if line.startswith('http://')
		)
		confirmation = self.client.get(urlparse(lien).path)

		utilisateur.refresh_from_db()
		self.assertTrue(utilisateur.is_active)
		self.assertRedirects(confirmation, reverse('utilisateurs:connexion'))
