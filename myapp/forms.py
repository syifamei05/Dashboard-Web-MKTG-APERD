from django.forms import ModelForm
from .models import Aperd, Product, AumData
from django import forms

class AperdForm(ModelForm):
    class Meta:
        model = Aperd
        fields = ['name', 'pic', 'progress', 'desc']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input'
            }),
            'pic': forms.TextInput(attrs={
                'class': 'form-input'
            }),
            'progress': forms.Select(attrs={
                'class': 'form-input'
            }),
            'desc': forms.TextInput(attrs={  # Changed from Textarea to TextInput
                'class': 'form-input'
            })
        }

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'status', 'aperd', 'desc']

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input'
            }),
            'status': forms.Select(attrs={
                'class': 'form-input'
            }),
            'aperd': forms.CheckboxSelectMultiple(),
            'desc': forms.TextInput(attrs={  # Changed from Textarea to TextInput
                'class': 'form-input'
            })
        }

class AumDataForm(forms.ModelForm):
    class Meta:
        model = AumData
        fields = ['date', 'aum', 'aperd']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'aum': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            }),
            'aperd': forms.Select(attrs={
                'class': 'form-input'
            })
        }
        labels = {
            'aperd': 'APERD'
        }