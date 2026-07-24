from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.kitap_listesi, name='kitap_listesi'),
    path('kitap/<int:pk>/', views.kitap_detay, name='kitap_detay'),
    path('kayit/', views.kayit_ol, name='kayit'),
    path('kitap-ekle/', views.kitap_ekle, name='kitap_ekle'),
    path('giris/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('cikis/', auth_views.LogoutView.as_view(), name='logout'),
]