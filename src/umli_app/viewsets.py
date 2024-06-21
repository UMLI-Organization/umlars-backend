from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from umli_app.models import UmlModel, UmlModelMetadata

from umli_app.serializers import UmlModelSerializer, UmlModelMetadataSerializer


class UmlModelViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all()
    serializer_class = UmlModelSerializer
    permission_classes = [AllowAny]


class UmlModelMetadataViewSet(viewsets.ModelViewSet):
    queryset = UmlModelMetadata.objects.all()
    serializer_class = UmlModelMetadataSerializer
    permission_classes = [AllowAny]