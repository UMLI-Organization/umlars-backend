from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.utils.safestring import mark_safe

from .models import UMLModel

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '*Email Address'}))
    first_name = forms.CharField(max_length=50, label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(max_length=70, label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    orcid_id = forms.CharField(max_length=16, label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ORCID iD'}), required=False, help_text=mark_safe('<span class="form-text text-muted"><small>Optional 16-digit ORCID iD.</small></span>'))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'orcid_id', 'email', 'password1', 'password2')
        

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = '*Username'
        self.fields['username'].label = ''
        self.fields['username'].help_text = mark_safe('<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>')

        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = '*Password'
        self.fields['password1'].label = ''
        self.fields['password1'].help_text = mark_safe('<ul class="form-text text-muted small"><li>Your password can\'t be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can\'t be a commonly used password.</li><li>Your password can\'t be entirely numeric.</li></ul>')

        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = '*Confirm Password'
        self.fields['password2'].label = ''
        self.fields['password2'].help_text = mark_safe('<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>')	



class AddUMLModel(forms.ModelForm):
    name = forms.CharField(label="", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model Name'}), required=True)
    description = forms.CharField(label="", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}), required=False)
    source_file = forms.FileField(label="", widget=forms.FileInput(attrs={'class': 'form-control-file'}), required=False)
    formatted_data = forms.CharField(label="", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Formatted Data'}), required=False)

    class Meta:
        model = UMLModel
        fields = ('name', 'description', 'source_file', 'formatted_data')

    def clean(self) -> dict:
        cleaned_data = super().clean()
        source_file = cleaned_data.get('source_file')
        formatted_data = cleaned_data.get('formatted_data')

        # Ensure at least one of the fields is filled
        if not source_file and not formatted_data:
            raise forms.ValidationError("You must provide either a source file or formatted data.")

        return cleaned_data