# LegalTech Contract Parser

This project is an automated legal contract parsing engine built using Django. The goal is to upload PDF contracts (like NDAs or MSAs) and parse them to extract clauses and flag risks automatically.

## Status: Week 1 Setup Completed

We have set up the basic project structure and database configuration. Here is what has been implemented so far:

- **Django Project Setup**: Configured Django with PostgreSQL database settings (falls back to SQLite for local development if PostgreSQL credentials are not provided in env).
- **Database Models**: Designed and created three models:
  - `Document`: Stores metadata and status of the uploaded file.
  - `ExtractedClause`: For storing clauses found in the document.
  - `RiskFlag`: To flag any risks in the clauses with details like risk level and suggested fix.
- **Upload API Endpoint**: Created a REST API (`/api/contracts/upload/`) that accepts PDF uploads. It validates that the file is indeed a PDF and is not larger than 10MB.
- **Testing UI Dashboard**: Created a simple HTML template served at the home URL (`/`) which provides a drag-and-drop box to upload contracts and shows the list of uploaded files.

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
