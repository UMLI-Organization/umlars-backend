from datetime import datetime

from django.db import models


class SCD2Model(models.Model):
    """Abstract class used for storing data in SCD2 approach."""
    tech_valid_from = models.DateTimeField(auto_now_add=True)
    tech_valid_to = models.DateTimeField(blank=True, null=True)
    tech_active_flag = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def archive(self) -> None:
        """Marks the record as inactive and archives it."""
        self.tech_valid_to = datetime.now()
        self.tech_active_flag = False
        self.save()


class UMLModel(SCD2Model):
    """Model representing a UML diagram."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    source_file = models.FileField(upload_to="models/%Y/%m/%d/", blank=True, null=True)
    formatted_data = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - file: {self.source_file.url}"


class UMLModelMetadata(SCD2Model):
    """Metadata for UML models, connected via a OneToOne relationship."""
    model = models.OneToOneField(UMLModel, on_delete=models.CASCADE, related_name='metadata')
    data = models.JSONField(default=dict)

    def __str__(self) -> str:
        return f"{self.model.name} - metadata: {self.data}"
