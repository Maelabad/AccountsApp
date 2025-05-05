from .models import UserProfile
from django.contrib.auth import (get_user_model, 
                                 update_session_auth_hash, logout
                                 )
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .utils import get_tokens_for_user

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import ( UserRegistrationSerializer, UserUpdateSerializer, 
                           ChangePasswordSerializer, MyTokenObtainPairSerializer, 
                           UserSerializer, OTPRequestSerializer, 
                           PasswordResetConfirmSerializer, CheckOTPSerializer
                            )
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from drf_spectacular.utils import extend_schema
from django.conf import settings
from .utils import CustomResponse

from rest_framework.exceptions import APIException


User = get_user_model()
token_generator = PasswordResetTokenGenerator()

# Inscription
@extend_schema(tags=["Accounts - Register"])
class RegisterView(generics.CreateAPIView):
    """
    Vue pour l'inscription des utilisateurs.
    
    Permet de créer un nouvel utilisateur avec les informations de base.
    Un code OTP est généré pour la vérification de l'email.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Crée un nouvel utilisateur et renvoie une réponse personnalisée.
        
        Le code OTP est généré automatiquement lors de la création.
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()  # Ajoutez cette ligne pour créer l'utilisateur
            return CustomResponse.response(serializer.data, status_code=status.HTTP_201_CREATED)
        except APIException as e:
            return CustomResponse.error(e)


@extend_schema(tags=["Accounts - Login"])
class MyTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée pour l'obtention de tokens JWT.
    
    Utilise un serializer personnalisé qui effectue des vérifications
    supplémentaires et inclut des informations sur l'expiration des tokens.
    """
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Valide les identifiants et génère les tokens JWT.
        
        Renvoie une réponse personnalisée avec les tokens et leur date d'expiration.
        """
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            return CustomResponse.response(serializer.validated_data, status_code=status.HTTP_200_OK)

        except APIException as e:
            return CustomResponse.error(e)

        except Exception as e:
            error_message = serializer.errors if hasattr(serializer, 'errors') else str(e)
            return CustomResponse.error(error_message, status_code=status.HTTP_400_BAD_REQUEST)


# Déconnexion
@extend_schema(tags=["Accounts - Logout"])
class LogoutView(APIView):
    """
    Vue pour la déconnexion des utilisateurs.
    
    Nécessite une authentification et invalide la session courante.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        """Déconnecte l'utilisateur en invalidant sa session."""
        logout(request)
        return Response({"message": "Vous etes déconnecté"}, status=status.HTTP_200_OK)


# Mise à jour des informations utilisateur
@extend_schema(tags=["Accounts - Profile"])
class UserUpdateView(generics.RetrieveUpdateAPIView):
    """
    Vue pour la récupération et la mise à jour des informations utilisateur.
    
    Permet de consulter et modifier les informations du profil utilisateur.
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Récupère le profil de l'utilisateur authentifié."""
        return UserProfile.objects.select_related('user', 'address').get(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """
        Récupère les informations de l'utilisateur (GET).
        
        Renvoie une réponse personnalisée avec les données du profil.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return CustomResponse.response(serializer.data, status_code=status.HTTP_200_OK)
        except APIException as e:
            return CustomResponse.error(e)

    def update(self, request, *args, **kwargs):
        """
        Met à jour les informations de l'utilisateur (PATCH/PUT).
        
        Permet de modifier les informations du profil et renvoie une réponse personnalisée.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return CustomResponse.response(serializer.data, status_code=status.HTTP_200_OK)
        except APIException as e:
            return CustomResponse.error(e)
        except Exception as e:
            return CustomResponse.error(str(e), status_code=status.HTTP_400_BAD_REQUEST)


# Changement de mot de passe
@extend_schema(tags=["Accounts - Change Password"])
class ChangePasswordView(generics.UpdateAPIView):
    """
    Vue pour le changement de mot de passe.
    
    Permet à un utilisateur authentifié de changer son mot de passe
    en fournissant l'ancien et le nouveau mot de passe.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Récupère l'utilisateur authentifié."""
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """
        Met à jour le mot de passe de l'utilisateur.
        
        Vérifie que l'ancien mot de passe est correct avant d'effectuer la modification.
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data.get("old_password")):
                return Response({"old_password": ["Mot de passe actuel incorrect."]}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            # Pour éviter que l'utilisateur soit déconnecté après le changement de mot de passe
            update_session_auth_hash(request, user)
            return Response({"message": "Mot de passe modifié avec succès"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Accounts - OTP Request"])
class OTPRequestView(APIView):
    """
    Vue pour la demande de code OTP.
    
    Permet de demander un code OTP pour l'inscription ou
    la réinitialisation de mot de passe.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = OTPRequestSerializer

    def post(self, request, *args, **kwargs):
        """
        Génère un nouveau code OTP et l'envoie à l'utilisateur.
        
        Le code est stocké en base de données avec sa date d'expiration.
        """
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # Création de l'OTPRequest

        return Response({"message": "Un OTP vous a été envoyé par email."}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Accounts - OTP Check"])
class CheckOTPView(APIView):
    """
    Vue pour la vérification d'un code OTP.
    
    Permet de valider un code OTP fourni par l'utilisateur pour
    l'inscription ou la réinitialisation de mot de passe.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = CheckOTPSerializer

    def post(self, request, *args, **kwargs):
        """
        Vérifie la validité du code OTP fourni.
        
        Si le code est valide, le marque comme utilisé et effectue les actions
        correspondant à son objectif (activation de compte ou préparation de
        réinitialisation de mot de passe).
        """
        serializer = CheckOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        otp_request = serializer.otp_request

        otp_request.used = True

        if otp_request.purpose == 'register':
            user.is_verify = True  # Valide le compte utilisateur
            otp_request.otp_code = None
            user.save()

        otp_request.save()

        return Response({"message": "OTP vérifié avec succès."}, status=status.HTTP_200_OK)


@extend_schema(tags=["Accounts - Reset Password"])
class PasswordResetConfirmView(APIView):
    """
    Vue pour la confirmation de réinitialisation de mot de passe.
    
    Permet de définir un nouveau mot de passe après validation du code OTP.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        """
        Réinitialise le mot de passe de l'utilisateur.
        
        Vérifie que l'OTP a bien été validé et que les nouveaux mots de passe correspondent.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        otp_request = serializer.otp_request

        # Réinitialiser le mot de passe
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        # Marquer l'OTP comme utilisé
        otp_request.otp_code = None
        otp_request.save()

        return Response({"message": "Mot de passe réinitialisé avec succès."}, status=200)
