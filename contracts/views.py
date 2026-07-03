import os
import io
import zipfile
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import Document
from .serializers import (
    DocumentSerializer, 
    DocumentDetailSerializer, 
    DocumentUploadSerializer
)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def document_upload_view(request):
    serializer = DocumentUploadSerializer(data=request.data)
    if serializer.is_valid():
        uploaded_file = serializer.validated_data['file']
        
        user_profile = request.user.userprofile
        # Create the Document instance in the database linked to organization & user
        document = Document.objects.create(
            file=uploaded_file,
            original_name=uploaded_file.name,
            status='PENDING',
            organization=user_profile.organization,
            uploaded_by=request.user
        )

        # Copy the uploaded file to the specific folder
        from .document_processor import process_and_copy_document
        process_and_copy_document(document)
        
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_list_view(request):
    user_profile = request.user.userprofile
    documents = Document.objects.filter(organization=user_profile.organization)
    serializer = DocumentSerializer(documents, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def document_detail_view(request, pk):
    try:
        document = Document.objects.get(pk=pk)
    except Document.DoesNotExist:
        return Response(
            {"error": "Document not found."}, 
            status=status.HTTP_404_NOT_FOUND
        )
        
    user_profile = request.user.userprofile
    if document.organization != user_profile.organization:
        return Response(
            {"error": "Access denied. This document belongs to another organization workspace."},
            status=status.HTTP_403_FORBIDDEN
        )
        
    if request.method == 'GET':
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'DELETE':
        # Remove the file from disk if it exists
        files_to_delete = []
        if document.file:
            files_to_delete.append(document.file.path)
        if document.copied_file_path:
            files_to_delete.append(document.copied_file_path)
        if document.extracted_text_path:
            files_to_delete.append(document.extracted_text_path)

        for filepath in files_to_delete:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error removing file {filepath} from disk during deletion: {e}")
                
        document.delete()
        return Response(
            {"message": "Document deleted successfully."},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def document_download_zip_view(request, pk):
    try:
        document = Document.objects.get(pk=pk)
    except Document.DoesNotExist:
        return Response(
            {"error": "Document not found."}, 
            status=status.HTTP_404_NOT_FOUND
        )

    user_profile = request.user.userprofile
    if document.organization != user_profile.organization:
        return Response(
            {"error": "Access denied. This document belongs to another organization workspace."},
            status=status.HTTP_403_FORBIDDEN
        )

    # Gather files to package
    files_to_zip = []
    
    # 1. Add original / copied contract file
    if document.copied_file_path and os.path.exists(document.copied_file_path):
        files_to_zip.append((document.original_name, document.copied_file_path))
    elif document.file and os.path.exists(document.file.path):
        files_to_zip.append((document.original_name, document.file.path))

    # 2. Add extracted text file
    if document.extracted_text_path and os.path.exists(document.extracted_text_path):
        text_filename = os.path.basename(document.extracted_text_path)
        files_to_zip.append((text_filename, document.extracted_text_path))

    if not files_to_zip:
        return Response(
            {"error": "No files associated with this document are available for download."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Create ZIP archive in memory
    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for name, filepath in files_to_zip:
                zip_file.write(filepath, name)
    except Exception as e:
        return Response(
            {"error": f"Error creating ZIP archive: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    zip_buffer.seek(0)
    name_part = os.path.splitext(document.original_name)[0]
    zip_filename = f"{name_part}_package.zip"

    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    return response

