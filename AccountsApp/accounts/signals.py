from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile, Address

# Pour les tâches asynchrones (importer si Celery est configuré)
# from AccountsApp.celery import app

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un profil utilisateur et une adresse vide
    lorsqu'un nouvel utilisateur est créé.
    
    Peut également envoyer un email de bienvenue à l'utilisateur.
    """
    if created:
        # Création d'une adresse vide ou avec des valeurs par défaut
        address = Address.objects.create(
            country='',
            city='',
            postal_code=0,
            address=''
        )
        UserProfile.objects.create(user=instance, address=address)
        
        # Envoi d'un email de bienvenue
        # Pour un traitement synchrone (peut ralentir la réponse API) :
        send_welcome_email(instance)
        
        # Pour un traitement asynchrone avec Celery (recommandé en production) :
        # send_welcome_email.delay(instance.id)  # Utiliser l'ID plutôt que l'objet pour la sérialisation


def send_welcome_email(user):
    """
    Envoie un email de bienvenue à l'utilisateur nouvellement inscrit.
    
    Cette fonction peut être transformée en tâche Celery pour un traitement asynchrone.
    """
    subject = 'Bienvenue sur notre plateforme !'
    message = f'Bonjour {user.first_name or user.email},\n\n' \
              f'Merci de vous être inscrit sur notre plateforme. ' \
              f'Votre compte a été créé avec succès.\n\n' \
              f'Cordialement,\nL\'équipe de notre application'
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

# Exemple de décorateur Celery pour transformer cette fonction en tâche asynchrone
# @app.task
# def send_welcome_email_async(user_id):
#     """
#     Version asynchrone de l'envoi d'email de bienvenue.
#     Récupère l'utilisateur par son ID pour éviter les problèmes de sérialisation.
#     """
#     try:
#         user = User.objects.get(id=user_id)
#         send_welcome_email(user)
#     except User.DoesNotExist:
#         logger.error(f"Impossible d'envoyer l'email de bienvenue: Utilisateur {user_id} non trouvé")
