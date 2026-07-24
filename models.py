import os
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class Kitap(models.Model):
    KATEGORİ_SEÇENEKLERİ = [
        ('roman', 'Roman'),
        ('bilim-kurgu', 'Bilim Kurgu'),
        ('klasik', 'Dünya Klasikleri'),
        ('felsefe', 'Felsefe & Psikoloji'),
        ('tarih', 'Tarih & Biyografi'),
        ('kisisel-gelisim', 'Kişisel Gelişim'),
        ('diger', 'Diğer'),
    ]

    baslik = models.CharField(max_length=200)
    yazar = models.CharField(max_length=100)
    ozet = models.TextField()
    kategori = models.CharField(max_length=50, choices=KATEGORİ_SEÇENEKLERİ, default='roman', verbose_name="Kategori")
    kapak_resmi = models.ImageField(upload_to='kitap_kapaklari/', blank=True, null=True,
                                    verbose_name="Kapak Resmi (İsteğe Bağlı)")
    ayin_kitabi = models.BooleanField(default=False, verbose_name="Ayın Kitabı mı?")
    eklenme_tarihi = models.DateTimeField(auto_now_add=True)

    def resim_gecerli_mi(self):
        """Kapak resminin geçerli bir dosya olup olmadığını kontrol eder."""
        if self.kapak_resmi and self.kapak_resmi.name:
            if self.kapak_resmi.name.startswith('http://') or self.kapak_resmi.name.startswith('https://'):
                return False
            return True
        return False

    def kategori_renk_sinifi(self):
        """Kategoriye göre özel renk sınıfı adı döndürür."""
        return f"cover-{self.kategori}"

    def ortalama_puan(self):
        ortalama = self.yorumlar.aggregate(Avg('puan'))['puan__avg']
        return round(ortalama, 1) if ortalama else 0.0

    def __str__(self):
        return self.baslik


class Yorum(models.Model):
    PUAN_SEÇENEKLERİ = [
        (5, '5 - Mükemmel'),
        (4, '4 - Çok İyi'),
        (3, '3 - Ortalama'),
        (2, '2 - Kötü'),
        (1, '1 - Çok Kötü'),
    ]

    kitap = models.ForeignKey(Kitap, on_delete=models.CASCADE, related_name='yorumlar')
    yazan = models.ForeignKey(User, on_delete=models.CASCADE)
    icerik = models.TextField()
    puan = models.IntegerField(choices=PUAN_SEÇENEKLERİ, default=5)
    begeniler = models.ManyToManyField(User, related_name='begenilen_yorumlar', blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def toplam_begeni(self):
        return self.begeniler.count()

    def __str__(self):
        return f"{self.yazan.username} - {self.kitap.baslik} ({self.puan} Yıldız)"


class OkumaListesi(models.Model):
    DURUM_SEÇENEKLERİ = [
        ('okunacak', 'Okuyacaklarım'),
        ('okundu', 'Okuduklarım'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liste')
    kitap = models.ForeignKey(Kitap, on_delete=models.CASCADE)
    durum = models.CharField(max_length=20, choices=DURUM_SEÇENEKLERİ)

    class Meta:
        unique_together = ('user', 'kitap')

    def __str__(self):
        return f"{self.user.username} - {self.kitap.baslik} ({self.get_durum_display()})"