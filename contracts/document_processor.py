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

    if copied_path:
        print(f"Successfully created a copy of {original_name} at: {copied_path}")
    else:
        print(f"Failed to copy {original_name}")

    if txt_path:
        print(f"Successfully extracted text of {original_name} to: {txt_path}")
    else:
        print(f"Failed to extract text of {original_name}")
