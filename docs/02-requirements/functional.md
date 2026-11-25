# Fonksiyonel Gereksinimler

**Kapsam notu:** Bu liste sistemin tamamını tanımlar. **İlk kesit** kolonu, ilk dikey kesitte (telemetri ingest → stream processing → asset state → kural tabanlı uyarı) implement edilecek olanları işaretler. Kapsam dışı bırakılanlar için bkz. [`out-of-scope.md`](out-of-scope.md).

## Aktörler

| Aktör | Tanım |
|---|---|
| **Device** | Asset üzerindeki telemetri üreten donanım. Sisteme veri yazan tek dış aktör. Ack alamadığında veriyi kendinde tutar ve yeniden gönderir. |
| **Fleet Operator** | Filoyu izleyen, kuralları tanımlayan ve alert'lere müdahale eden kullanıcı. |
| **System** | Zamanlayıcı tetiklemeli iç işler (stale asset taraması, downsampling, retention). Kullanıcı etkileşimi olmadan çalışır. |

## Ingest

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-01 | Sistem Device'lardan Reading kabul eder ve **kalıcı yazma tamamlandıktan sonra** ack döner. Ack dönmeden önce veri kaybı olmaz. | ✅ |
| FR-02 | Aynı Reading'in birden fazla kez gönderilmesi (Device retry'ı sonucu) sistem durumunu değiştirmez — **idempotent işleme**. | ✅ |
| FR-03 | Event-time'ı 24 saate kadar geçmişte olan Reading kabul edilir ve kural değerlendirmesine girer. | ✅ |
| FR-04 | Şemaya uymayan veya fiziksel olarak imkânsız değer taşıyan (örn. -300°C) Reading reddedilir; reddedilen veri kaybolmaz, incelenebilir bir yere yazılır. | ✅ |
| FR-05 | Event-time'ı 24 saatten daha eski olan Reading reddedilir ve bu durum metrik olarak görünür. | ✅ |

> **FR-04 neden "kaybolmaz"?** Geçersiz veri sessizce atılırsa, bir sensör bozulduğunda bunu kimse fark etmez. Poison message'ın gideceği bir yer olmalı.

## Asset State

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-06 | Her Asset için son bilinen konum, hız, sıcaklık, nem ve **son görülme zamanı** tutulur. | ✅ |
| FR-07 | Asset State yalnızca daha yeni event-time'lı Reading ile güncellenir — geç gelen eski bir Reading, güncel durumu geriye çekmez. | ✅ |

> **FR-07, FR-03'ün doğal sonucu.** Geç veriyi kabul ediyorsak, "son durum" ile "geçmişe yazma" ayrışmak zorunda: geç Reading arşive ve kural değerlendirmesine girer, ama Asset State'i bozmaz.

## Kurallar ve uyarılar

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-08 | Fleet Operator, Asset Type bazında kural tanımlar: ölçüm türü, eşik, karşılaştırma yönü ve **süre koşulu** (örn. *"10 dakika boyunca 8°C üzerinde"*). | ✅ |
| FR-09 | Kural değişiklikleri yeniden başlatma gerektirmeden canlı sisteme yansır. | ✅ |
| FR-10 | Sistem her Reading için ilgili Asset Type'ın kurallarını değerlendirir ve koşul sağlandığında Violation üretir. | ✅ |
| FR-11 | Beklenen süre boyunca Reading göndermeyen Asset için Violation üretilir (**Stale Asset** — tetikleyici event yoktur). | ✅ |
| FR-12 | Violation'dan Alert üretilir. Aynı Asset + aynı kural için **aktif bir Alert varken yeni Alert üretilmez** (flapping bastırma). | ✅ |
| FR-13 | Geç gelen Reading bir ihlal içeriyorsa, ihlalin event-time'ı geçmişte olsa bile Alert üretilir (**geriye dönük alarm**) ve Alert, ihlalin gerçekleştiği zamanı taşır. | ✅ |
| FR-14 | Alert yaşam döngüsü: `Raised` → `Acknowledged` → `Resolved`. Acknowledge işlemini Fleet Operator yapar. | ✅ |
| FR-15 | Koşul ortadan kalktığında Alert otomatik `Resolved` olur. | ⚠️ Karar Adım 3'te |

> **FR-12 ve FR-13 birlikte gerginlik üretiyor.** Dedup "aynı ihlal için tek alert" derken, geriye dönük alarm geçmişte kapanmış bir ihlal için alert isteyebilir. Bu iki gereksinimin kesişimi HLD'nin (Adım 3) çözmesi gereken en zor noktadır.

## Sorgulama

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-16 | Canlı Asset durumu sorgulanabilir (tek asset ve liste). | ✅ minimal |
| FR-17 | Alert listesi sorgulanabilir; duruma, Asset'e ve zaman aralığına göre filtrelenir. | ✅ minimal |
| FR-18 | Bir Asset'in son 24 saatlik telemetri serisi sorgulanabilir. | ❌ Faz 2 |
| FR-19 | 90 güne kadar geçmiş için agregasyon sorgulanabilir (ortalama/min/max, zaman kovaları). | ❌ Faz 2 |

> FR-16 ve FR-17 "minimal" çünkü ilk kesitin **sonucunu görebilmek** için gerekiyorlar, kendi başına hedef değiller. Tam sorgu API'si cold path ile birlikte gelir.

## Depolama ve yaşam döngüsü

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-20 | Ham Reading'ler 90 gün saklanır. | ❌ Faz 2 |
| FR-21 | 90 günü aşan veri downsample edilerek 1 yıl saklanır; ham veri silinir. | ❌ Faz 2 |
| FR-22 | Retention ve downsampling operatör müdahalesi olmadan çalışır. | ❌ Faz 2 |

> FR-20-22 ilk kesitte yok ama **BOTE'ye dahil** (Adım 2): depolama ve maliyet hesabı sistemin tamamı için yapılır, yoksa time-series store kararı dayanaksız kalır.

## Frontend

| # | Gereksinim | İlk kesit |
|---|---|:---:|
| FR-23 | Haritada canlı asset konumları ve durum renklendirmesi. | ❌ Faz 2 |
| FR-24 | Asset telemetri zaman serisi grafiği. | ❌ Faz 2 |
| FR-25 | Alert listesi ve acknowledge aksiyonu. | ❌ Faz 2 |
