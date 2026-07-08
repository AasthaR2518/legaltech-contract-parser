import jwt
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate_header(self, request):
        return 'Bearer realm="api"'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        try:
            parts = auth_header.split(' ')
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return None
            token = parts[1]
        except Exception:
            return None

        try:
            # 1. Protection against None algorithm vulnerability
            unverified_header = jwt.get_unverified_header(token)
            if unverified_header.get('alg', '').lower() == 'none':
                raise exceptions.AuthenticationFailed('Invalid token algorithm.')
                
            # 2. Enforce HS256 algorithm explicitly to prevent key confusion attacks
            if unverified_header.get('alg') != 'HS256':
                raise exceptions.AuthenticationFailed('Invalid signature algorithm. HS256 is required.')

            # Decode token using HS256 and Django SECRET_KEY
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            user_id = payload.get('sub')
            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token claims.')
                
            user = User.objects.get(id=user_id)
            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired.')
        except (jwt.InvalidTokenError, User.DoesNotExist):
            raise exceptions.AuthenticationFailed('Invalid token.')
