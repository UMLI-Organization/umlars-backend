from django.db import models


# UMLModel model with SCD2 approach
class UMLModel(models.Model):
    model_name = models.CharField(max_length=200)
    # TODO: check if this is the right way to store the file
    file = models.FileField(upload_to='models/files/')
    file_data = models.TextField()
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField()
    tech_active_flag = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.model_name


# Updated only when being asked for a new version of the model
class UMLModelMetadata(models.Model):
    model = models.ForeignKey(UMLModel, on_delete=models.CASCADE)
    metadata = models.JSONField()
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField()
    tech_active_flag = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.model.model_name} metadata: {self.metadata}"