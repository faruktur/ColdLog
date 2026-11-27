# Teknoloji ve Araç Haritası

Bu dosya **karar vermez, haritayı gösterir.** Üç kaynağı birbirine karıştırmamak için:

| Ne arıyorsun | Kaynak |
|---|---|
| Hipotez listesi (henüz karar değil) | [`docs/01-project-info/project-summary.md`](../docs/01-project-info/project-summary.md) — Teknolojiler tablosu |
| Kararın kendisi ve gerekçesi | [`docs/05-adr/`](../docs/05-adr/) — ilgili ADR |
| Dayanak → ölçüm zinciri | [`docs/05-adr/karar-haritasi.md`](../docs/05-adr/karar-haritasi.md) |

Bir teknoloji hakkında konuşurken **durumu** mutlaka belirtilir: *hipotez*, *Öneri*, *Kabul*, *bilinçli TBD*.

## Karar durumu özeti

| Alan | Seçim | Durum |
|---|---|---|
| Event Streaming | Apache Kafka | **Kabul** — ADR-0004 |
| Stream Processing | Apache Flink | **Kabul** — ADR-0003 |
| Time-Series Storage | PostgreSQL + TimescaleDB | **Öneri** — ADR-0002 (Faz 2) |
| Analytics Database | — | **Bilinçli TBD** — B-10 |
| Backend · Frontend · Relational DB · Cache · Orchestration | .NET 10 · Angular 22 · PostgreSQL · Redis · Kubernetes | *hipotez* |

> Bu tablo bir kısaltmadır. Çelişki halinde `project-summary.md` ve ADR'ler geçerlidir.

**Dil notu:** ADR-0003 ile sistem tek dilli değil — backend .NET, kural değerlendirme job'u JVM tarafında. Dil/arayüz seçimi Adım 6'ya bırakıldı.

## Araçlar

| Amaç | Araç | Nerede |
|---|---|---|
| BOTE kapasite hesabı | Python script | [`docs/03-capacity/bote.py`](../docs/03-capacity/bote.py) — sayı değişince script çalıştırılır, sonuç elle düzeltilmez |
| Diyagram | Mermaid (doküman içi) | [`docs/06-c4/c4-model.md`](../docs/06-c4/c4-model.md) |
| Versiyon kontrolü | git, `master` dalı | — |

## Build / test / run

Slice 1 (Adım 6) ile dolacak. Komutlar buraya yazılır; `.claude/rules/code.md` komut tekrarlamaz, buraya atıf verir.
