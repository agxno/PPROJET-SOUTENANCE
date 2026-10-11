from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse


def envoyer_confirmation(request, commande):
    lien = request.build_absolute_uri(
        reverse('commandes:detail', kwargs={'reference': commande.reference})
    )
    sujet = render_to_string(
        'commandes/emails/sujet_confirmation.txt', {'commande': commande}
    ).strip()
    message = render_to_string(
        'commandes/emails/confirmation.txt', {'commande': commande, 'lien': lien}
    )
    send_mail(sujet, message, None, [commande.utilisateur.email])