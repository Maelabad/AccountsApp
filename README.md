# AccountsApp - Système de Gestion d'Utilisateurs

AccountsApp est une API REST Django complète pour la gestion des utilisateurs, offrant des fonctionnalités avancées d'authentification et de gestion de profil.

- **OTP (One-Time Password)** : Système de codes à usage unique générés temporairement pour sécuriser la vérification d'email et la réinitialisation de mot de passe. Ces codes ont une durée de validité limitée et ne peuvent être utilisés qu'une seule fois, renforçant ainsi la sécurité des processus d'authentification.

- **JWT (JSON Web Tokens)** : Méthode d'authentification moderne qui permet de transmettre de façon sécurisée des informations entre le client et le serveur sous forme de jetons signés. Le système utilise une paire de tokens (access et refresh) pour maintenir une session sécurisée tout en permettant une expérience fluide.


## Fonctionnalités

- 🔐 **Inscription et Vérification** : Inscription utilisateur avec vérification par code OTP
- 🔑 **Authentification JWT** : Système d'authentification sécurisé avec JSON Web Tokens
- 👤 **Gestion de Profil** : Mise à jour des informations personnelles et téléchargement de photos de profil
- 🔄 **Réinitialisation de Mot de Passe** : Processus complet de réinitialisation par code OTP
- 📱 **API RESTful** : Interface API claire et bien documentée
- 📝 **Documentation Swagger** : Documentation API automatisée avec drf-spectacular
- 📧 **Notifications par Email** : Envoi automatique d'emails pour les OTP et les événements du compte

## Prérequis

- Python 3.8+
- Django 4.2+
- Django Rest Framework 3.14+
- Base de données (SQLite par défaut, configurable pour PostgreSQL, MySQL)
- Service SMTP pour l'envoi d'emails
- Redis (optionnel, pour les tâches asynchrones avec Celery)

## Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-username/AccountsApp.git
   cd AccountsApp

2.  Créez et activez un environnement virtuel :
    ```bash
    python -m venv myenv
    # Sous Windows
    myenv\Scripts\activate
    # Sous Linux/Mac
    source myenv/bin/activate
    
3.  Installez les dépendances :
    ```bash
    pip install -r requirements.txt

4.  Effectuez les migrations :
    ```bash
    python manage.py migrate

5.  Créez un superutilisateur (administrateur) :
    ```bash
    python manage.py createsuperuser

6.  Lancez le serveur de développement :
    ```bash
    python manage.py runserver  

## Configuration des Emails
L'application utilise le système d'emails de Django pour envoyer des notifications et des codes OTP. Configurez les paramètres suivants dans settings.py :   
```bash
# Configuration des emails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.votre-fournisseur.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre-email@domaine.com'
EMAIL_HOST_PASSWORD = 'votre-mot-de-passe'
DEFAULT_FROM_EMAIL = 'Votre Application <noreply@votreapp.com>'

Pour le développement, vous pouvez utiliser le backend de console qui affiche les emails dans la console :
```bash
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

## Traitement Asynchrone avec Celery et Redis (Optionnel)
Pour améliorer les performances, l'envoi d'emails et d'autres tâches peuvent être exécutés de manière asynchrone avec Celery et Redis.
-  Installation des dépendances
  ```bash
  pip install celery redis

- Configuration dans settings.py
  ```bash
  # Celery Configuration
  CELERY_BROKER_URL = 'redis://localhost:6379/0'
  CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
  CELERY_ACCEPT_CONTENT = ['json']
  CELERY_TASK_SERIALIZER = 'json'
  CELERY_RESULT_SERIALIZER = 'json'
  CELERY_TIMEZONE = 'UTC'

- Création du fichier celery.py à la racine du projet
      Créez un fichier celery.py dans le dossier principal du projet (à côté de settings.py) :
  ```bash
  import os
  from celery import Celery
  
  # Définir les paramètres par défaut de Django
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AccountsApp.settings')
  
  app = Celery('AccountsApp')
  app.config_from_object('django.conf:settings', namespace='CELERY')
  app.autodiscover_tasks()

- Démarrage de Celery
  ```bash
  # Dans un terminal séparé
  celery -A AccountsApp worker -l info

En utilisant Celery et Redis, vous pouvez exécuter l'envoi d'emails et d'autres tâches longues de manière asynchrone, ce qui améliore considérablement les performances de votre API.



