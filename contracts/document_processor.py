import os
from datetime import datetime
from .file_helper import copy_file_data, extract_and_save_text

def process_and_copy_document(document):
    """
    Main processor function that prepares paths, copies the file, and extracts text.
    """
    if not document.file or not os.path.exists(document.file.path):
        print(f"File not found for document {document.id}")
        return

    source_path = document.file.path

    # Generate a copy name and a text extraction name with a timestamp
    original_name = document.original_name
    name_part, ext_part = os.path.splitext(original_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    new_filename = f"{name_part}_copy_{timestamp}{ext_part}"
    txt_filename = f"{name_part}_text_{timestamp}.txt"

    # Determine destination folder inside the media directory
    media_root = os.path.dirname(os.path.dirname(source_path))
    destination_folder = os.path.join(media_root, 'copied_contracts')

    # 1. Copy the original uploaded file (PDF, Image, etc.)
    copied_path = copy_file_data(source_path, destination_folder, new_filename)

    # 2. Extract and save text as a .txt file
    txt_path = extract_and_save_text(source_path, destination_folder, txt_filename)

    # Update document status and paths in database
    document.copied_file_path = copied_path
    document.extracted_text_path = txt_path

    analysis_success = False
    if copied_path and txt_path:
        try:
            # Read the extracted text content
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                extracted_text = f.read()
            
            # Run NLP and risk analysis
            from .analyzer import analyze_contract_text
            analysis_success = analyze_contract_text(document, extracted_text)
        except Exception as e:
            print(f"Error during document analysis: {e}")

    if copied_path and txt_path and analysis_success:
        document.status = 'COMPLETED'
        print(f"Successfully created copy, extracted text, and completed analysis of {original_name}")
    else:
        document.status = 'FAILED'
        print(f"Failed to process {original_name}")

    document.save()
