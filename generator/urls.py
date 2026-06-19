from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.index, name='index'), # Redirects to login/dashboard
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('email-verified/', views.email_verified_view, name='email_verified'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('create-pdf/', views.create_pdf_view, name='create_pdf'),
    path('create-ppt/', views.create_ppt_view, name='create_ppt'),
    path('saved-documents/', views.saved_documents_view, name='saved_documents'),
    path('settings/', views.settings_view, name='settings'),
    
    # Generation
    path('generate/<int:pk>/', views.generate_presentation, name='generate'),
    path('download/<int:pk>/', views.download_pdf, name='download_pdf'),
    path('download-pptx/<int:pk>/', views.download_pptx, name='download_pptx'),
    
    # Editor
    path('edit/<int:pk>/', views.edit_presentation, name='edit_presentation'),
    path('api/presentation/<int:pk>/content/', views.api_get_content, name='api_get_content'),
    path('api/presentation/<int:pk>/save/', views.api_save_content, name='api_save_content'),
    path('api/presentation/<int:pk>/regenerate/', views.api_regenerate_pdf, name='api_regenerate'),
    path('api/presentation/<int:pk>/upload/', views.api_upload_image, name='api_upload_image'),
    path('api/presentation/<int:pk>/search-images/', views.api_search_images, name='api_search_images'),
    path('api/presentation/<int:pk>/download-image/', views.api_download_image, name='api_download_image'),
    path('api/presentation/<int:pk>/delete-image/', views.api_delete_image, name='api_delete_image'),
]
