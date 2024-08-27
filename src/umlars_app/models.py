from datetime import datetime
from enum import Enum

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class ObjectAccessLevel(models.IntegerChoices):
    """Enum representing the access level to an object."""
    READ = 10
    WRITE = 20


class ProcessStatus(models.IntegerChoices):
    """Enum representing the status of a process."""
    QUEUED = 10
    RUNNING = 20
    FINISHED = 30
    PARTIAL_SUCCESS = 40
    FAILED = 50


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


class UmlModel(SCD2Model):
    """Model representing a UML diagram."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    formatted_data = models.TextField(blank=True, null=True)
    accessed_by = models.ManyToManyField(
        User, through="UserAccessToModel", related_name="models"
    )

    def __str__(self):
        return f"{self.name}"


class UmlFile(models.Model):
    """
    Model representing an UML file.
    If new sources are added, the SupportedFormat enum should be updated.
    """
    
    class SupportedFormat(models.TextChoices):
        UNKNOWN = "unknown", _("Unknown")
        EA_XMI = "xmi_ea", _("Enterprise Architect XMI")
        PAPYRUS_UML = "uml_papyrus", _("Papyrus UML")
        PAPYRUS_NOTATION = "notation_papyrus", _("Papyrus Notation")
        STARUML_MDJ = "mdj_staruml", _("StarUML XMI")


    data = models.TextField()
    filename = models.CharField(max_length=200, default=None, blank=True, null=True)
    
    format = models.CharField(
        max_length=50, choices=SupportedFormat.choices, default=None
    )
    state = models.IntegerField(
        choices=ProcessStatus.choices, default=ProcessStatus.QUEUED
    )

    model = models.ForeignKey(
        UmlModel, on_delete=models.CASCADE, related_name="source_files",
        blank=True, null=True
    )
    date_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File: {self.filename} for model {self.model.name} in format {self.format}"
    

class UserAccessToModel(models.Model):
    """Model representing a user's access to a UML model."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    model = models.ForeignKey(UmlModel, on_delete=models.CASCADE)
    access_level = models.IntegerField(
        choices=ObjectAccessLevel.choices, default=ObjectAccessLevel.WRITE
    )
    def __str__(self):
        return f"User {self.user} has access to model {self.model}"
