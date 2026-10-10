from django.shortcuts import render
from django.contrib import messages
from .forms import ContactForm
# Create your views here.

def accueil(request):
    return render(request, 'accueil/accueil.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre message a été envoyé avec succès !')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ContactForm()
    
    return render(request, 'accueil/contact.html', {'form': form})