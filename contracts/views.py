from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Document
from .serializers import (
    DocumentSerializer, 
    DocumentDetailSerializer, 
    DocumentUploadSerializer
)

class DocumentUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            
            # Create the Document instance in the database
            # Django's FileField takes care of renaming and saving the file to media/contracts/
            document = Document.objects.create(
                file=uploaded_file,
                original_name=uploaded_file.name,
                status='PENDING' # Will be processed in later weeks
            )
            
            # Serialize the created document metadata
            output_serializer = DocumentSerializer(document)
            return Response(
                {
                    "message": "File uploaded successfully. Document queued for processing.",
                    "data": output_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentListView(APIView):
    def get(self, request, *args, **kwargs):
        documents = Document.objects.all()
        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDetailView(APIView):
    def get(self, request, pk, *args, **kwargs):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response(
                {"error": "Document not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

