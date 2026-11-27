# FleetStream — Dokümantasyon Düzeni

Bu klasör, FleetStream'in **nasıl tasarlandığını** değil sadece **ne olduğunu** değil, hangi sayıya ve hangi gerekçeye dayanarak o hâle geldiğini kaydeder. Amaç, her mimari kararın sonradan savunulabilir olması.

## Klasör düzeni

Klasörler peşin açılmaz, sırası gelince açılır.

| Klasör | İçerik | Durum |
|---|---|---|
| `01-project-info/` | Proje özeti, glossary (ubiquitous language) | Başlandı |
| `02-requirements/` | Fonksiyonel gereksinimler, sayısal NFR/SLO tablosu, out-of-scope | Yazıldı (Adım 1) |
| `03-capacity/` | BOTE kapasite modeli, varsayımlar ve kaynakları | Yazıldı (Adım 2) |
| `04-design/` | High-level design, zaman ve durum modeli | Yazıldı (Adım 3) |
| `05-adr/` | Architecture Decision Records | Sürekli — 0001, 0002 *(Öneri)*, 0003 *(Kabul)* |
| `06-c4/` | C4 diyagramları (Level 1 Context + Level 2 Container) | Adım 5 — sırada |
| `08-validation/` | Load test planı, BOTE tahmini vs ölçülen sonuç | Adım 7 |

## Çalışma kuralları

**1. Hipotez ile karar farklıdır.**
`01-project-info/project-summary.md` içindeki teknoloji tablosu bir **hipotez listesidir**, karar değil. Bir teknoloji ancak kendi ADR'si yazıldığında karar hâline gelir. Hipotez olanlar `TBD` veya *(hipotez)* ile işaretlenir.

> **Kapanmayan `TBD` bir eksik değildir.** Analytics Database satırı bilinçli olarak `TBD` kalıyor: FR-19 (90 güne kadar agregasyon) kaç Asset üzerinden agregasyon yapılacağını söylemiyor ve tek Asset ile filo geneli arasında ~100.000× fark var. Karar verecek sayı yokken ADR yazmak, kararı hesaba değil tahmine dayandırmak olur. Bu satır, FR-19 netleştiğinde kapanır.

**2. Her mimari karar bir ADR'dir.**
Geri dönüşü maliyetli olan her seçim `05-adr/` altına yazılır. Şablon: [`05-adr/template.md`](05-adr/template.md). Numaralar artar, ADR'ler silinmez — yanlış çıkan ADR'nin durumu *Değiştirildi* olur ve yerine geçen ADR'ye atıf verilir.

Her ADR aynı zamanda [`05-adr/karar-haritasi.md`](05-adr/karar-haritasi.md) tablosuna bir satır ekler: kararın dayandığı SLO, BOTE satırı, SLI ve metrik adı. **Satırı olmayan ADR eksik ADR'dir.** O tablonun son iki kolonu (tahmin / ölçülen) Adım 7'de dolar ve döngüyü kapatır.

> **Durum alanı ciddiye alınır.** Erken uyarı sinyali gözlemlenemeyen bir karar *Kabul* olamaz, *Öneri* kalır. ADR-0002 (time-series storage) bu yüzden *Öneri*: Faz 2 bileşeni, sinyali Adım 7 load testinde ölçülemiyor. ADR-0003 (stream processing) *Kabul*: beş sinyalinin beşi de Slice 1 içinde gözlemlenebilir. İkisinin farklı olması tutarsızlık değil, kuralın çalıştığının kanıtı.

**3. Her sayının kaynağı yazılır.**
Dokümanda geçen hiçbir sayı kaynaksız duramaz. Kaynak türü üç tanedir ve açıkça belirtilir:
- **Varsayım** — biz seçtik, gerekçesi yazılır (`03-capacity/assumptions.md`)
- **Türetilmiş** — başka sayılardan hesaplandı, formülü yazılır
- **Ölçülmüş** — load test veya gerçek sistemden geldi, nasıl ölçüldüğü yazılır

**4. Doküman dili.**
Anlatım Türkçe, teknik terimler İngilizce (`event-time`, `back-pressure`, `partition`, `idempotency`). Terim çevrilmez; glossary'de karşılığı açıklanır.

**5. Tasarım kodu beklemez, kod tasarımı bekler.**
Bir dikey kesit implementasyonuna, o kesitin HLD'si ve ilgili ADR'leri yazılmadan başlanmaz.

## İlerleme sırası

```
0. Çalışma düzeni        → bu doküman + ADR şablonu + glossary
1. Gereksinimler + SLO   → BOTE'nin girdisi
2. BOTE / kapasite       → teknoloji kararlarının dayanağı
3. HLD                   → teknolojiden bağımsız şekil
4. Teknoloji ADR'leri    → TBD'lerin kapatılması
5. C4                    → seçilen kesit için component seviyesi
6. Dikey kesit kodu      → observability + test + CI + k8s
7. Load test             → tahmin vs gerçek, döngünün kapanması
```

**Sabitlenen çıpalar:** 100.000 varlık × 1 mesaj/5 saniye → ~20.000 event/sn ortalama.
**İlk dikey kesit:** telemetri ingest → stream processing → asset state → kural tabanlı uyarı.
