from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.kitap_listesi, name='kitap_listesi'),
    path('kitap/<int:pk>/', views.kitap_detay, name='kitap_detay'),
    path('yorum-begen/<int:pk>/', views.yorum_begen, name='yorum_begen'),
    path('listeye-ekle/<int:pk>/<str:durum>/', views.listeye_ekle, name='listeye_ekle'),
    path('profilim/', views.profilim, name='profilim'),

    path('kayit/', views.kayit_ol, name='kayit'),
    path('giris/', views.giris_yap, name='login'),
    path('cikis/', views.cikis_yap, name='logout'),
    path('kitap-ekle/', views.kitap_ekle, name='kitap_ekle'),

    path('sifre-sifirla/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('sifre-sifirla/tamamlandi/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
]