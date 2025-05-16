from src.ingestion.document_loader import load_document
from src.ingestion.document_loader import parse_scanned_pdf

invoice_data = load_document("data/invoice.PDF", type_hint="invoice")
print("Invoice Data:", invoice_data)

result = parse_scanned_pdf("data/truck consignment, exit certificate, delivery note.pdf")
print(result["raw_text"][:1000])
