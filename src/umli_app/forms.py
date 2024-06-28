from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.utils.safestring import mark_safe

from .models import UmlModel, UmlFile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "*Email Address"}
        ),
    )
    first_name = forms.CharField(
        max_length=50,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First Name"}
        ),
        required=False,
    )
    last_name = forms.CharField(
        max_length=70,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last Name"}
        ),
        required=False,
    )
    orcid_id = forms.CharField(
        max_length=16,
        label="",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ORCID iD"}
        ),
        required=False,
        help_text=mark_safe(
            '<span class="form-text text-muted"><small>Optional 16-digit ORCID iD.</small></span>'
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "orcid_id",
            "email",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["username"].widget.attrs["placeholder"] = "*Username"
        self.fields["username"].label = ""
        self.fields["username"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.</small></span>'
        )

        self.fields["password1"].widget.attrs["class"] = "form-control"
        self.fields["password1"].widget.attrs["placeholder"] = "*Password"
        self.fields["password1"].label = ""
        self.fields["password1"].help_text = mark_safe(
            "<ul class=\"form-text text-muted small\"><li>Your password can't be too similar to your other personal information.</li><li>Your password must contain at least 8 characters.</li><li>Your password can't be a commonly used password.</li><li>Your password can't be entirely numeric.</li></ul>"
        )

        self.fields["password2"].widget.attrs["class"] = "form-control"
        self.fields["password2"].widget.attrs["placeholder"] = "*Confirm Password"
        self.fields["password2"].label = ""
        self.fields["password2"].help_text = mark_safe(
            '<span class="form-text text-muted"><small>Enter the same password as before, for verification.</small></span>'
        )


class AddUmlModelForm(forms.ModelForm):
    class Meta:
        model = UmlModel
        fields = ("name", "description",)

    name = forms.CharField(
        label="Model Name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Model Name"}
        ),
        required=True,
    )
    description = forms.CharField(
        label="Description",
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Description", 'rows':1, 'cols':1}
        ),
        required=False,
    )
    
    
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    

class AddUmlFileForm(forms.ModelForm):
    file = forms.FileField(
        label="Source files",
        widget=MultipleFileInput(attrs={"class": "form-control-file", "multiple": True}),
        required=False,
    )

    class Meta:
        model = UmlFile
        fields = ("data", "format", "filename")


    data = forms.CharField(
        label="Raw data",
        widget=forms.Textarea(
            attrs={"class": "form-control", "placeholder": "Raw Data", 'rows':2, 'cols':1}
        ),
        required=False,
    )

    format = forms.ChoiceField(
        label="Format",
        choices=UmlFile.SupportedFormat.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
        initial=None
    )

    filename = forms.CharField(
        label="",
        widget=forms.TextInput(attrs={"class": "d-none"}),
        required=False,
        initial=None
    )

        
    def clean(self) -> dict:
        return super(AddUmlFileForm, self).clean()
        old_cleaned = cleaned_data
        filename = self.data.get('filename')
        cleaned_data['filename']= filename

        source_file = cleaned_data.get("file") or next(self.files.items())[1] if self.files else None
        filename = cleaned_data['filename']
        cleaned_data["file"] = source_file
        # raise forms.ValidationError(
        #     "You must provide either a source file or formatted data."
        #     f"Cleaned: {cleaned_data}"
        # )
        data = cleaned_data.get("data")

        # Ensure at least one of the fields is filled
        if not source_file and not data:
            raise forms.ValidationError(
                "You must provide either a source file or formatted data."
                f"Self dir: {dir(self)}"
                f"Self.files: {self.files}"
                f"Old cleaned: {old_cleaned}"
                f"Cleaned: {cleaned_data}"
            )
        
        return cleaned_data
    
    # def save(self, commit=True) -> UmlFile:
    #     instance = super(AddUmlFileForm, self).save(commit=False)
    #     if self.cleaned_data.get('file'):
    #         instance.filename = self.cleaned_data['file'].name
    #         instance.data = self.cleaned_data['file'].read().decode('utf-8')
    #     elif self.cleaned_data.get('data'):
    #         instance.data = self.cleaned_data['data']
    #     if commit:
    #         instance.save()
    #     return instance


AddUmlFileFormset = forms.inlineformset_factory(
    UmlModel, UmlFile, form=AddUmlFileForm, 
    extra=1, can_delete=True, fields=("data", "format", "file", 'filename')
)
