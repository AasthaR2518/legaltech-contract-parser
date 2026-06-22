import os
import fitz

def copy_file_data(uploaded_file_path, destination_folder, new_filename):
    """
    Reads the content of the uploaded file and writes it to a new file in the target folder.
    """
    # Create target folder if it does not exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    destination_path = os.path.join(destination_folder, new_filename)

    try:
        # Read from source file in binary mode
        with open(uploaded_file_path, 'rb') as src:
            file_data = src.read()

        # Write to destination file in binary mode
        with open(destination_path, 'wb') as dest:
            dest.write(file_data)

        return destination_path
    except Exception as e:
        print(f"Error while copying file data: {e}")
        return None

def extract_and_save_text(uploaded_file_path, destination_folder, txt_filename):
    """
    Extracts plain text from the uploaded file (PDF or TXT) and saves it as a new .txt file.
    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    destination_path = os.path.join(destination_folder, txt_filename)
    ext = os.path.splitext(uploaded_file_path)[1].lower()
    text_content = ""

    try:
        if ext == '.pdf':
            # Extract text using PyMuPDF (fitz)
            doc = fitz.open(uploaded_file_path)
            pages_text = []
            for page in doc:
                pages_text.append(page.get_text())
            text_content = "\n--- Page Break ---\n".join(pages_text)
            doc.close()
        elif ext == '.txt':
            # Read plain text directly
            with open(uploaded_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
        else:
            # Fallback for docx or images where text extraction isn't implemented
            text_content = f"Text extraction not supported for format: {ext}"

        # Write to the destination text file
        with open(destination_path, 'w', encoding='utf-8') as f:
            f.write(text_content)

        return destination_path
    except Exception as e:
        print(f"Error extracting text content: {e}")
        return None
