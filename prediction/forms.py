from django import forms
from .models import ImageMatch


class ImageMatchForm(forms.ModelForm):

    class Meta:
        model = ImageMatch
        fields = ["uploaded_image"]

        widgets = {
            "uploaded_image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            )
        }

        labels = {
            "uploaded_image": "Choose Fruit Image"
        }