from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Kitap, Yorum, OkumaListesi
from .forms import KitapForm


# Ana Sayfa
def kitap_listesi(request):
    kategori_slug = request.GET.get('kategori')

    if kategori_slug:
        kitaplar = Kitap.objects.filter(kategori=kategori_slug).order_by('-eklenme_tarihi')
    else:
        kitaplar = Kitap.objects.all().order_by('-eklenme_tarihi')

    ayin_kitabi = Kitap.objects.filter(ayin_kitabi=True).first()
    if not ayin_kitabi and Kitap.objects.exists():
        ayin_kitabi = Kitap.objects.first()

    kategoriler = Kitap.KATEGORİ_SEÇENEKLERİ

    return render(request, 'kitaplar/kitap_listesi.html', {
        'kitaplar': kitaplar,
        'ayin_kitabi': ayin_kitabi,
        'kategoriler': kategoriler,
        'secili_kategori': kategori_slug
    })


# Detay Sayfası
def kitap_detay(request, pk):
    kitap = get_object_or_404(Kitap, pk=pk)
    yorumlar = kitap.yorumlar.all().order_by('-tarih')

    liste_durumu = None
    if request.user.is_authenticated:
        m_liste = OkumaListesi.objects.filter(user=request.user, kitap=kitap).first()
        if m_liste:
            liste_durumu = m_liste.durum

    if request.method == 'POST':
        if request.user.is_authenticated:
            icerik = request.POST.get('icerik')
            puan = request.POST.get('puan', 5)
            if icerik:
                Yorum.objects.create(
                    kitap=kitap,
                    yazan=request.user,
                    icerik=icerik,
                    puan=int(puan)
                )
                return redirect('kitap_detay', pk=pk)
        else:
            return redirect('login')

    return render(request, 'kitaplar/kitap_detay.html', {
        'kitap': kitap,
        'yorumlar': yorumlar,
        'liste_durumu': liste_durumu
    })


# Yorum Beğenme Fonksiyonu
@login_required
def yorum_begen(request, pk):
    yorum = get_object_or_404(Yorum, pk=pk)
    if yorum.begeniler.filter(id=request.user.id).exists():
        yorum.begeniler.remove(request.user)
    else:
        yorum.begeniler.add(request.user)
    return redirect('kitap_detay', pk=yorum.kitap.pk)


# Listeye Ekleme
@login_required
def listeye_ekle(request, pk, durum):
    kitap = get_object_or_404(Kitap, pk=pk)
    okuma_item, created = OkumaListesi.objects.get_or_create(user=request.user, kitap=kitap)

    if not created and okuma_item.durum == durum:
        okuma_item.delete()
    else:
        okuma_item.durum = durum
        okuma_item.save()

    return redirect('kitap_detay', pk=pk)


# Profilim
@login_required
def profilim(request):
    okuduklarim = OkumaListesi.objects.filter(user=request.user, durum='okundu')
    okuyacaklarim = OkumaListesi.objects.filter(user=request.user, durum='okunacak')

    return render(request, 'kitaplar/profilim.html', {
        'okuduklarim': okuduklarim,
        'okuyacaklarim': okuyacaklarim
    })


# Kayıt
def kayit_ol(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('kitap_listesi')
    else:
        form = UserCreationForm()
    return render(request, 'registration/kayit.html', {'form': form})


# Giriş
def giris_yap(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('kitap_listesi')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


# Çıkış
def cikis_yap(request):
    logout(request)
    return redirect('kitap_listesi')


# Kitap Ekle
@login_required
def kitap_ekle(request):
    if request.method == 'POST':
        form = KitapForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('kitap_listesi')
    else:
        form = KitapForm()
    return render(request, 'kitaplar/kitap_ekle.html', {'form': form})