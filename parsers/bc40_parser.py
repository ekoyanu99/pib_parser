import pdfplumber
import re
import json
import sys

def to_float(val_str):
    if not val_str: return 0.0
    clean = re.sub(r'[^\d\.,]', '', str(val_str))
    if not clean: return 0.0
    
    last_comma = clean.rfind(',')
    last_dot = clean.rfind('.')
    
    if last_comma > last_dot:
        # format Indonesia: 13.000.000,00
        clean = clean.replace('.', '').replace(',', '.')
    else:
        # format US: 53,979,730.00
        clean = clean.replace(',', '')
        
    try: return float(clean)
    except: return 0.0

def to_db_date(date_str):
    if not date_str: return None
    parts = date_str.split('-')
    if len(parts) == 3 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return date_str

def clean_text_stop(text, stop_words):
    if not text: return None
    for word in stop_words:
        if word in text:
            text = text.split(word)[0]
    return text.strip()

def parse_bc40_pdf(pdf_path):
    result = {
        "header": {
            "nomor_pengajuan": None,
            "nomor_pendaftaran": None,
            "tanggal_pendaftaran": None,
            "kantor_pabean": None,
            "kantor_pabean_kode": None,
            "jenis_tpb": None,
            "jenis_transaksi": None,
            
            "pemasok": None,
            "negara_pemasok": None,
            "importir_nama": None,
            "importir_npwp": None,
            "tpb_nama": None,
            "tpb_npwp": None,
            "pengirim_nama": None,
            "pengirim_npwp": None,
            
            "invoice_no": None,
            "invoice_date": None,
            "valuta": None,
            
            "jenis_sarana_pengangkut": None,
            "no_polisi": None,
            "jenis_kemasan": None,
            "jumlah_kemasan": 0.0,
            
            "ndpbm": 0.0,
            "cif_valuta": 0.0,
            "cif_idr": 0.0,
            "harga_penyerahan": 0.0,
            "bruto_kg": 0.0,
            "netto_kg": 0.0,
            
            "bm_ditangguhkan": 0.0,
            "ppn_dilunasi": 0.0,
            "ppn_dibebaskan": 0.0,
            "ppn_tidak_dipungut": 0.0,
            "pph_tidak_dipungut": 0.0,
            "pib_type": "bc40"
        }, 
        "items": [], 
        "documents": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        page1_text = pdf.pages[0].extract_text()
        full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        def get_match(pattern, text, group=1):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(group).strip() if match else None

        # =========================================================================
        # 1. PARSING HEADER BC 4.0
        # =========================================================================
        result["header"]["nomor_pengajuan"] = get_match(r"Nomor\s*Pengajuan\s*:\s*([0-9A-Z]{26})", full_text)
        result["header"]["nomor_pendaftaran"] = get_match(r"Nomor\s*Pendaftaran\s*:\s*(\d{6})", full_text)
        result["header"]["tanggal_pendaftaran"] = to_db_date(get_match(r"Tanggal\s*:\s*(\d{2}-\d{2}-\d{4})", page1_text))

        kantor_raw = get_match(r"A\.\s*KANTOR\s*PABEAN\s*:\s*([^\n]+)", page1_text)
        result["header"]["kantor_pabean"] = clean_text_stop(kantor_raw, ["F. KOLOM", "Nomor"])
        result["header"]["kantor_pabean_kode"] = get_match(r"A\.\s*KANTOR\s*PABEAN[^\n]*?\b(\d{6})\b", page1_text)
        
        result["header"]["jenis_tpb"] = clean_text_stop(get_match(r"B\.\s*JENIS\s*TPB\s*:\s*([^\n]+)", page1_text), ["F. KOLOM", "Nomor"])
        result["header"]["jenis_transaksi"] = clean_text_stop(get_match(r"C\.\s*JENIS\s*TRANSAKSI\s*:\s*([^\n]+)", page1_text), ["D. DATA", "Tanggal"])

        tpb_nama_raw = get_match(r"2\.\s*Nama\s*:\s*([^\n]+)", page1_text)
        result["header"]["tpb_nama"] = clean_text_stop(tpb_nama_raw, ["6. Nama", "7. Alamat", "5. NPWP"])
        result["header"]["tpb_npwp"] = get_match(r"PENGUSAHA\s*TPB[\s\S]*?1\.\s*NPWP\s*:\s*([0-9\.\-]+)", page1_text)
        
        pengirim_nama_raw = get_match(r"6\.\s*Nama\s*:\s*([^\n]+)", page1_text)
        result["header"]["pengirim_nama"] = clean_text_stop(pengirim_nama_raw, ["7. Alamat", "8. NPWP"])
        result["header"]["pengirim_npwp"] = get_match(r"5\.\s*NPWP\s*:\s*([0-9\.\-]+)", page1_text)

        pengangkut_raw = get_match(r"16\.\s*Jenis\s*Sarana\s*Pengangkut\s*([^\n]+)", page1_text)
        result["header"]["jenis_sarana_pengangkut"] = clean_text_stop(pengangkut_raw, ["17. No Polisi", "DATA PERDAGANGAN"])
        nopol_raw = get_match(r"17\.\s*No\s*Polisi\s*([^\n]+)", page1_text)
        result["header"]["no_polisi"] = clean_text_stop(nopol_raw, ["DATA PENGANGKUTAN", "18. Harga"])

        kemasan_raw = get_match(r"22\.\s*Jenis\s*Kemasan\s*([\s\S]*?)23\.", page1_text)
        result["header"]["jenis_kemasan"] = clean_text_stop(kemasan_raw.replace(':', ''), ["24. Jumlah", "Merek"]).strip() if kemasan_raw else None
        result["header"]["jumlah_kemasan"] = to_float(get_match(r"24\.\s*Jumlah\s*Kemasan\s*(\d+)", page1_text))

        result["header"]["harga_penyerahan"] = to_float(get_match(r"18\.\s*Harga\s*Penyerahan[\s\S]*?:\s*([0-9\.,]+)", page1_text))
        result["header"]["bruto_kg"] = to_float(get_match(r"25\.\s*Berat\s*Kotor[\s\n]*([0-9\.,]+)", page1_text))
        result["header"]["netto_kg"] = to_float(get_match(r"26\.\s*Berat\s*Bersih\s*\(Kg\)[\s\n]*([0-9\.,]+)", page1_text))

        result["header"]["ppn_dilunasi"] = to_float(get_match(r"31\.\s*PPN\s*Dilunasi[\s\S]*?Rp\.\s*([0-9\.,]+)", page1_text))
        result["header"]["ppn_dibebaskan"] = to_float(get_match(r"32\.\s*PPN\s*Dibebaskan[\s\S]*?Rp\.\s*([0-9\.,]+)", page1_text))
        result["header"]["ppn_tidak_dipungut"] = to_float(get_match(r"33\.\s*PPN\s*Tidak[\s\S]*?Rp\.\s*([0-9\.,]+)", page1_text))

        # =========================================================================
        # 2. PARSING DOKUMEN PELENGKAP
        # =========================================================================
        doc_types = ["SURAT JALAN", "INVOICE", "PACKING LIST", "B/L", "FAKTUR PAJAK", "KONTRAK", "SKEP"]
        seen_docs = set()

        doc_blocks = re.findall(r"([A-Z\s\/]+)\s*([A-Z0-9\/\.\-]+)\s*(\d{2}-\d{2}-\d{4})", full_text)
        for doc_name, doc_no, doc_date in doc_blocks:
            clean_name = doc_name.strip()
            if any(dt in clean_name for dt in doc_types):
                final_type = next((dt for dt in doc_types if dt in clean_name), clean_name)
                clean_no = doc_no.strip()
                
                identifier = f"{final_type}-{clean_no}"
                if identifier not in seen_docs:
                    seen_docs.add(identifier)
                    result["documents"].append({
                        "jenis_dokumen": final_type,
                        "nomor_dokumen": clean_no,
                        "tanggal_dokumen": to_db_date(doc_date)
                    })

        # =========================================================================
        # 3. PARSING ITEMS BARANG
        # =========================================================================
        split_pattern = r'Pos\s*Tarif\s*/\s*HS\s*:'
        if not re.search(split_pattern, full_text, re.IGNORECASE):
            split_pattern = r'(?=Kode\s*(?:Brg|Barang)\s*:)' 
            
        item_blocks = re.split(split_pattern, full_text, flags=re.IGNORECASE)
        
        for idx, block in enumerate(item_blocks[1:], start=1):
            hs_code_match = re.search(r"^\s*([0-9\.]+)", block)
            hs_code = hs_code_match.group(1).replace('.', '') if hs_code_match else ""
            
            kb_match = re.search(r"Kode\s*(?:Brg|Barang)\s*:?[\r\n\s]*([A-Z0-9\-\_\.\/]+)", block, re.IGNORECASE)
            kode_brg = kb_match.group(1).strip() if kb_match else None
            
            qty_matches = re.findall(r"(\d{1,3}(?:[,\.]\d{3})*[,\.]\d{2,4})\b", block)
            qty = to_float(qty_matches[0]) if qty_matches else 0.0

            unit_match = re.search(r"-\s*([A-Z]{2,4})\b", block)
            satuan = unit_match.group(1).strip() if unit_match else ""
            
            if not satuan: 
                units = re.findall(r"\b([A-Z]{2,4})\b", block)
                valid = [u for u in units if u not in ["USD", "CNY", "IDR", "SGD", "EUR", "JPY", "PO", "DTG", "TID", "BM", "BMT", "PPN", "PPH", "CT", "PX", "Rp"]]
                satuan = valid[-1] if valid else ""

            harga_matches = re.findall(r"(\d{1,3}(?:[,\.]\d{3})*[,\.]\d{2})", block)
            harga = to_float(harga_matches[-1]) if harga_matches else 0.0

            result["items"].append({
                "pos": idx,
                "hs_code": hs_code,
                "kode_barang": kode_brg,
                "uraian_raw": block[:120].replace('\n', ' ').strip(),
                "negara_asal": result["header"]["negara_pemasok"],
                "jumlah": qty,
                "satuan": satuan,
                "cif_item": 0.0,                
                "harga_penyerahan": harga      
            })

    return result

if __name__ == "__main__":
    file_pdf = sys.argv[1] if len(sys.argv) > 1 else "sample.pdf"
    print(json.dumps(parse_bc40_pdf(file_pdf), indent=2))