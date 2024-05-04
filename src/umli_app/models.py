from datetime import datetime

from django.db import models


"""
Abstract class used for storing data in SCD2 approach
"""
class SCD2Model(models.Model):
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField(blank=True, null=True)
    tech_active_flag = models.BooleanField(default=True)

    def archive(self):
        self.tech_valid_to = datetime.now()
        self.tech_active_flag = False
        self.save()


class UMLModel(SCD2Model):
    name = models.CharField(max_length=200)
    # TODO: check if this is the right way to store the file
    file = models.FileField(upload_to="uploads/models/%Y/%m/%d/")
    file_data = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.name} - file: {self.file.url}"


# Metadata Model - updated only when being asked for a newer version of the model
class UMLModelMetadata(SCD2Model):
    model = models.OneToOneField(UMLModel, on_delete=models.CASCADE, related_name='metadata')
    data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.model.name} - metadata: {self.data}"
