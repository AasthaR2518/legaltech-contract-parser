from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient
from .models import Document

class DocumentUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.upload_url = reverse('document-upload')

    def test_upload_valid_pdf_success(self):
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        uploaded_file = SimpleUploadedFile(
            name="test_contract.pdf",
            content=pdf_content,
            content_type="application/pdf"
        )

        response = self.client.post(
            self.upload_url,
            {'file': uploaded_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['original_name'], "test_contract.pdf")
        self.assertEqual(response.data['data']['status'], "PENDING")
        
        # Verify it was saved to the database
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.original_name, "test_contract.pdf")
        self.assertTrue(doc.file.name.startswith("contracts/test_contract"))

    def test_upload_invalid_extension_fails(self):
        # Create a mock zip file
        zip_content = b"Mock zip content"
        uploaded_file = SimpleUploadedFile(
            name="test_contract.zip",
            content=zip_content,
            content_type="application/zip"
        )

        response = self.client.post(
            self.upload_url,
            {'file': uploaded_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
        self.assertEqual(Document.objects.count(), 0)

    def test_upload_valid_txt_success(self):
        # Create a mock txt file
        txt_content = b"This is a plain text file."
        uploaded_file = SimpleUploadedFile(
            name="test_contract.txt",
            content=txt_content,
            content_type="text/plain"
        )

        response = self.client.post(
            self.upload_url,
            {'file': uploaded_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()
        self.assertEqual(doc.original_name, "test_contract.txt")

    def test_upload_empty_fails(self):
        response = self.client.post(
            self.upload_url,
            {},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)

    def test_upload_exceeds_size_fails(self):
        # Create a mock PDF file larger than 10MB (11MB here)
        large_content = b"%" * (11 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile(
            name="large_contract.pdf",
            content=large_content,
            content_type="application/pdf"
        )

        response = self.client.post(
            self.upload_url,
            {'file': uploaded_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', response.data)
        self.assertIn("exceeds the 10MB limit", response.data['file'][0])
        self.assertEqual(Document.objects.count(), 0)

