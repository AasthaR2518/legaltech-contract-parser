from rest_framework import serializers
from .models import Document, ExtractedClause, RiskFlag

class RiskFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskFlag
        fields = ['id', 'risk_level', 'reason', 'suggested_fix']


class ExtractedClauseSerializer(serializers.ModelSerializer):
    risk_flags = RiskFlagSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractedClause
        fields = ['id', 'clause_type', 'raw_text', 'page_number', 'created_at', 'risk_flags']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'original_name', 'uploaded_at', 'status']
        read_only_fields = ['id', 'original_name', 'uploaded_at', 'status']


class DocumentDetailSerializer(serializers.ModelSerializer):
    clauses = ExtractedClauseSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'file', 'original_name', 'uploaded_at', 'status', 'clauses']


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        # Validate that the file is not empty
        if not value:
            raise serializers.ValidationError("No file was uploaded.")

        # Validate file size (limit to 10 MB)
        max_size = 10 * 1024 * 1024 # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError(f"File size exceeds the 10MB limit (uploaded size: {value.size / (1024*1024):.2f}MB).")

        # Validate extension
        filename = value.name
        if not filename.lower().endswith('.pdf'):
            raise serializers.ValidationError("Invalid file type. Only PDF documents are allowed.")

        # Validate MIME type
        content_type = value.content_type
        if content_type != 'application/pdf':
            raise serializers.ValidationError("File content must be a PDF application/pdf.")

        return value
