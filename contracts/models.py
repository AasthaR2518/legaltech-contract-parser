from django.db import models
import uuid

class Document(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='contracts/')
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    copied_file_path = models.CharField(max_length=500, null=True, blank=True)
    extracted_text_path = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.original_name} ({self.status})"


class ExtractedClause(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='clauses')
    clause_type = models.CharField(max_length=100) # e.g., 'Governing Law', 'Limitation of Liability'
    raw_text = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number']

    def __str__(self):
        return f"{self.clause_type} (Page {self.page_number or 'Unknown'})"


class RiskFlag(models.Model):
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clause = models.ForeignKey(ExtractedClause, on_delete=models.CASCADE, related_name='risk_flags')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='LOW')
    reason = models.TextField()
    suggested_fix = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.risk_level}] Risk on {self.clause.clause_type}"

