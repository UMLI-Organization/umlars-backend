from django.db import models


# UMLModel model with SCD2 approach
class UMLModel(models.Model):
    model_name = models.CharField(max_length=200)
    # TODO: check if this is the right way to store the file
    file = models.FileField(upload_to="uploads/models/%Y/%m/%d/")
    file_data = models.TextField(blank=True, null=True)
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField(blank=True, null=True)
    tech_active_flag = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.model_name} - file: {self.file.url}"


# Updated only when being asked for a new version of the model
class UMLModelMetadata(models.Model):
    model = models.ForeignKey(UMLModel, on_delete=models.CASCADE)
    metadata = models.JSONField(default=dict)
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField(blank=True, null=True)
    tech_active_flag = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.model.model_name} - metadata: {self.metadata}"