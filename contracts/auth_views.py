from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
import jwt
import datetime
from .models import Organization, UserProfile

def generate_jwt_token(user):
    profile = user.userprofile
    payload = {
        'sub': str(user.id),
        'username': user.username,
        'email': user.email,
        'org': profile.organization.name,
        'role': profile.role,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

@api_view(['GET'])
@permission_classes([AllowAny])
def get_organizations(request):
    """
    Fetch all registered organizations for the Join Workspace dropdown list.
    """
    orgs = Organization.objects.all().values('id', 'name')
    return JsonResponse(list(orgs), safe=False)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_organization(request):
    """
    Step 1 of login: dynamically check if organization exists.
    """
    name = request.GET.get('name', '').strip()
    if not name:
        return JsonResponse({"exists": False, "error": "Organization name is required."}, status=400)
    
    exists = Organization.objects.filter(name__iexact=name).exists()
    return JsonResponse({"exists": exists})

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Self-registration for new users, mapping them to a new or existing organization.
    """
    data = request.data
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone_number = data.get('phone_number', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    org_action = data.get('org_action', '') # 'create' or 'join'
    org_name = data.get('org_name', '').strip()
    org_id = data.get('org_id', '')

    # Validations
    if not (username and email and password and confirm_password and org_action):
        return JsonResponse({"error": "All fields are required."}, status=400)

    if password != confirm_password:
        return JsonResponse({"error": "Passwords do not match."}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username is already taken."}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email is already registered."}, status=400)

    # Organization resolution
    if org_action == 'create':
        if not org_name:
            return JsonResponse({"error": "New organization name is required."}, status=400)
        if Organization.objects.filter(name__iexact=org_name).exists():
            return JsonResponse({"error": "An organization with this name already exists."}, status=400)
        
        # Create Organization
        organization = Organization.objects.create(name=org_name)
        role = 'ADMIN'
    elif org_action == 'join':
        if not org_id:
            return JsonResponse({"error": "Please select an organization to join."}, status=400)
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Selected organization does not exist."}, status=400)
        role = 'MEMBER'
    else:
        return JsonResponse({"error": "Invalid organization action selection."}, status=400)

    # Create standard user
    user = User.objects.create_user(username=username, email=email, password=password)

    # Create User Profile linking to Organization
    UserProfile.objects.create(
        user=user,
        organization=organization,
        phone_number=phone_number,
        role=role
    )

    token = generate_jwt_token(user)
    return JsonResponse({
        "message": "Registration successful!",
        "token": token,
        "role": role,
        "organization": organization.name
    }, status=201)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    Custom 2-step authenticated login.
    Checks org name validity and matches credentials to that workspace.
    """
    data = request.data
    org_name = data.get('organization_name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not (org_name and username and password):
        return JsonResponse({"error": "Organization, username, and password are required."}, status=400)

    try:
        organization = Organization.objects.get(name__iexact=org_name)
    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization workspace does not exist."}, status=400)

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({"error": "Invalid username or password."}, status=401)

    # Verify if user profile links to this organization
    try:
        user_profile = user.userprofile
        if user_profile.organization != organization:
            return JsonResponse({"error": "Credentials do not match this organization workspace."}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User does not have an active profile."}, status=403)

    # Generate JWT token
    token = generate_jwt_token(user)

    return JsonResponse({
        "message": "Login successful!",
        "token": token,
        "username": user.username,
        "organization": organization.name,
        "role": user_profile.role
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user(request):
    """
    Logs out standard authenticated session.
    """
    return JsonResponse({"message": "Logout successful!"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_team_members(request):
    """
    Fetch all users/members in the logged-in user's organization.
    """
    profile = request.user.userprofile
    members = UserProfile.objects.filter(organization=profile.organization)
    
    result = []
    for member in members:
        result.append({
            "username": member.user.username,
            "email": member.user.email,
            "phone_number": member.phone_number or "Not provided",
            "role": member.role
        })
    return JsonResponse(result, safe=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_team_user(request):
    """
    Admin-only console: register a new standard user directly inside the organization.
    """
    admin_profile = request.user.userprofile
    if admin_profile.role != 'ADMIN':
        return JsonResponse({"error": "Access denied. Only organization admins can add team members."}, status=403)

    data = request.data
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    phone_number = data.get('phone_number', '').strip()
    password = data.get('password', '')

    if not (username and email and password):
        return JsonResponse({"error": "Username, email, and password are required."}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username is already taken."}, status=400)

    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email is already registered."}, status=400)

    # Create team member (defaults to 'MEMBER' role)
    user = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.create(
        user=user,
        organization=admin_profile.organization,
        phone_number=phone_number,
        role='MEMBER'
    )

    return JsonResponse({"message": f"User '{username}' successfully added to team '{admin_profile.organization.name}'."}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Fetch details of the currently logged-in user profile.
    """
    profile = request.user.userprofile
    return JsonResponse({
        "username": request.user.username,
        "email": request.user.email,
        "organization": profile.organization.name,
        "role": profile.role
    })
