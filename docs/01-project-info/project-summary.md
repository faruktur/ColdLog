# FleetStream

## Özet

**FleetStream** kamyonlar, kargo uçakları ve soğutuculu konteynerler gibi hareket halindeki varlıklar tarafından üretilen yüksek hacimli telemetri verilerini toplamak, işlemek ve analiz etmek üzere tasarlanmış, gerçek zamanlı bir filo ve soğuk zincir takip sistemidir.

Sistem; GPS koordinatları, hız, sıcaklık ve kargo nemi gibi telemetri verilerini gerçek zamanlı olarak işler. Temel odak noktası; ölçeklenebilir veri girişi, akış işleme, gerçek zamanlı durum takibi ve kural tabanlı uyarı oluşturma süreçleri için gereken arka uç (backend) altyapısıdır.

Hafif bir ön uç (frontend) uygulaması ise canlı varlık izleme, telemetri görselleştirme ve oluşturulan uyarıları görüntüleme imkânı sunarak arka uç altyapısını tamamlar.

## Temel İşlevler

- Gerçek zamanlı telemetri verisi alımı
- Yüksek iş hacimli olay işleme
- Varlıkların konum ve durumunun anlık takibi
- Sıcaklık ve nem izleme
- Kural tabanlı uyarı oluşturma
- Geçmiş telemetri verilerinin depolanması
- Gerçek zamanlı ve analitik veri sorgulama
- Yatay ölçeklenebilirlik ve dağıtık işleme
- AI Agent ile veri analizi

## Teknolojiler

> **Bu tablo bir hipotez listesidir, karar değildir.** Her satır, kendi ADR'si (`docs/05-adr/`) BOTE çıktısına dayanarak yazıldığında karar hâline gelir. Bkz. `docs/README.md` — Çalışma kuralları.

| Area | Technology | Durum |
|---|---|---|
| Frontend | Angular 22 | *(hipotez)* |
| Backend | .NET 10 | *(hipotez)* |
| Relational Database | PostgreSQL | *(hipotez — ADR yazılmayacak, bkz. B-09)* |
| Time-Series / Telemetry Storage | PostgreSQL + TimescaleDB | **Karar** — [ADR-0002](../05-adr/0002-time-series-storage.md) *(Öneri durumunda)* |
| Event Streaming | Apache Kafka | *(hipotez — 48 partition / RF 3 / 7 gün: B-04)* |
| Stream / Data Processing | Apache Flink | **Karar** — [ADR-0003](../05-adr/0003-stream-processing.md) *(Kabul)* |
| Analytics Database | TBD | **Bilinçli TBD** — FR-19 agregasyonun Asset kardinalitesini söylemiyor; karar verecek sayı yok |
| Cache / Real-Time State | Redis | *(hipotez — hot path state'i **değil**; Query API'nin okuduğu projeksiyon: `hld.md` §5.3, H-07)* |
| Container Orchestration | Kubernetes | *(hipotez)* |

> **Dil notu:** ADR-0003 ile Flink geldiği için sistem artık tek dilli değil. Backend .NET; kural değerlendirme job'u JVM tarafında çalışacak (dil/arayüz seçimi Adım 6'ya bırakıldı). Bu, ADR-0003'ün *Sonuçlar* bölümünde kabul edilen bedel olarak yazılıdır.
