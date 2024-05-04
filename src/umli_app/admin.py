from django.contrib import admin

from .models import UMLModel, UMLModelMetadata

admin.site.register(UMLModel)
admin.site.register(UMLModelMetadata)