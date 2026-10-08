# Progress: Transaksi Penjualan + Pengadaan Stok

**Project:** `/home/choirulhaq/venvProject/testopencode/`
**Branch:** master (⚠️ **JANGAN COMMIT** sampai user selesai test di host)

---

## Aturan Sesi Ini

> **User: "Sebelum saya katakan ok jangan dicommit di git dulu, perlu saya test
> di host dulu sebagai development"**

**Artinya:**
- Semua perubahan **hanya di host**, tidak ada `git commit` / `git push`
- `crud.choirulhaq.com` **tidak boleh berubah** — dia auto-deploy dari GitHub
- Selesai coding → minta user test di host → **baru** commit setelah user bilang ok

---

## Session 2026-10-06 — Planning

### Yang dikerjakan

- [x] Audit project testopencode (1.221 baris app.py, 27 route, 5 tabel, 23 template)
- [x] Pahami pola RBAC (`@has_permission('menu', 'action')`, permissions JSON)
- [x] Pahami seed yang ada (kategori, role admin, user admin)
- [x] Desain skema kartu stok (ledger, bukan kolom di `items`)
- [x] Desain HPP moving average + snapshot di baris penjualan
- [x] Tulis `task_plan.md` + `findings.md`

### Belum dikerjakan

- [ ] Fase 1 — implementasi skema DB
- [ ] Fase 2 — supplier + pembelian
- [ ] Fase 3 — penjualan + validasi
- [ ] Fase 4 — kartu stok + laporan
- [ ] Fase 5 — RBAC menu baru
- [ ] Fase 6 — seed data awal
- [ ] Fase 7 — test + verifikasi

### Test Results

_(belum ada — belum ada kode diubah)_

### Catatan

- Fase 1 **ditahan** sampai desain skema disetujui user
- Semua test lama (`test_enhancement.py`, `verify_security.py`) harus tetap lolos

---

## Log Sesi

| Tanggal | Kegiatan | Hasil |
|---|---|---|
| 2026-10-06 | Penilaian skala + persetujuan Opsi B | ✅ planning dibuat |
