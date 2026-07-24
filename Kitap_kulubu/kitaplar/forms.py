from django import forms
from .models import Kitap

class KitapForm(forms.ModelForm):
    class Meta:
        model = Kitap
        fields = ['baslik', 'yazar', 'ozet', 'kapak_resmi']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kitap Adı'}),
            'yazar': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Yazar Adı'}),
            'ozet': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Kitap Özeti...'}),
            'kapak_resmi': forms.FileInput(attrs={'class': 'form-control'}),
        }