# Glossary — FleetStream Ubiquitous Language

Bu listedeki terimler kodda, dokümanlarda ve diyagramlarda **aynı** şekilde kullanılır. Bir kavramın iki adı olmaz.

⚠️ işaretli satırlar henüz karara bağlanmamıştır; Adım 1 (gereksinimler) veya Adım 3 (HLD) sırasında netleşecek.

## Domain

| Terim | Tanım |
|---|---|
| **Asset** | Takip edilen fiziksel birim: kamyon, kargo uçağı veya reefer konteyner. Benzersiz `assetId` taşır. Sistemin takip ettiği en küçük iş birimi. |
| **Asset Type** | `Truck` / `AirCargo` / `ReeferContainer`. Hangi sensörlerin beklendiğini ve hangi kuralların uygulanabilir olduğunu belirler (bir kamyonda kargo nemi yoktur). |
| **Device** | Asset üzerindeki, telemetri üreten donanım. Ack alamadığında Reading'i kendinde tutar ve yeniden gönderir — yani sistemin ilk buffer'ı. İlk kesitte Asset ↔ Device ilişkisi **1:1** (`../02-requirements/nfr-slo.md` C-03); çoklu device faz 2. |
| **Reading** | Tek bir zaman damgalı ölçüm seti: konum, hız, sıcaklık, nem. Sistemin ingest ettiği atomik veri birimi. |
| **Telemetry** | Reading'lerin bütünü; alan adı olarak kullanılır (örn. "telemetry ingest"). |
| **Asset State** | Bir Asset'in **son bilinen** durumu: son konum, son ölçümler, son görülme zamanı, aktif alert'ler. Sorgu için tutulan türetilmiş veri; kaynak değil. |
| **Cold Chain** | Kargonun üretimden teslime kadar belirli sıcaklık aralığında tutulması gereken taşıma zinciri. |
| **Excursion** | Sektör terimi: sıcaklığın izin verilen aralığın dışına çıkması. Her excursion bir Violation'dır ama her Violation excursion değildir (hız ihlali de olabilir). |
| **Shipment / Trip** | Bir Asset'in belirli bir kargoyu taşıdığı iş emri / sefer. **Kapsam dışı** (`../02-requirements/out-of-scope.md`) — domain'i iki katına çıkarırdı. Bedeli: kurallar kargo bazlı değil Asset Type bazlı kalıyor, her kargonun kendi sıcaklık aralığı olamıyor. |

## Kural ve uyarı

| Terim | Tanım |
|---|---|
| **Rule** | Kullanıcı tanımlı koşul: *"ReeferContainer sıcaklığı 10 dakika boyunca 8°C üzerindeyse"*. Eşik, süre ve kapsam (hangi Asset'ler) içerir. Veri değil, konfigürasyon. |
| **Violation** | Bir Rule'un koşulunun sağlandığının **tespiti**. Stream processing'in ürettiği olay. |
| **Alert** | Violation'dan türeyen, kullanıcıya görünen ve yaşam döngüsü olan kayıt. Violation → Alert eşlemesi 1:1 **değildir**: aynı Asset + aynı kural için aktif Alert varken yeni Alert üretilmez (`../02-requirements/nfr-slo.md` D-05 — *flapping* bastırma). Mekanizma Adım 3'te tasarlanacak. |
| **Alert Lifecycle** | `Raised` → `Acknowledged` → `Resolved`. `Acknowledged` manuel; `Resolved` yalnızca **pozitif gözlemle** otomatik olur — kuralın duration penceresi kadar süre eşiğin içinde kalan okumalar gelmesi (HLD H-02). Veri gelmemesi resolve değildir, o ayrı bir Violation'dır (Stale Asset). |
| **Stale Asset** | Beklenen süre boyunca hiç Reading göndermeyen Asset. **Verinin gelmemesi de bir alarm sebebidir** — ve stream processing'de tespiti en zor olandır, çünkü tetikleyici bir event yoktur (timer gerekir). |

## Mimari

| Terim | Tanım |
|---|---|
| **Hot Path** | Reading'in sisteme girişinden Alert üretimine kadar geçtiği, gecikmeye duyarlı yol. İlk dikey kesit budur. |
| **Cold Path** | Reading'lerin kalıcı depolamaya yazılıp sonradan analitik sorgulandığı, gecikmeye toleranslı yol. |
| **Event-time** | Reading'in **cihazda ölçüldüğü** an. Kural değerlendirmesinin dayanması gereken zaman. |
| **Processing-time** | Reading'in sunucuda **işlendiği** an. Event-time ile arasındaki fark, mobil varlıklarda şebeke kaybı nedeniyle saatlere çıkabilir. |
| **Out-of-order** | **Geç gelen veri ile aynı şey değil** (HLD §2.1). *Geç ama sıralı:* event-time eski, ama o Asset için daha yenisi henüz işlenmedi — cihazın buffer'ını boşaltması; hot path normal işler, maliyeti sıfır. *Sıra dışı (out-of-order):* event-time, o Asset için **zaten işlenmiş** bir okumadan eski — retry veya cihaz saat düzeltmesi; geçmişin yeniden hesaplanmasını gerektirir. Slice 1'de ölçülür, değerlendirilmez. |
| **Watermark** | Stream processing'in *"bu event-time'dan öncesi için tüm veri geldi sayıyorum"* dediği sınır. Geç gelen veriyle ne yapılacağını belirler. |
| **Idempotency** | Aynı Reading'in iki kez işlenmesinin sonucu değiştirmemesi. At-least-once delivery altında zorunlu. |
| **Back-pressure** | Downstream yetişemediğinde upstream'in yavaşlatılması veya veri atılması. Alternatifi kontrolsüz bellek büyümesi ve çökmedir. |
| **Consumer Lag** | Kafka'da üretilen ile tüketilen offset arasındaki fark. Sistemin yetişip yetişmediğinin birincil göstergesi. |
