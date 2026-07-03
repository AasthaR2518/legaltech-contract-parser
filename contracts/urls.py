from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path('upload/', views.document_upload_view, name='document-upload'),
    path('', views.document_list_view, name='document-list'),
    path('<uuid:pk>/', views.document_detail_view, name='document-detail'),
    path('<uuid:pk>/download/', views.document_download_zip_view, name='document-download-zip'),

    # B2B Multi-tenant Auth Endpoints
    path('auth/organizations/', auth_views.get_organizations, name='auth-organizations'),
    path('auth/check-organization/', auth_views.check_organization, name='auth-check-organization'),
    path('auth/register/', auth_views.register_user, name='auth-register'),
    path('auth/login/', auth_views.login_user, name='auth-login'),
    path('auth/logout/', auth_views.logout_user, name='auth-logout'),
    path('auth/team/', auth_views.get_team_members, name='auth-team-members'),
    path('auth/team/create-user/', auth_views.create_team_user, name='auth-create-team-user'),
]
