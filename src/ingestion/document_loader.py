import os
from .pdf_parser import parse_invoice_pdf
from pdf2image import convert_from_path
from .gcloud_ocr import ocr_image
import tempfile

def parse_scanned_pdf(path):
    full_text = ""
    with tempfile.TemporaryDirectory() as tmpdir:
        images = convert_from_path(path, dpi=300, output_folder=tmpdir)
        for i, image in enumerate(images):
            image_path = os.path.join(tmpdir, f"page_{i}.png")
            image.save(image_path)
            text = ocr_image(image_path)
            full_text += f"\n--- Page {i+1} ---\n{text}"
    return {"raw_text": full_text}

def load_document(path, type_hint=None):
    if type_hint == "invoice":
        return parse_invoice_pdf(path)
    elif type_hint == "ocr":
        return parse_scanned_pdf(path)
    else:
        raise ValueError("Unknown document type")
