from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['author', 'rating', 'comment']
        widgets = {
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Escribe tu opinión...'}),
        }
        labels = {
            'author': 'Nombre',
            'rating': 'Puntuación (1-5)',
            'comment': 'Comentario'
        }