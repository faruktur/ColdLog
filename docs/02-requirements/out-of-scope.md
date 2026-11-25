# Kapsam Dışı

Bu doküman, **bilinçli olarak yapmadığımız** şeyleri kaydeder. Amaç ikisi birden: scope creep'i engellemek ve "bunu neden düşünmediniz?" sorusuna cevap bırakmak.

Üç kategori var:

- **Faz 2** — sistemin parçası, ilk dikey kesitten sonra gelecek
- **Faz 3** — niyet var, tasarımı etkilemiyor
- **Kapsam dışı** — bu projede hiç yapılmayacak

## Faz 2 — sistemin parçası, sonraki kesitler

| Konu | Neden ilk kesitte değil |
|---|---|
| Cold path: ham telemetri kalıcı depolama, retention, downsampling | İlk kesit hot path. Ama BOTE'ye dahil (bkz. `nfr-slo.md` R-01/R-02), çünkü time-series store kararı bu sayılara dayanacak. |
| Tam sorgu API'si (son 24 saat serisi, 90 gün agregasyon) | Cold path'e bağımlı |
| Frontend (harita, grafik, alert ekranı) | Backend kesiti bitmeden arayüz yapmak, değişecek bir sözleşmeye karşı kod yazmak olur |
| Bildirim kanalları (e-posta, SMS, push, webhook) | Alert **üretimi** ilk kesitte var; **dağıtımı** ayrı bir problem (retry, rate limit, kullanıcı tercihleri) ve mimari olarak yeni bir şey öğretmiyor |
| Alert otomatik resolve (FR-15) | Kararı Adım 3'te verilecek; dedup mantığıyla birlikte tasarlanmalı |
| Geofence / coğrafi kural türü | Spatial indeksleme ayrı bir problem alanı. Threshold + duration + stale üçlüsü zaten hot path'in tüm zorluğunu içeriyor. |
| Çoklu Device desteği (çekici + dorse) | `nfr-slo.md` C-03: 1:1 varsayımı. Asset State'i birden fazla kaynaktan birleştirmek (state merge) ayrı bir karmaşıklık. |

## Faz 3 — niyet var, tasarımı etkilemiyor

| Konu | Not |
|---|---|
| AI Agent ile veri analizi | Proje özetinde yer alıyor. Mimari olarak bambaşka bir eksen (sorgu üretimi, LLM maliyeti, güvenlik) ve yüksek trafik öğrenme hedefine katkısı en az olan madde. Cold path ve sorgu API'si olgunlaşmadan anlamsız. |

## Kapsam dışı — bu projede yapılmayacak

| Konu | Gerekçe |
|---|---|
| Multi-tenant izolasyon, tenant bazlı auth / quota / rate limit | `nfr-slo.md` C-02: tek tenant. Ama `tenantId` veri modelinde rezerve edildi — sonradan eklemenin maliyeti veri göçü olduğu için bu önlem bedava alındı. |
| Device provisioning, cihaz kimlik yönetimi, OTA firmware güncelleme | IoT device management ayrı bir ürün alanı. Cihazların kimliğini ve kimlik doğrulamasını **verili** kabul ediyoruz. |
| Kullanıcı yönetimi, RBAC, organizasyon hiyerarşisi | Standart CRUD; yüksek trafik mimarisi öğrenme hedefine katkısı yok |
| Shipment / Trip (sefer ve kargo iş emri) | Soğuk zincir domaininin gerçek merkezi, ama domain'i iki katına çıkarıyor: sefer yaşam döngüsü, kargo-asset eşlemesi, sefer bazlı kural ve raporlama. Kabul edilirse kesit "basit domain" olmaktan çıkar. **Bu kararın bedeli:** kurallar kargo bazlı değil Asset Type bazlı kalıyor (C-01), yani her kargonun kendi sıcaklık aralığı olamıyor. |
| Rota optimizasyonu, ETA tahmini, harita yönlendirme | Farklı problem sınıfı (optimizasyon), telemetri mimarisiyle ilgisi yok |
| Faturalama, abonelik, müşteri yönetimi | Projenin gelir amacı yok |
| Disaster recovery, çoklu bölge (multi-region) replikasyon | Tek bölge varsayılıyor. Multi-region, consistency ve veri egemenliği konularını açar; tek kişilik projede doğrulanamaz. **Not:** `nfr-slo.md` A-01 (%99,9) bu varsayımla tutarlı — daha yüksek availability hedefi multi-region'ı zorunlu kılardı. |
| Cihaz tarafı yazılımı | Load test için bir **telemetri simülatörü** yazılacak (Adım 7), gerçek cihaz yazılımı değil |
