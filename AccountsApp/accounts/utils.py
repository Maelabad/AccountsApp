# accounts/utils.py
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta
import random
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return {
        # "first_name" : user.first_name,
        # "last_name" : user.last_name,
        "refresh": str(refresh),
        "access": str(access),
        "access_token_expiration": datetime.fromtimestamp(access['exp']).isoformat(),
        "refresh_token_expiration": datetime.fromtimestamp(refresh['exp']).isoformat(),
    }



class CustomResponse:
    """
    Création d'une classe générique pour gérer toutes les réponses
    """
    @staticmethod
    def response(data=None, status_code=status.HTTP_200_OK):
        """
        Retourne une réponse JSON standardisée.
        """
        return Response({
            "status_code": status_code,
            "body": data
        }, status=status_code)

    @staticmethod
    def error(exception):
        """
        Capture automatiquement les erreurs DRF et renvoie un JSON standardisé avec des codes spécifiques.
        """        
        # Par défaut : 401 Unauthorized
        status_code = exception.status_code if hasattr(exception, 'status_code') else status.HTTP_401_UNAUTHORIZED
        error_message = {"detail": str(exception)}

        # Si l'exception a un attribut "detail" (comme ValidationError)
        if hasattr(exception, 'detail'):
            error_message = exception.detail if isinstance(exception.detail, dict) else {"detail": str(exception.detail)}

            # Vérifie le message exact et adapte le status_code
            detail_text = str(exception.detail)  # Transforme en string pour matcher

            if detail_text == "Identifiants invalides.":
                status_code = 401  # Unauthorized
            elif detail_text == "Votre compte n’est pas encore vérifié.":
                status_code = 403  # Forbidden
            elif detail_text == "Votre compte a été desactivé, veuillez contacter les administrateurs du site.":
                status_code = 423  # Locked (code HTTP un peu moins courant mais parfait pour "compte désactivé")

        return Response({
            "status_code": status_code,
            "body": error_message
        }, status=status_code)


def get_otp_code(minutes=10):
    otp = random.randint(1000, 9999)
    otp_expiry = datetime.now() + timedelta(minutes = minutes)
    return str(otp), otp_expiry


"""def get_otp_code(minutes=10):
    otp = random.randint(1000, 9999)
    otp_expiry = datetime.now() + timedelta(minutes = minutes)
    return str(otp), otp_expiry"""