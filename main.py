import sys
import json
import argparse
from parsers.bc23_parser import parse_bc23_pdf
from parsers.bc40_parser import parse_bc40_pdf

def main():
    parser = argparse.ArgumentParser(description="PIB & Customs Document PDF Parser (BC 2.3 & BC 4.0)")
    parser.add_argument("pdf_path", help="Path ke file PDF Bea Cukai")
    parser.add_argument(
        "--type", 
        choices=["BC23", "BC40", "auto"], 
        default="auto", 
        help="Jenis dokumen BC (BC23, BC40, atau auto-detect)"
    )

    args = parser.parse_args()
    pdf_path = args.pdf_path
    doc_type = args.type.upper()

    # Deteksi otomatis jenis BC berdasarkan nama file jika set ke 'auto'
    if doc_type == "AUTO":
        if "40-" in pdf_path.lower() or "bc40" in pdf_path.lower():
            doc_type = "BC40"
        else:
            doc_type = "BC23"

    try:
        if doc_type == "BC40":
            result = parse_bc40_pdf(pdf_path)
            result["header"]["jenis_bc"] = "BC40"
        else:
            result = parse_bc23_pdf(pdf_path)
            result["header"]["jenis_bc"] = "BC23"

        print(json.dumps(result, indent=2))
    except Exception as e:
        error_res = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_res, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()