import fitz 
import docx
import io
import requests
from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes
import pytesseract

def extract_text_from_upload(uploaded_file):
    """
    Extracts text from PDF, DOCX, or TXT files.
    """
    file_ext = uploaded_file.name.split('.')[-1].lower()
    text = ""

    try:
        if file_ext == 'pdf':
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
            
            if len(text.strip()) < 50:
                uploaded_file.seek(0)
                try:
                    images = convert_from_bytes(uploaded_file.read())
                    for img in images:
                        text += pytesseract.image_to_string(img)
                except Exception as e:
                    print(f"OCR failed: {e}")

        elif file_ext == 'docx':
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])

        elif file_ext == 'txt':
            text = uploaded_file.read().decode("utf-8")

    except Exception as e:
        return f"Error reading file: {str(e)}"

    return text

def fetch_job_description_from_url(url):
    """
    Fetches text from a URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def create_highlighted_pdf(uploaded_file, keywords):
    """
    Highlights found keywords in the PDF and returns images of pages.
    """
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext != 'pdf':
        return []

    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0) 

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    highlighted_pages = []

    for page_num, page in enumerate(doc):
        for word in keywords:
            quads = page.search_for(word)
            
            for quad in quads:
                highlight = page.add_highlight_annot(quad)
                highlight.set_colors(stroke=(0, 1, 0)) 
                highlight.update()

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        highlighted_pages.append(img_bytes)
        
    return highlighted_pages
