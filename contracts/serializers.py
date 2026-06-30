import os
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
        fields = ['id', 'file', 'original_name', 'uploaded_at', 'status', 'contracting_parties']
        read_only_fields = ['id', 'original_name', 'uploaded_at', 'status', 'contracting_parties']


class DocumentDetailSerializer(serializers.ModelSerializer):
    clauses = ExtractedClauseSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'file', 'original_name', 'uploaded_at', 'status', 'contracting_parties', 'clauses']


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        # File size check (limit to 10 MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds the 10MB limit.")

        # File extension check
        ext = os.path.splitext(value.name)[1].lower()
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt']
        if ext not in allowed_extensions:
            raise serializers.ValidationError("Invalid file type. Only PDF, JPG, PNG, DOC/DOCX, and TXT files are allowed.")

        return value