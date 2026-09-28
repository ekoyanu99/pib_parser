# PIB Parser

Parser PDF untuk dokumen kepabeanan Indonesia **BC 2.3** dan **BC 4.0**. Proyek ini mengekstrak data dokumen CEISA menjadi JSON terstruktur yang dapat langsung dikonsumsi oleh aplikasi Python, Laravel, atau backend berbasis PHP lainnya.

## Fitur Utama

- Parser khusus untuk dokumen BC 2.3 dan BC 4.0.
- Deteksi tipe dokumen otomatis melalui nama file.
- Output JSON terpadu untuk header, item barang, dan dokumen pendukung.
- Ekstraksi data dari tabel PDF yang memiliki line break dan format teks tidak konsisten.
- Dapat dipanggil dari Laravel menggunakan Symfony Process.

## Struktur Proyek

```text
pib_parser/
├── main.py
├── parsers/
│   ├── __init__.py
│   ├── bc23_parser.py
│   └── bc40_parser.py
├── samples/
├── requirements.txt
└── README.md
```

## Persyaratan

- Python 3.9 atau lebih baru
- `pip`
- File PDF dokumen BC 2.3 atau BC 4.0

## Instalasi

```bash
git clone <repository-url>
cd pib_parser

python -m venv .venv
```

Aktifkan virtual environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

Install dependensi:

```bash
pip install -r requirements.txt
```

## Penggunaan

### CLI Terpadu

Gunakan `main.py` untuk memilih tipe dokumen secara eksplisit atau membiarkan parser mendeteksinya dari nama file:

```bash
# Deteksi otomatis
python main.py "path/to/document.pdf"

# Pilih parser BC 2.3
python main.py "path/to/document.pdf" --type BC23

# Pilih parser BC 4.0
python main.py "path/to/document.pdf" --type BC40
```

Output berhasil dicetak ke `stdout` sebagai JSON. Jika terjadi kesalahan, proses mengembalikan exit code `1` dan mencetak objek error:

```json
{
  "status": "error",
  "message": "..."
}
```

### Menjalankan Parser Secara Langsung

Kedua parser juga dapat dijalankan langsung:

```bash
python parsers/bc23_parser.py "path/to/bc23-document.pdf"
python parsers/bc40_parser.py "path/to/bc40-document.pdf"
```

## Format Output

Output menggunakan tiga bagian utama: `header`, `items`, dan `documents`.

```json
{
  "header": {
    "nomor_pengajuan": null,
    "nomor_pendaftaran": "051579",
    "tanggal_pendaftaran": "2020-10-26",
    "kantor_pabean": null,
    "kantor_pabean_kode": null,
    "jenis_tpb": null,
    "jenis_transaksi": null,
    "pemasok": "KGH KUNSTSTOFFGESELLSCHAFT MBH",
    "negara_pemasok": null,
    "importir_nama": null,
    "importir_npwp": "93.317.274.4-418.000",
    "tpb_nama": null,
    "tpb_npwp": null,
    "pengirim_nama": null,
    "pengirim_npwp": null,
    "invoice_no": "09-043-20",
    "invoice_date": "2020-09-23",
    "valuta": "USD",
    "jenis_sarana_pengangkut": "TEAL HUNTER 015S SINGAPORE SG US DOLLAR USD 14.768,0000",
    "no_polisi": null,
    "jenis_kemasan": null,
    "jumlah_kemasan": 0.0,
    "ndpbm": 0.0,
    "cif_valuta": 0.0,
    "cif_idr": 0.0,
    "harga_penyerahan": 0.0,
    "bruto_kg": 465.0,
    "netto_kg": 199.7,
    "bm_ditangguhkan": 500.0,
    "ppn_dilunasi": 0.0,
    "ppn_dibebaskan": 0.0,
    "ppn_tidak_dipungut": 0.0,
    "pph_tidak_dipungut": 0.0,
    "pib_type": "bc23",
    "jenis_bc": "BC23"
  },
  "items": [
    {
      "pos": 1,
      "hs_code": "39151090",
      "kode_barang": "BB000002",
      "uraian_raw": "39151090 11 (BAHAN GERMANY BM 5,00%,100,00%TG - 199.700,0000 56.914,50 Kode Brg : BB000002 BAKU / (DE) PPH 2,50%,100,00",
      "negara_asal": "GERMANY",
      "jumlah": 0.0,
      "satuan": "PPJK",
      "cif_item": 199.7,
      "harga_penyerahan": 0.0
    },
    {
      "pos": 2,
      "hs_code": "39151090",
      "kode_barang": "BB000002",
      "uraian_raw": "39151090 11 (BAHAN GERMANY BM 5,00%,100,00%TG - 199.700,0000 56.914,50 Kode Brg : BB000002 BAKU / (DE) PPH 2,50%,100,00",
      "negara_asal": "GERMANY",
      "jumlah": 0.0,
      "satuan": "PPJK",
      "cif_item": 199.7,
      "harga_penyerahan": 0.0
    },
    {
      "pos": 3,
      "hs_code": "39151090",
      "kode_barang": "BB000002",
      "uraian_raw": "39151090 11 (BAHAN GERMANY BM 5,00%,100,00%TG - 199.700,0000 56.914,50 Kode Brg : BB000002 BAKU / (DE) PPH 2,50%,100,00",
      "negara_asal": "GERMANY",
      "jumlah": 20.2458,
      "satuan": "TPB",
      "cif_item": 5.2,
      "harga_penyerahan": 0.0
    }
  ],
  "documents": [
    {
      "jenis_dokumen": "INVOICE",
      "nomor_dokumen": "09-043-20",
      "tanggal_dokumen": "2020-09-23"
    },
    {
      "jenis_dokumen": "PACKING LIST",
      "nomor_dokumen": "09-043-20",
      "tanggal_dokumen": "2020-09-23"
    },
    {
      "jenis_dokumen": "B/L",
      "nomor_dokumen": "ONEYHAMAA5206400",
      "tanggal_dokumen": "2020-09-25"
    },
    {
      "jenis_dokumen": "SKEP/KEPUTUSAN",
      "nomor_dokumen": "ONEYHAMAA5206400",
      "tanggal_dokumen": "2020-09-25"
    },
    {
      "jenis_dokumen": "SKEP",
      "nomor_dokumen": "09-043-20",
      "tanggal_dokumen": "2020-09-23"
    },
    {
      "jenis_dokumen": "AWB",
      "nomor_dokumen": "ONEYHAMAA5206400",
      "tanggal_dokumen": "2020-09-25"
    },
    {
      "jenis_dokumen": "SURAT PERSETUJUAN",
      "nomor_dokumen": "04.PI-05.20.2458",
      "tanggal_dokumen": "2020-07-29"
    },
    {
      "jenis_dokumen": "BC 1.1",
      "nomor_dokumen": "004259",
      "tanggal_dokumen": "2020-10-23"
    }
  ]
}
```

## Integrasi Laravel

Parser dapat dipanggil dari service Laravel menggunakan `Symfony\Component\Process\Process`:

```php
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;

public function parsePdf(string $pdfPath, string $docType = 'BC23'): array
{
    $scriptName = $docType === 'BC40'
        ? 'bc40_parser.py'
        : 'bc23_parser.py';

    $process = new Process([
        'python',
        base_path("pib_parser/parsers/{$scriptName}"),
        $pdfPath,
    ]);
    $process->run();

    if (!$process->isSuccessful()) {
        throw new ProcessFailedException($process);
    }

    return json_decode($process->getOutput(), true) ?? [];
}
```

Setelah parsing, data dapat disimpan ke model Eloquent:

```php
$parsedData = $this->parserService->parsePdf($filePath, 'BC23');

$header = AjuHeader::create(array_merge(
    $parsedData['header'],
    ['jenis_bc' => 'BC23']
));

$header->items()->createMany($parsedData['items'] ?? []);
$header->documents()->createMany($parsedData['documents'] ?? []);
```

## Catatan

- Format PDF yang berbeda dapat menghasilkan tingkat kelengkapan data yang berbeda.
- Pastikan path PDF dapat dibaca oleh proses Python ketika dipanggil dari Laravel.
- Nilai tanggal pada output menggunakan format `YYYY-MM-DD` jika berhasil diekstrak.

## Lisensi

Proyek ini tersedia di bawah lisensi MIT.
