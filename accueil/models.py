from django.db import models

# Create your models here.
class MessageContact(models.Model):
    nom = models.CharField(max_length=100)
    sujet = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    traitement = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.sujet} - {self.nom} ({self.email})"