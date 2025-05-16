import pdfplumber
import re

def parse_invoice_pdf(path):
    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    # Extract metadata
    data = {
        "invoice_no": re.search(r"Invoice No\s*:\s*(\S+)", text).group(1),
        "invoice_date": re.search(r"Invoice Date\s*:\s*(\d{1,2}-[A-Za-z]+-\d{4})", text).group(1),
        "po_no": re.search(r"PO No\s*:\s*(\S+)", text).group(1),
        "customer_name": re.search(r"Customer Name\s*:\s*(.*)", text).group(1).strip(),
        "currency": re.search(r"Currency\s*:\s*(\w+)", text).group(1),
        "total_excl_vat": float(re.search(r"Total Amount \(Excluding VAT\)\s*:\s*(\d+\.\d+)", text).group(1)),
        "total_incl_vat": float(re.search(r"Total Amount \(Including\s+VAT\)\s*:\s*(\d+\.\d+)", text).group(1))
    }

    # Extract item (basic assumption: one row)
    match = re.search(r"(\d+\.00)\s+SET\s+(\d+\.\d+)\s+(\d+\.\d+)", text)
    if match:
        quantity, unit_price, total = map(float, match.groups())
        item_desc = re.search(r"1\s+(.*?)\s+" + re.escape(match.group(1)), text, re.DOTALL).group(1).strip()
        data["items"] = [{
            "description": item_desc,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": total
        }]

    return data
