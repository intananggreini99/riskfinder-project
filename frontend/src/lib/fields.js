/**
 * Skema 23 fitur input model Credit Risk (dataset Default of Credit Card Clients).
 * Urutan & tipe identik dengan CreditInput pada FastAPI (Step 18 notebook).
 *
 * Catatan: kunci PAY mengikuti dataset asli (PAY_0, PAY_2..PAY_6 — tanpa PAY_1).
 */

export const SEX_OPTS = [
  { value: 1, label: 'Laki-laki' },
  { value: 2, label: 'Perempuan' },
]

export const EDUCATION_OPTS = [
  { value: 1, label: 'Pascasarjana' },
  { value: 2, label: 'Sarjana' },
  { value: 3, label: 'SMA' },
  { value: 4, label: 'Lainnya' },
]

export const MARRIAGE_OPTS = [
  { value: 1, label: 'Menikah' },
  { value: 2, label: 'Lajang' },
  { value: 3, label: 'Lainnya' },
]

// Status pembayaran: -2 tanpa konsumsi, -1 lunas tepat waktu, 0 pakai kredit bergulir,
// 1..9 = telat n bulan.
export const PAY_OPTS = [
  { value: -2, label: '-2 · Tanpa transaksi' },
  { value: -1, label: '-1 · Lunas tepat waktu' },
  { value: 0, label: '0 · Kredit bergulir' },
  { value: 1, label: '+1 · Telat 1 bulan' },
  { value: 2, label: '+2 · Telat 2 bulan' },
  { value: 3, label: '+3 · Telat 3 bulan' },
  { value: 4, label: '+4 · Telat 4 bulan' },
  { value: 5, label: '+5 · Telat 5 bulan' },
  { value: 6, label: '+6 · Telat 6 bulan' },
  { value: 7, label: '+7 · Telat 7 bulan' },
  { value: 8, label: '+8 · Telat 8 bulan' },
]

const billMonths = ['September', 'Agustus', 'Juli', 'Juni', 'Mei', 'April']

/** Kelompok fitur untuk tampilan form yang rapi (prinsip Spacing & Balance). */
export const FIELD_GROUPS = [
  {
    id: 'profil',
    title: 'Profil & Kredit',
    desc: 'Identitas peminjam dan plafon kredit.',
    fields: [
      { key: 'LIMIT_BAL', label: 'Plafon Kredit (LIMIT_BAL)', type: 'number', unit: 'NT$', placeholder: 'mis. 200000', min: 0 },
      { key: 'AGE', label: 'Usia (AGE)', type: 'number', unit: 'tahun', placeholder: 'mis. 35', min: 18, max: 100 },
      { key: 'SEX', label: 'Jenis Kelamin (SEX)', type: 'select', options: SEX_OPTS },
      { key: 'EDUCATION', label: 'Pendidikan (EDUCATION)', type: 'select', options: EDUCATION_OPTS },
      { key: 'MARRIAGE', label: 'Status Pernikahan (MARRIAGE)', type: 'select', options: MARRIAGE_OPTS },
    ],
  },
  {
    id: 'status',
    title: 'Riwayat Status Pembayaran',
    desc: 'Status keterlambatan 6 bulan terakhir (April–September 2005).',
    fields: [
      { key: 'PAY_0', label: 'PAY_0 · September', type: 'select', options: PAY_OPTS },
      { key: 'PAY_2', label: 'PAY_2 · Agustus', type: 'select', options: PAY_OPTS },
      { key: 'PAY_3', label: 'PAY_3 · Juli', type: 'select', options: PAY_OPTS },
      { key: 'PAY_4', label: 'PAY_4 · Juni', type: 'select', options: PAY_OPTS },
      { key: 'PAY_5', label: 'PAY_5 · Mei', type: 'select', options: PAY_OPTS },
      { key: 'PAY_6', label: 'PAY_6 · April', type: 'select', options: PAY_OPTS },
    ],
  },
  {
    id: 'tagihan',
    title: 'Jumlah Tagihan (BILL_AMT)',
    desc: 'Nominal tagihan bulanan dalam NT$.',
    fields: billMonths.map((m, i) => ({
      key: `BILL_AMT${i + 1}`,
      label: `BILL_AMT${i + 1} · ${m}`,
      type: 'number',
      unit: 'NT$',
      placeholder: '0',
    })),
  },
  {
    id: 'pembayaran',
    title: 'Jumlah Pembayaran (PAY_AMT)',
    desc: 'Nominal pembayaran bulanan dalam NT$.',
    fields: billMonths.map((m, i) => ({
      key: `PAY_AMT${i + 1}`,
      label: `PAY_AMT${i + 1} · ${m}`,
      type: 'number',
      unit: 'NT$',
      placeholder: '0',
      min: 0,
    })),
  },
]

/** Daftar seluruh key fitur (urutan kanonik). */
export const ALL_KEYS = FIELD_GROUPS.flatMap((g) => g.fields.map((f) => f.key))

/** Contoh data peminjam (auto-fill untuk demo / uji cepat). */
export const SAMPLE_BORROWER = {
  LIMIT_BAL: 200000, SEX: 2, EDUCATION: 2, MARRIAGE: 1, AGE: 35,
  PAY_0: 0, PAY_2: 0, PAY_3: 0, PAY_4: 0, PAY_5: 0, PAY_6: 0,
  BILL_AMT1: 38000, BILL_AMT2: 41000, BILL_AMT3: 39500,
  BILL_AMT4: 30000, BILL_AMT5: 25000, BILL_AMT6: 20000,
  PAY_AMT1: 4000, PAY_AMT2: 3500, PAY_AMT3: 3000,
  PAY_AMT4: 2500, PAY_AMT5: 2000, PAY_AMT6: 1800,
}

export const SAMPLE_RISKY = {
  LIMIT_BAL: 20000, SEX: 1, EDUCATION: 3, MARRIAGE: 2, AGE: 24,
  PAY_0: 2, PAY_2: 2, PAY_3: 2, PAY_4: 2, PAY_5: 2, PAY_6: 2,
  BILL_AMT1: 19000, BILL_AMT2: 18500, BILL_AMT3: 19500,
  BILL_AMT4: 19800, BILL_AMT5: 19200, BILL_AMT6: 18800,
  PAY_AMT1: 0, PAY_AMT2: 700, PAY_AMT3: 0,
  PAY_AMT4: 800, PAY_AMT5: 0, PAY_AMT6: 0,
}
