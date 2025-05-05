from rest_framework import serializers
from .models import UserProfile, Address, UserModel, OTPRequest
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from datetime import datetime
from django.db.models import Sum
from datetime import datetime, timedelta
from django.conf import settings
from .utils import get_otp_code
from rest_framework.exceptions import AuthenticationFailed
from django.utils.timezone import now


User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer pour le modèle Address.
    
    Gère la sérialisation/désérialisation des informations d'adresse.
    """
    class Meta:
        model = Address
        fields = ['country', 'city', 'postal_code', 'address']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer pour les informations de base d'un utilisateur.
    
    Utilisé pour exposer les informations générales d'un utilisateur.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'inscription d'un nouvel utilisateur.
    
    Gère la validation des données d'inscription, notamment la correspondance
    des mots de passe et la vérification d'unicité de l'email.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.CharField(required=True)
    
    class Meta:
        model = UserModel
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']
        
    def validate(self, data):
        """Vérifie que les deux mots de passe fournis correspondent."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Les mots de passe doivent correspondre.")
        return data

    def validate_email(self, value):
        """Vérifie que l'email n'est pas déjà utilisé."""
        if UserModel.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email existe déjà. Connectez vous.")
        return value

    def create(self, validated_data):
        """
        Crée un nouvel utilisateur et génère un code OTP pour la vérification.
        
        L'email est également utilisé comme nom d'utilisateur.
        """
        validated_data.pop('password2')
        validated_data['username'] = validated_data['email']
        user = UserModel.objects.create_user(**validated_data)

        # Générer l'OTP après création
        otp_code, expiry_time = get_otp_code(minutes=60)
        OTPRequest.objects.create(
            user=user,
            otp_code=otp_code,
            expiry_time=expiry_time,
            purpose='register'
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la mise à jour des informations d'un utilisateur.
    
    Permet de modifier les informations du profil utilisateur, y compris 
    les informations d'adresse et les données personnelles.
    """
    # Champs modifiables de l'user
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', read_only=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    telephone_number = serializers.CharField(source='user.telephone_number', required=False)
    address = AddressSerializer(required=False)

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'profile_picture', 
                  'telephone_number', 'address']
    
    def update(self, instance, validated_data):
        """
        Met à jour les informations de l'utilisateur, son adresse et son profil.
        
        Gère la mise à jour des différentes entités liées à un utilisateur.
        """
        # Update user fields
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update address
        address_data = validated_data.pop('address', None)
        if address_data:
            for attr, value in address_data.items():
                setattr(instance.address, attr, value)
            instance.address.save()

        # Update UserProfile fields directement
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer pour le changement de mot de passe.
    
    Requiert l'ancien mot de passe et le nouveau mot de passe.
    """
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializer personnalisé pour l'obtention de tokens JWT.
    
    Ajoute des vérifications supplémentaires lors de l'authentification et
    inclut des informations sur l'expiration des tokens dans la réponse.
    """
    def validate(self, attrs):
        """
        Valide les identifiants de l'utilisateur et effectue des vérifications supplémentaires.
        
        Vérifie que l'utilisateur existe, que son mot de passe est correct,
        que son compte est vérifié et actif avant de générer les tokens.
        """
        username = attrs.get(self.username_field)
        password = attrs.get('password')

        # Récupère l'utilisateur sans encore authentifier
        try:
            user = UserModel.objects.get(**{self.username_field: username})
            # Vérification du mot de passe
            if not user.check_password(password):
                raise AuthenticationFailed("Identifiants invalides.")
        except UserModel.DoesNotExist:
            # Si l'utilisateur n'existe pas
            raise AuthenticationFailed("Identifiants invalides.")

        # Vérifications supplémentaires
        if not user.is_verify:
            raise AuthenticationFailed("Votre compte n'est pas encore vérifié.")
        
        if not user.is_active:
            raise AuthenticationFailed("Votre compte a été desactivé, veuillez contacter les administrateurs du site.")

        data = super().validate(attrs)
        
        # Récupération de l'utilisateur
        user = self.user

        refresh = self.get_token(self.user)
        access = refresh.access_token

        # Conversion des timestamps en format ISO
        data['access_token_expiration'] = datetime.fromtimestamp(access['exp']).isoformat()
        data['refresh_token_expiration'] = datetime.fromtimestamp(refresh['exp']).isoformat()

        return data


class OTPRequestSerializer(serializers.Serializer):
    """
    Serializer pour la demande de code OTP.
    
    Gère les demandes de génération de code OTP pour l'inscription ou
    la réinitialisation de mot de passe.
    """
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['register', 'reset_password'])

    def validate_email(self, value):
        """
        Vérifie que l'email correspond à un utilisateur existant et que 
        le nombre de demandes récentes ne dépasse pas la limite.
        """
        try:
            user = UserModel.objects.get(email=value)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur associé à cet email.")

        recent_otp_count = OTPRequest.objects.filter(
            user=user,
            created_at__gte=now() - timedelta(minutes=5),
            used=False,
            purpose=self.initial_data.get('purpose')
        ).count()

        if recent_otp_count >= 3:
            raise serializers.ValidationError("Trop de demandes d'OTP récentes. Veuillez patienter avant de réessayer.")

        self.context['user'] = user
        return value

    def create(self, validated_data):
        """
        Crée une nouvelle demande OTP et invalide les codes précédents non utilisés.
        
        Génère un nouveau code OTP et définit sa date d'expiration.
        """
        user = self.context['user']
        purpose = validated_data['purpose']

        # Invalider les OTP encore valides
        OTPRequest.objects.filter(
            user=user,
            purpose=purpose,
            used=False,
            expiry_time__gt=now()
        ).update(
            used=True,
            otp_code=None
        )

        # Générer un nouveau code OTP
        otp_code, expiry_time = get_otp_code()

        otp_request = OTPRequest.objects.create(
            user=user,
            otp_code=otp_code,
            expiry_time=expiry_time,
            purpose=purpose
        )
        return otp_request


class CheckOTPSerializer(serializers.Serializer):
    """
    Serializer pour la vérification d'un code OTP.
    
    Valide que le code OTP fourni est correct et non expiré.
    """
    email = serializers.EmailField()
    otp = serializers.CharField()
    purpose = serializers.ChoiceField(choices=['register', 'reset_password'])

    def validate(self, data):
        """
        Vérifie que l'email existe et que le code OTP est valide, 
        non utilisé et non expiré.
        """
        try:
            user = UserModel.objects.get(email=data['email'])
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur associé à cet email.")

        otp_request = OTPRequest.objects.filter(
            user=user,
            otp_code=data['otp'],
            purpose=data['purpose'],
            used=False,
            expiry_time__gte=now()
        ).first()

        if not otp_request:
            raise serializers.ValidationError("L'OTP renseigné n'est pas valide ou a expiré.")

        # Stocker pour la vue
        self.user = user
        self.otp_request = otp_request
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour la confirmation de réinitialisation de mot de passe.
    
    Vérifie que les nouveaux mots de passe correspondent et que l'OTP 
    a bien été validé précédemment.
    """
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        """
        Vérifie que les mots de passe correspondent et que l'utilisateur
        a bien validé un OTP pour la réinitialisation de mot de passe.
        """
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")

        try:
            user = UserModel.objects.get(email=data['email'])
        except UserModel.DoesNotExist:
            raise serializers.ValidationError("Aucun utilisateur associé à cet email.")

        # Vérifie l'OTP
        otp_request = OTPRequest.objects.filter(
            user=user,
            purpose='reset_password',
            used=True,
            expiry_time__gte=now()
        ).first()

        if not otp_request:
            raise serializers.ValidationError("OTP invalide ou expiré.")

        # Stocker l'user et l'otp_request pour la view
        self.user = user
        self.otp_request = otp_request

        return data
