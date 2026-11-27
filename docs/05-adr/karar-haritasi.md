# Karar Haritası

Bu dosyanın tek işi, her kararı **dayanağından ölçümüne kadar** tek satırda izlenebilir kılmak:

```
kurgusal senaryo → SLO → BOTE satırı → karar (ADR) → SLI → metrik → ölçülen değer
```

Son iki kolon **Adım 7'de (load test)** dolacak. O an bu dosya şu cümleyi üretebilir hâle gelir: *"Bu kararı şu sayıya dayanarak aldım, tahminim şuydu, gerçek şu çıktı."* Projenin asıl çıktısı bu tablodur; kod onun kanıtı.

**Kural:** Yeni bir ADR yazıldığında aynı mesajda bu tabloya satırı eklenir. Satırı olmayan ADR, eksik ADR'dir.

## Kararlar

| # | Karar | Dayandığı SLO/NFR | BOTE satırı | İlgili SLI | Metrik | Tahmin | Ölçülen |
|---|---|---|---|---|---|---|---|
| B-01 | L-01 = p99 ≤ 5 sn | Referans senaryo §0 (15 dk domain bütçesi) | §1.1–1.2 | SLI-01 | `fleetstream_alert_latency_seconds` | p99 ≤ 5 sn | — |
| B-02 | Kural modeli: eşik + sürekli süre | C-01 | §2.4 | — | `fleetstream_rule_state_bytes` | ~25 MB | — |
| B-03 | Late data ayrı consumer | D-03, D-04, FR-13 | §2.5 | *(SLO yok — bilinçli boşluk)* | `fleetstream_latedata_lag_seconds` | — | — |
| B-04 | Kafka 48 partition, RF 3, 7 gün | S-03, D-01, D-03 | §2.3 | SLI-01 (dolaylı) | `kafka_consumergroup_lag` | partition başına ~420 event/sn | — |
| B-05 | Serialization: JSON | — (darboğaz değil) | §2.1–2.2 | — | `fleetstream_ingest_bytes_total` | ~4 MB/sn | — |
| B-06 | Tepe faktörü ×2 | A-01, D-03 | §2.8 | SLI-02 | `fleetstream_ingest_requests_total` | tepe 40.000 req/sn | — |
| B-07 | Back-pressure + `Retry-After` | A-01, S-05 | §2.7 | SLI-02 | `fleetstream_ingest_throttled_total` | kesinti sonrası > 0 | — |
| B-08 | Headroom: tepe × 2, N+1 | A-01, A-03 | §3 | — | pod CPU kullanımı | < %50 | — |
| B-09 | Alert deposu: PostgreSQL *(ADR yazılmadı)* | — | §2.11 | — | `fleetstream_alerts_created_total` | ~2.500/gün | — |
| B-10 | Analytics DB: **TBD** | L-04, FR-19 | §3 | — | — | karar verecek sayı yok | — |
| H-01 | Alert = event-time aralığı; dedup aralık çakışmasıyla | FR-12, FR-13, D-02, D-05 | §2.5 | SLI-01 | `fleetstream_alerts_created_total` | ~2.500/gün, replay'de artış yok | — |
| H-02 | Auto-resolve yalnızca pozitif gözlemle | FR-14, FR-15 | — | — | `fleetstream_alert_ack_seconds` (MTTA) | ~3 dk (senaryo) | — |
| H-03 | Reorder buffer yok; sıra dışı okuma hot path'te işlenmez | L-01 | §2.4 | *(SLO yok — ölçülen boşluk)* | `fleetstream_outoforder_total` | ? — Slice 1'in ilk bilinmeyeni | — |
| H-04 | Stale tespiti `ingest_time`'a bakar, 30 sn tarama | FR-11, A-03 | §2.9 | SLI-04 | `fleetstream_stale_assets` | ~2.000/gün | — |
| H-05 | Kural dağıtımı 10 sn poll | FR-09 | — | — | `fleetstream_rule_version` | yayılma ≤ 10 sn | — |
| ADR-0001 | Mimari kararları ADR ile kaydetme | — (süreç kararı) | — | — | ADR'siz teknoloji kararı sayısı | 0 | — |
| ADR-0002 | Time-series storage: PostgreSQL + TimescaleDB *(**Öneri** — Faz 2, sinyali Adım 7'de gözlemlenemez)* | R-01, R-02, R-03, L-03 | §2.10 | SLI-03 | `insert_duration_seconds`, gerçekleşen sıkıştırma oranı | 155,5 milyar satır, ~2,1 TB (15× sıkıştırma) | — |
| ADR-0003 | Stream processing: Flink (yönetilen state) *(**Kabul**)* | L-01, D-01, D-02, C-01 | §2.4, §2.6, §2.3 | SLI-01, SLI-04 | `flink_checkpoint_duration`, `flink_backPressuredTimeMsPerSecond`, `kafka_consumergroup_lag` | checkpoint < 5 sn; back-pressure = 0; state ~25 MB | — |

## Okunması gereken zincir

BOTE'nin en öğretici çıktısı tek bir karar değil, bir **zincir**:

```
D-03 (24 saat geç veri kabul edilir)
  → A-01 gevşetilebilir (%99,9), çünkü kesinti kayıp değil gecikme üretir
    → ama kesinti sonrası recovery burst oluşur → S-05 = ×2
      → recovery sırasındaki Reading'lerin event-time'ı saatler öncesine ait
        → SLI-01 geç veriyi dışlamak zorunda, yoksa her kesinti error budget'ı bitirir
          → ve bunun bedeli: geç veri yolunun gecikmesini hiçbir SLO ölçmüyor
```

Tek bir gereksinim satırı (D-03) beş adım sonra bir **ölçüm boşluğu** üretiyor. Bu tabloyu tutmanın sebebi bu: tek tek bakıldığında her karar makul, zincir hâlinde bakıldığında boşluk görünüyor.

## Adım 7'de yapılacak

1. Son iki kolonun doldurulması.
2. Tahminden **1 mertebe** sapan her satır için: ya BOTE'nin varsayımı yanlıştı, ya implementasyon beklendiği gibi değil — ikisi farklı sonuçlar doğurur, hangisi olduğu yazılır.
3. Ölçülen noktadan geriye doğru gecikme-maliyet eğrisinin çizilmesi (`bote-model.md` §1.3'teki segment tablosuna gerçek değerlerin eklenmesi).
