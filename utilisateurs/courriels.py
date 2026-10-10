from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .jetons import jeton_activation


def envoyer_mail_activation(request, utilisateur):
    uid = urlsafe_base64_encode(force_bytes(utilisateur.pk))
    jeton = jeton_activation.make_token(utilisateur)
    lien = request.build_absolute_uri(
        reverse('utilisateurs:activation', kwargs={'uidb64': uid, 'token': jeton})
    )
    sujet = render_to_string('utilisateurs/emails/sujet_activation.txt').strip()
    message = render_to_string('utilisateurs/emails/activation.txt', {
        'utilisateur': utilisateur,
        'lien': lien,
    })
    send_mail(sujet, message, None, [utilisateur.email])