from django import forms
from .models import Result

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'subject', 'terminal', 'marks_obtained', 'total_marks']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border: 2px solid #e0d4f7; border-radius: 8px; font-size: 1rem;'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border: 2px solid #e0d4f7; border-radius: 8px; font-size: 1rem;'
            }),
            'terminal': forms.Select(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border: 2px solid #e0d4f7; border-radius: 8px; font-size: 1rem;'
            }),
            'marks_obtained': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border: 2px solid #e0d4f7; border-radius: 8px; font-size: 1rem;',
                'placeholder': 'Enter marks obtained',
                'step': '0.01'
            }),
            'total_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border: 2px solid #e0d4f7; border-radius: 8px; font-size: 1rem;',
                'value': '100'
            }),
        }
