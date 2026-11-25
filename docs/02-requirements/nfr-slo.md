# Sayısal NFR / SLO Tablosu

Bu doküman BOTE'nin (Adım 2) **tek girdi kaynağıdır**. Buradaki her sayı `docs/README.md` kural 3 uyarınca kaynağıyla birlikte verilir:

- **Varsayım** — biz seçtik, gerekçesi yazılı
- **Türetilmiş** — başka sayılardan hesaplandı, formülü yazılı
- **Ölçülmüş** — load test veya gerçek sistemden geldi *(Adım 7'ye kadar bu kolonda hiçbir satır olmayacak)*

## 1. Ölçek

| # | Metrik | Hedef | Kaynak |
|---|---|---|---|
| S-01 | Takip edilen Asset sayısı | 100.000 | Varsayım: orta-büyük lojistik operatörü. Tek node'u kıracak, ama tek kişinin doğrulayabileceği ölçek. |
| S-02 | Asset başına Reading sıklığı | 1 / 5 saniye | Varsayım: sıcaklık yavaş değişir ama konum takibi için 5 sn makul çözünürlük. |
| S-03 | Ortalama ingest hızı | ~20.000 event/sn | Türetilmiş: S-01 / S-02 |
| S-04 | Günlük event sayısı | ~1,73 milyar | Türetilmiş: S-03 × 86.400 |
| S-05 | Tepe faktörü | Adım 2'de belirlenecek | BOTE varsayımı; `03-capacity/assumptions.md`'de gerekçelendirilecek |

## 2. Gecikme (latency)

| # | Metrik | Hedef | Kaynak |
|---|---|---|---|
| L-01 | **Alarm end-to-end**: Reading'in cihazda ölçülmesinden Alert'in sorgulanabilir olmasına kadar | **p99 ≤ 5 sn** | Varsayım: "gerçek zamanlı" iddiasının savunulabilir olması için. Micro-batch mimarileri eler, event-by-event işleme ve in-memory/cache state zorunlu kılar. |
| L-02 | Canlı Asset durumu sorgusu | p95 < 200 ms | Varsayım: dashboard etkileşimli hissettirmeli |
| L-03 | Son 24 saat telemetri serisi sorgusu | p95 < 1 sn | Varsayım |
| L-04 | 90 güne kadar agregasyon sorgusu | p95 < 5 sn | Varsayım: analitik sorgu, etkileşimli değil |

> **L-01, L-02 ve L-04'ün farklı olması tesadüf değil, tasarım girdisidir.** Üç farklı sorgu sınıfı üç farklı depolama çözümü gerektirir: canlı durum cache'ten, son 24 saat time-series store'dan, agregasyon rollup/analytics DB'den. Teknoloji tablosundaki üç `TBD`'nin gerekçesi bu üç satırda yatıyor.

## 3. Dayanıklılık (durability) ve doğruluk

| # | Metrik | Hedef | Kaynak |
|---|---|---|---|
| D-01 | Ack dönülmüş Reading için veri kaybı | **Sıfır** | Varsayım: soğuk zincir verisi compliance kanıtıdır; kaybolan bir Reading kaybolan bir ihlal olabilir. |
| D-02 | Delivery semantics | **At-least-once + idempotent işleme** | Türetilmiş: D-01 exactly-once'ı uçtan uca garanti edemez (cihaz ack'i kaybederse yeniden gönderir), dolayısıyla duplicate kaçınılmaz ve idempotency zorunlu. |
| D-03 | Kabul edilen maksimum late data | **24 saat** (event-time geriye) | Varsayım: şebeke kapsaması olmayan güzergahlarda bir günlük offline kalma normal davranış. |
| D-04 | Geç gelen veri için kural değerlendirmesi | Yapılır — **geriye dönük Alert üretilir** | Varsayım: D-01 ile tutarlı olmak için. Veriyi saklayıp ihlali kaçırmak, "kayıp yok" iddiasını iş seviyesinde boşa çıkarır. |
| D-05 | Alert duplicate'i | Aynı Asset + kural için aktif Alert varken yeni Alert üretilmez | Varsayım: operatöre 10 dakikada 120 alert göndermek alarm sistemini işlevsiz kılar |

> **D-02 bu projenin merkezindeki teknik zorunluluk.** Sıfır kayıp istemek, duplicate'i kabul etmek demektir. Bu takasın farkında olmamak, dağıtık sistem tasarımında en yaygın hata.

## 4. Erişilebilirlik (availability)

| # | Metrik | Hedef | Kaynak |
|---|---|---|---|
| A-01 | Ingest endpoint | %99,9 (aylık ~43 dk kesinti) | Varsayım, gerekçe aşağıda |
| A-02 | Sorgu API'si | %99,5 (aylık ~3,6 saat) | Varsayım: sorgu kesintisi veri kaybetmez, sadece görünürlük kaybettirir |
| A-03 | Alarm üretim pipeline'ı | %99,9 | Varsayım: A-01 ile eşlenik; ingest çalışıp alarm üretmiyorsa sistem sessizce başarısız olur |

> **A-01 neden %99,99 değil?** D-03 sayesinde cihaz 24 saate kadar veriyi kendinde tutabiliyor. Yani kısa bir ingest kesintisi **veri kaybı değil, gecikme** üretir — kesinti sonrası cihazlar birikmiş veriyi gönderir. Bu, availability hedefini bir mertebe gevşetmemize izin veriyor; karşılığında kesinti sonrası **ingest hızının normalin çok üzerine çıkmasını** (recovery burst) hesaba katmak zorundayız. Bu burst, Adım 2'de tepe faktörünün (S-05) belirleyici bileşeni olacak.

## 5. Veri yaşam döngüsü

| # | Metrik | Hedef | Kaynak |
|---|---|---|---|
| R-01 | Ham Reading retention | 90 gün | Varsayım: operasyonel inceleme ve müşteri itirazları için yeterli pencere |
| R-02 | Downsampled veri retention | 1 yıl | Varsayım |
| R-03 | Downsampling çözünürlüğü | Adım 3'te belirlenecek (5 dk / 1 saat kovaları) | Tasarım kararı |

## 6. Kapsam ve model kısıtları

| # | Kısıt | Değer | Kaynak |
|---|---|---|---|
| C-01 | Kural tanım modeli | Asset Type bazında, ~5-10 global kural | Varsayım: en küçük model. 20K event/sn × ~7 kural = **~140K değerlendirme/sn** — basit model bile gerçek bir yük üretiyor. |
| C-02 | Tenancy | Tek tenant; `tenantId` şemada ve partition key tasarımında rezerve | Varsayım: izolasyon ve auth kapsam dışı, ama sonradan eklemek tam repartition + veri göçü demek. Bedava alınabilen tek-yönlü kapı önlemi. |
| C-03 | Asset ↔ Device ilişkisi | 1:1 | Varsayım: çoklu device (çekici + dorse) ilk kesitte gereksiz karmaşıklık |

## 7. SLI tanımları — SLO'ların nasıl ölçüleceği

Bir SLO, SLI'ı yazılmadan **ölçülemez bir niyettir**. Her satır kodun hangi iki zaman damgasını kaydedeceğini söylüyor; Adım 6'da enstrümantasyon doğrudan bu tablodan yazılacak.

| # | Hangi SLO | Ölçülen | Olay kümesi (hangi istekler sayılır) | Pencere | Metrik adı |
|---|---|---|---|---|---|
| **SLI-01** | L-01 | `alert.created_at − reading.event_time` | **Yalnızca** `ingest_time − event_time < 60 sn` olan Reading'ler | p99, 5 dk'lık kovalar; uyum penceresi 30 gün | `fleetstream_alert_latency_seconds` (histogram) |
| **SLI-02** | A-01 | 1 sn içinde 2xx dönen ingest isteği oranı | Tüm ingest istekleri; **4xx hariç** (geçersiz payload sunucunun hatası değil) | 30 gün | `fleetstream_ingest_requests_total{outcome}` |
| **SLI-03** | L-02 | Canlı Asset durumu endpoint'inin yanıt süresi | Tüm başarılı sorgular | p95, 5 dk'lık kovalar | `fleetstream_query_duration_seconds{endpoint="asset-state"}` |
| **SLI-04** | A-03 | **Canary Asset'in** son Alert'inin yaşı | Sürekli ihlal üreten 1 sentetik Asset | Sürekli; ihlal = yaş > 60 sn | `fleetstream_canary_alert_age_seconds` |

### SLI-01'in filtresi neden zorunlu

`03-capacity/bote-model.md` §2.8: kesinti sonrası recovery sırasında işlenen Reading'lerin `event_time`'ı saatler öncesine ait. Bu veriyi SLI-01'e dahil ederseniz **her kesinti SLO'yu otomatik ihlal eder ve error budget bir anda tükenir** — hâlbuki sistem D-03'ün gerektirdiği gibi davranmıştır. 60 sn eşiği, "cihaz zamanında gönderdi" ile "cihaz buffer'dan boşaltıyor" ayrımının pratik sınırı.

**Bedeli:** bu filtre, geç veri yolunun (B-03) gecikmesini hiçbir SLO'nun ölçmemesi anlamına geliyor. Faz 2'de ayrı bir SLO gerekecek; şimdilik bilinçli boşluk.

### SLI-04 neden consumer lag değil

Consumer lag sıfır olduğu hâlde alarm üretilmiyor olabilir: kural motoru çökmüş, kural tablosu boş gelmiş, veya tüm event'ler sessizce `invalid` sayılıp atılmış olabilir. Lag bu üç durumda da **sağlıklı** görünür. **A-03'ün gerçek riski sessiz başarısızlıktır**, o yüzden ölçüm uçtan uca olmak zorunda: sürekli ihlal üreten sahte bir Asset, ve onun Alert'inin bayatlama süresi. Bu aynı zamanda ADR'lerin "erken uyarı sinyali" alanının ilk gerçek örneği.

## 8. BOTE'de kapanan sayılar

Adım 2 çıktısı: `03-capacity/bote-model.md`

| Konu | Değer | Nerede |
|---|---|---|
| Tepe faktörü (S-05) | **×2** (yakalama süresi ≈ kesinti süresi) | §2.8, B-06 |
| Reading payload boyutu | **~200 B JSON** (~50 B Protobuf; fark hiçbir darboğazı açmıyor) | §2.1–2.2, B-05 |
| Kafka partition sayısı | **48**, RF 3, 7 gün retention, key `tenantId:assetId` | §2.3, B-04 |
| Beklenen Alert hacmi | **~0,03 Alert/sn** — ingest'in 5 mertebe altında | §2.11, B-09 |
| Node/instance sayısı | **~10 node × 8 vCPU** | §3 |
| Maliyet | **Hesaplanmadı — kapsam dışı** (gelir amacı yok, maliyet karar sürücüsü değil) | §4 |

### BOTE'nin bu dosyaya geri döndürdüğü iki kısıt

| # | Kısıt | Sebep |
|---|---|---|
| C-01 revizyonu | Kural modeli **"eşik + sürekli süre"** ile sınırlı; ortalama/pencere tabanlı kural kapsam dışı | State 25 MB ile 346 GB arasında 14.000× fark yapıyor (§2.4) |
| D-03/D-04 sonucu | Geç veri **ayrı bir consumer**'dan, log yeniden okunarak işlenir | Canlı state geriye dönük streak bilgisini tutmuyor (§2.5) |

> Bu iki satır Adım 3'ün (HLD) gündemidir. Özellikle ikincisi, FR-12 (dedup) ile FR-13 (geriye dönük Alert) arasındaki çatışmanın çözüleceği yer.
