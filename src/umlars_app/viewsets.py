from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from umlars_app.models import UmlModel, UmlModelMetadata
from umlars_app.serializers import UmlModelSerializer, UmlModelMetadataSerializer, UmlFileSerializer


class UmlModelViewSet(viewsets.ModelViewSet):
    queryset = UmlModel.objects.all()
    serializer_class = UmlModelSerializer
    permission_classes = [AllowAny]


class UmlModelMetadataViewSet(viewsets.ModelViewSet):
    queryset = UmlModelMetadata.objects.all()
    serializer_class = UmlModelMetadataSerializer
    permission_classes = [AllowAny]


class UmlFileViewSet(viewsets.GenericViewSet):
    serializer_class = UmlFileSerializer
    permission_classes = [AllowAny]

    def get( self, request: Request, pk: int) -> Response:
        try:
            uml_model = UmlModel.objects.get(pk=pk)
            files = uml_model.source_files.all()
            serializer = self.get_serializer(files, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UmlModel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)