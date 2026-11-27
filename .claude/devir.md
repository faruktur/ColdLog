# Devir Notu

Oturumlar arası tek hatırlatıcı. Kısa tutulur — ayrıntı dokümanlarda, burada sadece kaldığımız yer. Her oturum sonunda üzerine yazılır, geçmiş tutulmaz.

**Tarih:** 2026-11-27

**Nerede kaldık:** Adım 5 (C4 Level 1 + Level 2) bitti. `CLAUDE.md` ve `.claude/` altındaki kural dosyaları kuruldu (core, docs, code, workflow, stack), ilk iki hook yazıldı (`.claude/hooks/guard.js` + `.claude/settings.json`: commit engeli, *Kabul* ADR koruması) — hiçbiri commit edilmedi.

**Sıradaki adım:** Adım 6 — Slice 1 kodu (telemetri ingest → stream processing → asset state → kural tabanlı uyarı). Başlamadan önce kodlama tarafının skill/agent/hook yapısı konuşulacak.

**Açık konular:**
- `.gitignore` → `__pycache__/` eklenmedi; `bote.cpython-314.pyc` repoda duruyor.
- Kural dosyaları eksik/çelişki açısından taranmadı — kullanıldıkça düzeltilecek.
- B-10 (Analytics Database) bilinçli `TBD`, FR-19 netleşmesini bekliyor.
