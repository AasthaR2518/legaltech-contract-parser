# LegalTech Contract Parser

This project is an automated legal contract parsing engine built using Django. The goal is to upload PDF contracts (like NDAs or MSAs) and parse them to extract clauses and flag risks automatically.

## Status: Week 2 Completed

Here is what has been implemented so far:

### Week 1: Base Setup & Document Management
- **Django Project Setup**: Configured Django with database settings supporting PostgreSQL and SQLite.
- **Database Models**: Designed and created models (`Document`, `ExtractedClause`, `RiskFlag`).
- **Upload API Endpoint**: Created a REST API (`/api/contracts/upload/`) to handle file uploads.
- **Testing UI Dashboard**: Created a simple HTML template served at `/` to upload and list contracts.

### Week 2: Multi-format Support, Text Extraction & File Actions
- **Multi-format Support**: Expanded upload validations to support PDF, JPG, PNG, Word (DOC/DOCX), and TXT formats.
- **Auto-copy & Text Extraction**: Implemented background processing using PyMuPDF (`fitz`) to copy uploaded files and extract their raw text into separate `.txt` files under `media/copied_contracts/`.
- **Download and Delete Features**: Added file download links and a direct Delete button linked to a backend `DELETE` API endpoint (which cleans up both database records and physical files on disk).
- **Developer UI Enhancements**: Re-styled the dashboard for a clean mid-level developer look with dynamic file-type specific icons.

## Project Structure

- `config/`: Contains main Django settings and URLs.
- `contracts/`: The Django app containing models, views, serializers, URLs, and migrations.
- `templates/index.html`: Dashboard interface for testing the file upload.

## How to Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database**:
   - If using PostgreSQL, copy `.env.example` to `.env` and fill in your database details.
   - If `.env` is not set up, it will automatically use SQLite.

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Start the server**:
   ```bash
   python manage.py runserver
   ```
   Now open `http://127.0.0.1:8000/` in your web browser. You will see the upload dashboard where you can test the PDF file upload.
