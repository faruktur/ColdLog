# BOTE Kapasite Modeli

**Girdi:** `02-requirements/nfr-slo.md` (tek kaynak). Buradaki hiçbir sayı o dosyadaki bir satıra dayanmadan üretilmemiştir.
**Yöntem:** Tek anlamlı basamak. Amaç doğru sayıyı bulmak değil, **doğru mertebeyi bulup kararı zorlayan satırı tespit etmek**.
**Hesap makinesi:** [`bote.py`](bote.py) — bu dosyadaki tüm sayıları üretir. `python bote.py` raporu basar, `python bote.py --test` buradaki sayıların modelden çıktığını doğrular. Girdileri değiştirip sonucu görmek için o dosya kullanılır; **gerekçeler burada, aritmetik orada.**

---

## 0. Dondurulmuş referans senaryo

> **Bu blok 2026-11-25 tarihinde yazılmış ve dondurulmuştur.** Kurgusaldır. Bir kararı haklı çıkarmak için **değiştirilmez**; değişirse tarihli bir revizyon notu olarak eklenir, sessizce düzeltilmez. (Kurgusal senaryonun tek gerçek riski, sonradan kararın şekline göre eğilmesidir.)

**Müşteri:** Orta-büyük bir soğuk zincir taşıma operatörü. 100.000 takip birimi (çekici, reefer konteyner, hava kargo ULD).
**Birincil yük:** İlaç soğuk zinciri. Ürün bandı **2–8 °C**.
**Düzenleyici kural (kurgusal):** Sıcaklık 8 °C'yi aştıktan sonra **15 dakika** içinde müdahale edilmezse parti karantinaya alınır ve imha edilir.
**Müdahale zinciri:** Alarm ofisteki dispatcher ekranına düşer → dispatcher şoförü arar → şoför kenara çekip kompresörü resetler veya yedeğe alır.
**Müdahale eden insan araçta değil, ofistedir.** (Bu cümle bir mimari karar üretiyor — bkz. §1.4.)

### 0.1 Alternatif segmentler (karşılaştırma için)

| Segment | Yük | Tolerans penceresi | Durum |
|---|---|---|---|
| **A — İlaç** | 2–8 °C ilaç | **15 dk** | **Referans senaryo** |
| B — Gıda dağıtımı | −18 °C donmuş | ~2 saat (−15 °C'ye kadar) | Alternatif |
| C — Kuru yük | Sıcaklık yok, sadece konum | Gün sonu mutabakatı | Alternatif |

---

## 1. L-01 (p99 ≤ 5 sn) nereden geliyor?

### 1.1 Toplam bütçenin dürüst dağılımı — Segment A

| Kalem | Süre | Kim harcıyor |
|---|---|---|
| Düzenleyici toplam bütçe | **15 dk** | — |
| Kural duration penceresi (8 °C üzeri, 2 dk sürekli) | −2 dk | **Domain kararı** |
| Dispatcher'ın alarmı görmesi (MTTA) | −3 dk | İnsan |
| Telefon + şoförün müdahalesi | −7 dk | İnsan |
| **Sisteme kalan** | **≈ 3 dk** | Mimari |

**Dürüst sonuç: domain, sistemden 3 dakika istiyor — 5 saniye değil.** Bu rakamı gizlemiyoruz, çünkü 5 sn'yi "domain öyle gerektiriyor" diye savunmak sahte bir gerekçe olurdu.

### 1.2 O zaman 5 sn neden?

**Çünkü SLO, domain limitine değil; bozulmuş sistemin domain limitinin içinde kalacağı yere konur.**

| Hedef | Domain limiti (3 dk) içinde kalmak için tolere edilen bozulma |
|---|---|
| p99 ≤ **5 sn** | **36×** — consumer lag 36 katına çıksa bile ürün kurtulur |
| p99 ≤ 60 sn | 3× — tek bir broker arızası bütçeyi bitirir |
| p99 ≤ 5 dk | **0×** — sistem sağlıklıyken bile bütçe aşılmış |

Karar: **L-01 = p99 ≤ 5 sn, gerekçesi 36× bozulma payı.** Savunulabilir cümle şu: *"Normalde 5 saniye, kötü günde 3 dakika; domain 3 dakikaya kadar dayanıyor."*

İkinci gerekçe — dürüst olmak gerekirse neredeyse eşit ağırlıkta: **5 sn eşiği mimari sınıfı değiştiren eşiktir.** Micro-batch'i eler, event-by-event işleme ve in-memory state zorunlu kılar. Projenin öğrenme amacı tam olarak o sınıf. Bunu da yazıyoruz; gizli kalan gerekçe, gerekçe değildir.

### 1.3 Segment karşılaştırması — gecikme hedefi mimari sınıfı nasıl değiştiriyor

| | Segment A (ilaç) | Segment B (gıda) | Segment C (kuru yük) |
|---|---|---|---|
| Sisteme kalan bütçe | ~3 dk | ~95 dk | saatler |
| Seçilecek SLO (bozulma payı) | **5 sn** (36×) | **60 sn** (95×) | **5 dk** (saatlerce) |
| Mimari sınıf | event-by-event stream | **micro-batch (30 sn) yeterli** | periyodik batch job |
| Durum (state) nerede | in-memory + cache | batch job'ın belleği | yok, sorgu anında hesaplanır |
| Kafka gerekli mi | Evet (sıralı log + replay) | Evet, ama partition ihtiyacı düşük | **Hayır** — object storage + cron yeter |
| Cihaz → sunucu | sürekli bağlantı, **20.000 req/sn** | 5 dk'lık paketler → **~330 req/sn** `100.000/300` | saatlik dosya upload → **~30 req/sn** `100.000/3.600` |
| Altyapı payı (tahmin) | **1×** (referans) | ~0,2× | ~0,02× |

**Okunması gereken satır son satır: aynı iş gereksinimi, gecikme hedefi 5 sn'den 5 dk'ya çıktığında altyapı ~50 kat ucuzluyor.** Eğri doğrusal değil, basamaklı — maliyet, mimari sınıf değiştiğinde atlıyor. Ölçülmüş değerler Adım 7'den sonra bu tabloya eklenecek.

### 1.4 Edge/gateway alarmı neden yok

§0'daki "müdahale eden insan ofistedir" cümlesi yüzünden. Edge'de alarm üretmek ağdan tasarruf ettirir, ama müdahale zinciri yine ağdan geçiyor — kazandığı 5 saniye, 10 dakikalık insan zincirinin içinde kaybolur. Karşılığında FR-09 (kuralların canlı güncellenmesi) bozulur: 24 saat offline kalan cihaz 24 saat eski kuralla alarm üretir. **Bedeli gereksinim seviyesinde, kazancı ölçülemez seviyede.**

---

## 2. Hesaplar

### 2.1 Reading payload boyutu

| Format | Hesap | Sonuç |
|---|---|---|
| JSON | assetId (36 B string) + eventTime (ISO-8601, 24 B) + lat/lon/speed/temp/humidity (~5 × 15 B) + alan adları ve noktalama | **~200 B** |
| Protobuf | assetId 16 B bytes + eventTime int64 + lat/lon sfixed32 (1e7 ölçekli) + 3 × varint | **~50 B** |

Fark **4×**. Nerede önemli olduğu §2.2–2.3'te belli olacak.

### 2.2 Ingest bant genişliği

```
ortalama  = 20.000 event/sn × 200 B  =  4 MB/sn  ≈  32 Mbit/sn   (JSON)
tepe (×2)                            =  8 MB/sn  ≈  64 Mbit/sn
Protobuf karşılığı                   =  1 MB/sn ortalama, 2 MB/sn tepe
```

**Sonuç: serialization formatı bir bant genişliği kararı değil.** 8 MB/sn, tek bir 1 Gbit NIC'in %6'sı. 4× tasarruf burada hiçbir şeyi değiştirmiyor.

### 2.3 Kafka

```
günlük hacim = 1,73e9 event × 200 B  =  346 GB/gün   (JSON)
retention 7 gün                      =  2,4 TB
× replication factor 3               =  ~7 TB toplam disk
Protobuf karşılığı                   =  ~1,8 TB
```

**Retention neden 7 gün:** D-03 geç veriyi 24 saate kadar kabul ediyor. Geç gelen bir Reading'i doğru değerlendirebilmek için (§2.5) o pencerenin log'da hâlâ durması gerekiyor. 24 saat + yeniden işleme payı = 7 gün.

**Partition sayısı.** Sıralama birimi `assetId`: aynı Asset'in okumaları tek partition'da, sırayla. Throughput partition sayısını belirlemiyor (partition başına 420 event/sn, 84 KB/sn — sınırın çok altında). Belirleyen şey **consumer paralelliği ve repartition'ın maliyeti**: partition sayısını sonradan artırmak key→partition eşlemesini bozar ve Asset bazlı sıralamayı tarihsel olarak kırar. Yani bu tek yönlü bir kapı.

```
seçim = 48 partition
  → 1, 2, 3, 4, 6, 8, 12, 16, 24, 48 consumer'da eşit dağılır (dengeli rebalance)
  → bugün 4 consumer ile çalışıp, repartition etmeden 48'e kadar büyüyebiliriz
  → 48 × RF3 = 144 replica / 3 broker = broker başına 48 partition (sorun değil)
partition key = tenantId:assetId   → C-02'nin tek yönlü kapı önlemi burada somutlaşıyor
```

### 2.4 Stream processing state boyutu — modelin kırıldığı yer

**State nedir ve neden boyutu önemli:** stream processor event'leri tek tek, sonsuz bir akıştan okur. Event başına veritabanı sorgusu yapamaz (20.000/sn'de imkânsız). "8 °C üzerinde **2 dakika sürekli**" gibi bir kuralı ise tek bir event cevaplayamaz — processor event'ler arasında bir şey **hatırlamak** zorundadır. O hatırladığı şeye `state` denir, RAM'de durur, ve **key başına** (burada `assetId`) tutulur. Yani Asset başına ne tutarsanız **100.000 ile çarpılır.**

İki farklı kural şekli, iki farklı mertebe:

| Kural şekli | State'te ne durur | Hesap | Boyut |
|---|---|---|---|
| **(a) Eşik + sürekli süre**<br>*"8 °C üstü, 2 dk sürekli"* | Asset+kural başına: streak'in **başlangıç zamanı** (8 B) + tetiklendi bayrağı → 16 B. Ayrıca Asset başına son bilinen durum (100 B). | `100K × 7 × 16 B + 100K × 100 B` | **~25 MB** |
| (b) Pencere ortalaması (ham veri)<br>*"son 10 dk ortalaması > 8 °C"* | Pencere içindeki **tüm Reading'ler** | `(600/5) × 200 B × 100K` | **~2,9 GB** |
| (b′) Aynı kural, kovalanmış | Kova başına `sum+count` (16 B), 60 sn'lik 10 kova | `10 × 16 B × 7 × 100K` | **~134 MB** |

**(a) ile (b) arasındaki fark bir optimizasyon değil, cins farkı:**

```
(a)  state'te SONUÇ durur      →  boyut = O(asset × kural)
(b)  state'te VERİ durur       →  boyut = O(asset × pencere_süresi / örnekleme_sıklığı)
```

(a)'da örnekleme sıklığını 5 sn'den 50 ms'ye çıkarsan da, pencereyi 2 dk'dan 2 güne çıkarsan da **state aynı 16 byte kalır** — çünkü sakladığın şey veri değil, "bu streak şu an ne zaman başladı" bilgisi. Yeni event gelince:

```
if reading.temp > 8:
    if streak_start is None: streak_start = reading.event_time      # streak başladı
    elif reading.event_time - streak_start >= 2dk and not fired:
        emit Violation; fired = True
else:
    streak_start = None; fired = False                               # streak kırıldı, sıfırla
```

(b)'de ise ortalamayı güncellemek için **pencereden çıkan okumanın değerini bilmek şart** (ortalamadan çıkarmak için). O yüzden ham okumaları tutmak zorundasın, ve state hem örnekleme sıklığıyla hem pencere süresiyle **doğru orantılı büyür**.

(b′) satırı dürüstlük payı: (b) 2,9 GB olmak zorunda değil — kovalayarak 134 MB'a indirilebilir, karşılığında pencerenin kenarı 60 sn hassasiyete düşer. Yani (b) **imkânsız değil, pahalı ve daha karmaşık.**

#### Karar ve nedenselliğin yönü

> **Dikkat: (b) ve (b′)'yi eleyen şey C-01 değil.** C-01 kural *sayısını* ve *kapsamını* söylüyor (Asset Type bazında ~5-10 global kural), şeklini söylemiyor. Nedensellik ters yönde işledi: **BOTE state hesabını yaptı, sonuç C-01'e yeni bir kısıt olarak geri yazıldı.** Hesap olmadan C-01 bu kısıtı üretemezdi — zaten BOTE'nin varlık sebebi bu.

Karar (**B-02**): **C-01, kural şekli olarak "eşik + sürekli süre" ile sınırlandırılıyor.** Gerekçe: ilk dikey kesit için 25 MB'lık state tek bir process'in belleğinde durur, snapshot'ı ucuzdur, çökme sonrası yeniden kurulması saniyeler alır. (b) seçilse state yönetimi tek başına bir alt proje olurdu — ki slice 1'in amacı o değil.

Bedeli yazıyoruz: kapı açılıp kapandığında oluşan kısa sıcaklık sıçraması, ortalama tabanlı bir kuralda yutulurdu. Eşik+süre modelinde bu gürültüyü **duration penceresinin (2 dk) filtrelemesi** gerekiyor — yani pencere, (b)'nin yapacağı işi kabaca yapan tek mekanizma hâline geliyor.

### 2.5 Geç gelen veri nereden işlenir — §2.4'ün zorunlu sonucu

(a) modelinde state yalnızca "şu anki streak"i biliyor. 6 saat önceye ait bir Reading geldiğinde o anın streak'i artık state'te yok — **canlı state üzerinden geriye dönük değerlendirme matematiksel olarak imkânsız.**

#### (c) Bu sorunu state ile çözmeye kalkarsak

D-03 geç veriyi **24 saate** kadar kabul ediyor. Herhangi bir anın durumunu yeniden kurabilmek için, son 24 saatin **tüm Reading'lerini** Asset başına state'te tutmak gerekir:

```
24 saat / 5 sn = 17.280 Reading/Asset
17.280 × 200 B = ~3,5 MB/Asset
× 100.000 Asset × 1,2 overhead = ~415 GB
```

**346 → 415 GB'ı üreten şey bir kuralın penceresi değil, geç veri toleransının penceresi.** (a) ile arasında **~16.000×** fark var ve bu iki ayrı mimari demek:

| | (a) 25 MB | (c) 415 GB |
|---|---|---|
| Nerede durur | process belleği | disk-backed state store (RocksDB tarzı) |
| Event başına | bellek erişimi | **disk IO** |
| Çökme sonrası toparlanma | saniyeler | 415 GB'ın geri yüklenmesi |
| Operasyonel yük | yok | yeni bir sistemin bakımı |

**Ve en belirleyicisi: bu veri zaten Kafka'da duruyor** (7 gün retention, 3 broker'da ~7 TB). (c) seçmek, aynı veriyi ikinci kez saklamak demek.

```
sonuç: FR-13 (geriye dönük Alert) canlı consumer'dan karşılanamaz
       → ayrı bir "late data reprocessing" consumer'ı log'u ilgili offset'ten yeniden okur
       → bellek yerine CPU ödenir, ve yalnızca geç veri geldiğinde (nadir)
       → Kafka retention'ın 7 gün olmasının ikinci gerekçesi bu
```

BOTE bir tasarım sorusunu kapattı: **hot path ile late-data path aynı consumer olamaz.** Adım 3'e taşınıyor.

### 2.6 Hesaplama (CPU) — darboğaz değil

```
event başına iş = deserialize (~2 µs) + state lookup (~0,1 µs) + 7 eşik karşılaştırması + state write
tutucu tahmin   = 20 µs/event
20.000 event/sn × 20 µs = 0,4 core-saniye/saniye → ~0,4 core
tepe ×2 ve headroom ×2 ile → ~2 core
```

**C-01'deki 140.000 değerlendirme/sn kulağa büyük geliyor, tek çekirdeğin altında kalıyor.** Yani stream processing bir CPU problemi değil; serialization, state erişimi ve IO problemi. Teknoloji ADR'sinde "yüksek throughput" gerekçesi **kullanılamaz** — doğru gerekçe state yönetimi, event-time semantiği ve replay.

### 2.7 Ingest API

```
istek hızı         = 20.000 req/sn   (S-02 + L-01 batch'lemeyi eliyor: 5 sn'lik veriyi
                                      biriktirmek bütçenin tamamını yer)
eşzamanlı bağlantı = 100.000         (C-03: Asset ↔ Device 1:1, cihaz başına kalıcı bağlantı)

pod kapasitesi (tutucu) = 5.000 req/sn
ortalama  → 4 pod
tepe ×2   → 8 pod
N+1       → 9 pod        (pod başına ~11.000 eşzamanlı bağlantı)
```

**Kesinti sonrası TLS handshake fırtınası:** 100.000 cihaz aynı anda yeniden bağlanırsa, pod başına ~2.000 handshake/sn kapasitesiyle `100.000 / (9 × 2.000) ≈ 6 sn`. Kabul edilebilir — **ama yalnızca cihazlar jitter'lı yeniden bağlanıyorsa.** Jitter yoksa ilk saniyede 100.000 handshake gelir ve kabul edilen istek hızı sıfıra düşer. B-07 kararının ilk gerekçesi bu.

### 2.8 Recovery burst — "×2 ile yakalama" ne demek

**Kilit gözlem: veri üretimi hiç durmaz.** Ingest kesintiye girdiğinde kamyonlar yolda, sensörler ölçmeye devam ediyor; **20.000 event/sn üretilmeye devam ediyor.** Fark şu ki artık cihazların buffer'ına yazılıyor (D-03).

Kesinti bittiğinde cihazlar iki şeyi birlikte göndermek ister: **birikmiş backlog + o an üretilmeye devam eden yeni veri.** Yani kapasitenin bir kısmı zaten yeni veriye gidiyor; backlog'u eritmeye sadece **taban hızın üzerinde kalan fazla** kullanılabilir:

```
backlog              = kesinti_süresi × 20.000
drenaj kapasitesi    = kapasite − 20.000            (taban hızın ÜZERİNDEKİ fazla)
                     = 20.000 × (tepe − 1)

yakalama süresi      = backlog / drenaj
                     = kesinti_süresi / (tepe − 1)        ← tüm mesele bu formül
```

"Yakalama" (catch-up) = **consumer lag'in yeniden ~0'a dönmesi**, yani sistemin tekrar *şu anki* veriyi işlemeye başlaması.

| Tepe faktörü | Fazla kapasite | Yakalama süresi | 24 saat kesinti için | Ingest pod |
|---|---|---|---|---|
| ×1,1 | 0,1× | kesinti × 10 | **10 gün** | 6 |
| ×1,5 | 0,5× | kesinti × 2 | 2 gün | 7 |
| **×2** | 1× | **kesinti × 1** | **24 saat** | **9** |
| ×3 | 2× | kesinti / 2 | 12 saat | 13 |
| ×4 | 3× | kesinti / 3 | 8 saat | 17 |

**Tuzak ×1,1 satırında:** "%10 headroom bıraktım" diyen bir sistemde 1 saatlik kesinti **10 saat** sürer. Tepe faktörü bir konfor payı değil, **toparlanma hızının kendisi.**

Karar: **S-05 = ×2.** Bedeli açıkça kabul ediyoruz: *bir günlük kesintinin telafisi bir gün sürer.*

#### Yakalama süresi boyunca ne oluyor

Bu, kapasite hesabının sadece bir sayı olmadığı yer:

1. **L-01 ihlal ediliyor** — işlenen veri saatler öncesine ait. Süre boyunca SLO tutmaz. (SLI-01'in filtresinin tek sebebi bu.)
2. **Alert'ler geriye dönük geliyor** — 20 saat önceki bir sıcaklık ihlalinin alarmı şimdi düşüyor. Referans senaryodaki 15 dakikalık bütçe çoktan geçmiş; **ilaç partisi zaten kaybedilmiş.** Yani 24 saatlik bir kesintide ×2 ile toparlanmak "veri kaybı yok" demek, "iş kaybı yok" demek değil.
3. **Buffer sınırı sert bir duvar** — D-03 cihaz buffer'ını 24 saate bağlıyor. Kesinti 24 saati geçerse veri **gerçekten kaybolur**, tepe faktörü ne olursa olsun.

#### Hangi katmanda ×2 gerekli

| Katman | ×2 neden gerekli | Gecikse ne olur |
|---|---|---|
| Ingest API | Veriyi cihazların buffer'ından **almak** için | Buffer dolar → 24 saatlik duvara yaklaşılır → **veri kaybı** |
| Stream processor | Alarmların zamanında üretilmesi için | Backlog Kafka'da bekler → **gecikme**, kayıp değil |

**Kafka burst'ü yutuyor**, yani iki katmanın tepe faktörü aynı olmak zorunda değil: ingest'teki ×2 bir *dayanıklılık* kararı, stream processor'daki ×2 bir *gecikme* kararı. Slice 1'de ikisine de ×2 veriyoruz; ayrıştırmak Faz 2'nin optimizasyonu.

Karar: **S-05 = ×2.** Bedeli açıkça kabul ediyoruz: *bir günlük kesintinin telafisi bir gün sürer.*

**Buradan uçtan uca bir bağlantı çıkıyor:** recovery sırasında işlenen Reading'lerin `event_time`'ı saatler öncesine ait. Bunları L-01'in ölçümüne dahil ederseniz **her kesinti SLO'yu otomatik ihlal eder ve error budget tamamen tükenir** — hâlbuki sistem tam olarak tasarlandığı gibi davranmıştır. Bu yüzden L-01'in SLI'ı geç gelen veriyi dışlamak zorundadır (bkz. `02-requirements/nfr-slo.md` §7, SLI-01). **D-03 → A-01 → S-05 → SLI-01** zinciri burada kapanıyor.

### 2.9 Hot path state store (Redis)

```
100.000 Asset × ~300 B (overhead dahil) = ~30 MB
dashboard okuma: 50 eşzamanlı dispatcher × ~100 asset/viewport × 1/sn = ~5.000 read/sn
```

**30 MB ve 5.000 read/sn, Redis için anlamsız derecede küçük.** Yani Redis bir **kapasite kararı değil**; gerekçesi (1) durumun pod'lar arasında paylaşılması, (2) pod restart'ında kaybolmaması. ADR'de gerekçe olarak "ölçek" yazılamaz.

### 2.10 Cold path depolama — üç TBD'den birini kapatan sayı

```
90 gün ham Reading (R-01) = 1,73e9/gün × 90 = ~156 MİLYAR satır
ham boyut                 = 346 GB/gün × 90 = ~31 TB
columnar + time-series sıkıştırma (10–20×)  = ~2–3 TB
sürekli yazma hızı        = 20.000 satır/sn (10.000'lik batch → 2 commit/sn)
```

20.000 insert/sn, PostgreSQL için batch'leme ile ulaşılabilir bir sayı. **Kıran şey satır sayısı:** tek tabloda 156 milyar satır + index bakımı + 90 günlük retention silme işlemi. Bunu düz PostgreSQL'de çözmek, partition yönetimini ve sıkıştırmayı elle yazmak demek — yani TimescaleDB'yi baştan inşa etmek.

**Bu tek satır, time-series storage TBD'sini kapatacak sayıdır.** Karar Adım 4'teki ADR'de verilecek.

### 2.11 Alert hacmi — karar gerektirmediği ortaya çıkan satır

```
sıcaklık ihlali: günde Asset'lerin ~%0,5'i  → ~500 Alert/gün
Stale Asset:     günde Asset'lerin ~%2'si   → ~2.000 Alert/gün
toplam ≈ 2.500 Alert/gün ≈ 0,03 Alert/sn
```

Ingest'in **5 mertebe** altında. **Sonuç: Alert deposu bir karar gerektirmiyor** — PostgreSQL fazlasıyla yeter, ADR yazılmasına değmez.

Dedup (D-05) olmasaydı: 10 dakikalık bir ihlal, 5 saniyede bir Alert → ihlal başına 120 Alert → 60.000/gün. **Bu da kapasite için önemsiz.** Yani **D-05 bir kapasite gereksinimi değil, operatörün kullanılabilirliği gereksinimidir** — ve bu onu daha az değil daha çok kritik yapıyor, çünkü kapasite metrikleri ihlal edildiğini asla göstermez.

---

## 3. Sonuç: BOTE'nin ürettiği kararlar

| # | Karar | Dayanak |
|---|---|---|
| B-01 | L-01 = p99 ≤ 5 sn | §1.2 — 3 dk domain bütçesi / 36× bozulma payı |
| B-02 | Kural modeli **eşik + sürekli süre** ile sınırlı | §2.4 — state 25 MB vs 2,9 GB (pencere kuralı) |
| B-03 | Late-data path, hot path'ten **ayrı consumer** | §2.5 — (a) modelinde geriye dönük hesap imkânsız |
| B-04 | Kafka: **48 partition**, RF 3, 7 gün retention, key `tenantId:assetId` | §2.3 |
| B-05 | Serialization: **JSON** (slice 1) | §2.2 — 4× tasarruf hiçbir darboğazı açmıyor; en az kodla çalışan seçenek |
| B-06 | S-05 tepe faktörü **×2**; yakalama süresi ≈ kesinti süresi | §2.8 |
| B-07 | Recovery burst politikası: **sunucu tarafı back-pressure + `Retry-After`** | §2.7 — alternatifi 100.000 firmware'in doğru davranmasına güvenmek |
| B-08 | Headroom: tepe × 2, stateless katmanlarda N+1 | Varsayım (politika) |
| B-09 | Alert deposu PostgreSQL, **ADR yazılmayacak** | §2.11 — ingest'in 5 mertebe altında |
| B-10 | Analytics DB **TBD olarak kalıyor** | FR-19 agregasyonun Asset kardinalitesini söylemiyor; karar verecek sayı yok |

### Altyapı mertebesi

| Bileşen | Adet / boyut |
|---|---|
| Ingest API pod | 9 × (2 vCPU, 1 GB) |
| Stream processor | 4 instance × 2 vCPU *(hesap 1 instance'ı gerektiriyor; 4, partition paralelliği ve arıza toleransı için)* |
| Kafka broker | 3 × (4 vCPU, ~2,5 TB disk) |
| Redis | 1 primary + 1 replica, 1 GB |
| PostgreSQL | 1 primary + 1 replica (Alert, kural, Asset registry — hepsi küçük) |
| Time-series store | Faz 2, ~3 TB sıkıştırılmış |
| **Toplam** | **~50 vCPU; headroom ile ~100 vCPU ≈ 8 vCPU'luk 10 node** |

> **Dürüst sanity check:** 10 node'a 20.000 event/sn = node başına 2.000 event/sn. İyi ayarlanmış **tek bir sunucu** bu şekildeki 20.000 event/sn'yi kaldırır. Yani bu kümenin boyutunu belirleyen şey **throughput değil; erişilebilirlik (A-01/A-03), izolasyon ve arıza toleransı.** Bu cümleyi ADR'lerde kullanacağız — "ölçek için dağıttık" demek bu projede yanlış olur.

---

## 4. Gereksinimlere geri dönen bulgular

| Bulgu | Etkilenen satır | Durum |
|---|---|---|
| Kural modeli eşik+süre ile sınırlanıyor | C-01 | B-02 — Adım 3'te şekillenecek |
| Late data ayrı consumer'dan işlenir | D-03, D-04, FR-13 | B-03 — Adım 3'ün ana konusu |
| Tepe faktörü | S-05 | Kapandı (B-06) |
| Reading payload = ~200 B (JSON) | "açık kalan sayılar" | Kapandı (B-05) |
| Kafka partition = 48 | "açık kalan sayılar" | Kapandı (B-04) |
| Alert hacmi ≈ 0,03/sn | "açık kalan sayılar" | Kapandı (B-09) |
| Node sayısı ≈ 10 | "açık kalan sayılar" | Kapandı; **maliyet hesabı kapsam dışı** (gelir amacı yok, maliyet karar sürücüsü değil) |

### Bilinçli olarak hesaplanmayanlar

- **Maliyet / platform karşılaştırması** (self-hosted vs managed) — kapsam dışı. Sonucu: ADR'lerde "neden managed service değil" sorusu sayıyla savunulmayacak, gerekçe "kapsam dışı" olacak.
- **Telemetri tipine göre farklı örnekleme sıklığı** — S-02 tek sıklıkta (5 sn) bırakıldı. Tipe göre ayırmak bu dosyadaki tüm sayıları **düşürür**; yani 5 sn en kötü durumdur ve BOTE geçerli kalır. Bilinen optimizasyon, uygulanmadı.
- **Tipe göre farklı retention** — R-01 tek değerde (90 gün) bırakıldı. Cold path Faz 2; slice 1 kodunu etkilemiyor.
- **Duyarlılık analizi ve gecikme-maliyet eğrisi** — Adım 7'den sonra. O noktada elde **ölçülmüş bir nokta** olacak; şimdi çizilse üç kurgusal noktadan oluşurdu.
