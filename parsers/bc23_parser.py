import pdfplumber
import re
import json
import sys

def to_float(val_str):
    if not val_str: return 0.0
    clean = re.sub(r'[^\d\.,]', '', val_str)
    if not clean: return 0.0
    clean = clean.replace(',', '')
    try: return float(clean)
    except: return 0.0

def to_db_date(date_str):
    if not date_str: return None
    parts = date_str.split('-')
    if len(parts) == 3 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return date_str

def parse_bc23_pdf(pdf_path):
    
    COUNTRY_PATTERN = r"\b(CHINA|KOREA(?:,\s*REPUBLIC\s*OF)?|JAPAN|TAIWAN|SINGAPORE|MALAYSIA|THAILAND|VIETNAM|INDIA|GERMANY|UNITED\s*STATES|AUSTRALIA|ITALY|FRANCE)\b"
    
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
            "pib_type": "bc23"
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
        # 1. PARSING HEADER BC 2.3
        # =========================================================================
        result["header"]["nomor_pengajuan"] = get_match(r"\b([0-9]{6}[A-Z0-9]{20})\b", full_text)
        
        nopen_match = re.search(r"Nomor Pendaftaran[\r\n\s]+[0-9A-Z]{26}[\r\n\s]+(\d{6})", full_text, re.IGNORECASE)
        result["header"]["nomor_pendaftaran"] = nopen_match.group(1) if nopen_match else get_match(r"No\.\s*dan\s*Tgl\.[\s\S]{1,40}?\b(\d{6})\b", page1_text)

        tgl_match = re.search(r"\b(\d{2}-\d{2}-\d{4})\b", page1_text)
        result["header"]["tanggal_pendaftaran"] = to_db_date(tgl_match.group(1) if tgl_match else None)

        result["header"]["kantor_pabean_kode"] = get_match(r"Kantor\s*Pabean\s*:[^\n]*?\b(\d{6})\b", page1_text)
        kantor_raw = get_match(r"Kantor\s*Pabean\s*:\s*([^\n]+)", page1_text)
        if kantor_raw:
            result["header"]["kantor_pabean"] = re.sub(r'\d{6}', '', kantor_raw).strip()
            
        pemasok_block = get_match(r"PEMASOK\s*1\.\s*Nama,\s*Alamat,\s*Negara\s*:\s*([\s\S]*?)(?=IMPORTIR|Identitas|\n\s*\n)", page1_text)
        if pemasok_block:
            clean_pemasok = re.split(r'\bNo\.', pemasok_block)[0].strip()
            lines = [line.strip() for line in clean_pemasok.split('\n') if line.strip()]
            
            result["header"]["pemasok"] = lines[0] if lines else None
            
            country_matches = re.findall(COUNTRY_PATTERN, clean_pemasok, re.IGNORECASE)
            if country_matches:
                result["header"]["negara_pemasok"] = country_matches[-1].strip().upper()

        pemasok_raw = get_match(r"PEMASOK\s*1\.\s*Nama,\s*Alamat,\s*Negara\s*:\s*([^\n]+)", page1_text)
        result["header"]["pemasok"] = re.split(r'\bNo\.', pemasok_raw)[0].strip() if pemasok_raw else None

        importir_nama_raw = get_match(r"NITKU\s*:\s*[0-9]+\s*:\s*([^\n]+)", page1_text)
        if importir_nama_raw:
             result["header"]["importir_nama"] = re.split(r'JL\.|JALAN', importir_nama_raw, flags=re.IGNORECASE)[0].strip()
        
        result["header"]["importir_npwp"] = get_match(r"Identitas\s*\(NPWP\)\s*:\s*([0-9\.\-]+)", full_text)
        
        result["header"]["invoice_no"] = get_match(r"16\.\s*Invoice\s*:\s*([^\n\s]+)", page1_text)
        result["header"]["invoice_date"] = to_db_date(get_match(r"16\.\s*Invoice.*?Tgl\.\s*(\d{2}-\d{2}-\d{4})", page1_text))
        result["header"]["valuta"] = get_match(r"\b(USD|CNY|IDR|SGD|EUR|JPY)\b", page1_text)
        
        pengangkut_raw = get_match(r"12\.\s*Nama\s*Sarana\s*Pengangkut[^\n]*\n([^\n]+)", page1_text)
        result["header"]["jenis_sarana_pengangkut"] = pengangkut_raw.split('/')[0].strip() if pengangkut_raw else None
        
        result["header"]["jumlah_kemasan"] = to_float(get_match(r"30\.\s*Jumlah\s*dan\s*Jenis\s*Kemasan\s*[\r\n\s]*(\d+)", page1_text))

        result["header"]["ndpbm"] = to_float(get_match(r"24\.\s*NDPBM\s*:\s*([0-9\.,]+)", page1_text))
        result["header"]["cif_valuta"] = to_float(get_match(r"28\.\s*Nilai\s*CIF\s*:\s*[\r\n\s]*([0-9\.,]{4,})", page1_text))
        result["header"]["cif_idr"] = to_float(get_match(r"Rp\.\s*([0-9\.,]+)", page1_text))
        result["header"]["bruto_kg"] = to_float(get_match(r"31\.\s*Berat\s*Kotor\s*\(Kg\)\s*:\s*([0-9\.,]+)", page1_text))
        result["header"]["netto_kg"] = to_float(get_match(r"32\.\s*Berat\s*Bersih\s*\(Kg\)\s*:\s*([0-9\.,]+)", page1_text))

        result["header"]["bm_ditangguhkan"] = to_float(get_match(r"BM\s*([\d\.,]+)", page1_text))
        result["header"]["ppn_tidak_dipungut"] = to_float(get_match(r"PPN\s*[\d\.,]+\s*[\d\.,]+\s*([\d\.,]+)", page1_text))
        result["header"]["pph_tidak_dipungut"] = to_float(get_match(r"PPh\s*[\d\.,]+\s*[\d\.,]+\s*([\d\.,]+)", page1_text))

        # =========================================================================
        # 2. PARSING DOKUMEN PELENGKAP (UPDATED)
        # =========================================================================
        doc_types = ["INVOICE", "PACKING LIST", "B/L", "KEPUTUSAN", "SKEP", "AWB", "SURAT PERSETUJUAN", "BILL OF LADING", "BC 1.1"]
        seen_docs = set()

        for doc_type in doc_types:
            matches = re.findall(rf"\b({doc_type})\b([\s\S]{{1,250}}?)(\d{{2}}-\d{{2}}-\d{{4}})", full_text, re.IGNORECASE)
            
            for m in matches:
                raw_gap = m[1]
                
                candidates = re.findall(r'[A-Z0-9\./\-]{3,}', raw_gap.upper())
                
                ignore_words = [
                    "TGL", "TANGGAL", "NOMOR", "DOKUMEN", "JENIS", "KEPUTUSAN", 
                    "PENETAPAN", "TEMPAT", "SEBAGAI", "KAWASAN", "BERIKAT", "DAN",
                    "PEMBERIAN", "IZIN", "PENYELENGGARA", "IMPOR", "DEP", "DAG",
                    "SURAT", "PERSETUJUAN", "KEMENTERIAN", "PERDAGANGAN"
                ]
                
                valid_candidates = [c for c in candidates if not any(iw in c for iw in ignore_words)]
                
                if valid_candidates:
                    clean_no = valid_candidates[-1]
                else:
                    clean_no = re.sub(r'[\s\|\n:]+', '', raw_gap)
                    clean_no = re.sub(r'Tgl\.?', '', clean_no, flags=re.IGNORECASE)

                if clean_no and len(clean_no) <= 40:
                    jenis_dok = doc_type.upper()
                    if jenis_dok == "KEPUTUSAN": 
                        jenis_dok = "SKEP/KEPUTUSAN"
                        
                    identifier = f"{jenis_dok}-{clean_no}"
                    if identifier not in seen_docs:
                        seen_docs.add(identifier)
                        result["documents"].append({
                            "jenis_dokumen": jenis_dok,
                            "nomor_dokumen": clean_no,
                            "tanggal_dokumen": to_db_date(m[2])
                        })

        # =========================================================================
        # 3. PARSING ITEMS BARANG
        # =========================================================================
        item_blocks = re.split(r'Pos\s*Tarif\s*/\s*HS\s*:', full_text, flags=re.IGNORECASE)
        
        for idx, block in enumerate(item_blocks[1:], start=1):
            hs_code_match = re.search(r"^\s*([0-9\.]+)", block)
            hs_code = hs_code_match.group(1).replace('.', '') if hs_code_match else ""
            
            kb_match = re.search(r"Kode\s*(?:Brg|Barang)\s*:?[\r\n\s]*([A-Z0-9\-\_\.\/]+)", block, re.IGNORECASE)
            kode_brg = kb_match.group(1).strip() if kb_match else None
            
            negara_item_match = re.search(rf"({COUNTRY_PATTERN}\s*(?:\([A-Z]{{2}}\))?)", block, re.IGNORECASE)
            
            if negara_item_match:
                negara_item = negara_item_match.group(1).strip().upper()
            else:
                negara_item = result["header"]["negara_pemasok"]
            
            qty_matches = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{4})\b", block)
            qty = to_float(qty_matches[0]) if qty_matches else 0.0

            unit_match = re.search(r"-\s*([A-Z]{2,4})\b", block)
            satuan = unit_match.group(1).strip() if unit_match else ""
            
            if satuan in ["DTG", "TID", ""]: 
                units = re.findall(r"\b([A-Z]{2,4})\b", block)
                valid = [u for u in units if u not in ["USD", "CNY", "IDR", "SGD", "EUR", "JPY", "PO", "DTG", "TID", "BM", "BMT", "PPN", "PPH", "CT", "PX", "CIF"]]
                satuan = valid[-1] if valid else ""

            cif_matches = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2})", block)
            cif_item = to_float(cif_matches[-1]) if cif_matches else 0.0

            result["items"].append({
                "pos": idx,
                "hs_code": hs_code,
                "kode_barang": kode_brg,
                "uraian_raw": block[:120].replace('\n', ' ').strip(),
                "negara_asal": negara_item,
                "jumlah": qty,
                "satuan": satuan,
                "cif_item": cif_item,
                "harga_penyerahan": 0.0, 
            })

    return result

if __name__ == "__main__":
    file_pdf = sys.argv[1] if len(sys.argv) > 1 else "sample_bc23.pdf"
    print(json.dumps(parse_bc23_pdf(file_pdf), indent=2))