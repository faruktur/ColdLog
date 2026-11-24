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

| Area | Technology |
|---|---|
| Frontend | Angular 22 |
| Backend | .NET 10 |
| Relational Database | PostgreSQL |
| Time-Series / Telemetry Storage | TBD |
| Event Streaming | Apache Kafka |
| Stream / Data Processing | TBD |
| Analytics Database | TBD |
| Cache / Real-Time State | Redis |
| Container Orchestration | Kubernetes |
