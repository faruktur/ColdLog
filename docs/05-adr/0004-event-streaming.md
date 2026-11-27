# ADR-0004: Ingest ile kural değerlendirmesi arasındaki tampon, replay edilebilir ve key bazında sıralı bir log (Kafka) olacak

| | |
|---|---|
| **Durum** | **Kabul** |
| **Tarih** | 2026-11-27 |
| **İlgili** | `02-requirements/nfr-slo.md` D-01/D-02/D-03/A-01/S-05, `02-requirements/functional.md` FR-01/FR-02/FR-04/FR-05, `03-capacity/bote-model.md` §2.3/§2.5/§2.8, `04-design/hld.md` §1/§2.1/§3.3/§7, ADR-0002, ADR-0003 |

## Bağlam

Ingest ile kural değerlendirmesi arasında bir tampon var. Bu ADR'ye kadar o tampon **kayıtsız bir bağımlılıktı**: parametreleri B-04'te sabitlenmiş (48 partition, RF 3, 7 gün), fakat kararın kendisi hiçbir yerde gerekçelenmemişti. Oysa tasarımın birbirinden bağımsız görünen dört sonucu bu bileşenin garantilerine dayanıyor. Teknoloji adı kullanmadan, o dört iş:

**1. Dayanıklılık sınırı burada.** FR-01 + D-01: ack dönüldükten sonra kayıp sıfır. `hld.md` §1 ack'in anlamını *"tampona yazıldı ve yeterli sayıda replikaya ulaştı"* olarak tanımladı — *"işlendi"* değil. Yani cihazın buffer'ını boşaltmasına izin veren şey kural motoru değil, **tamponun replikasyonu**. Tampon bu garantiyi veremiyorsa D-01 yalandır.

**2. Key bazında sıra korunmak zorunda.** `hld.md` §2.1'in tüm sonucu — *geç ama sıralı* okumaların hot path tarafından sıradan trafik gibi işlenebilmesi, dolayısıyla FR-13'ün ayrı bir mekanizma gerektirmemesi — şu zincire dayanıyor: cihaz FIFO buffer'ı (C-03: Asset ↔ Device 1:1) → tek Asset'in okumaları tek kuyrukta, sırayla → Asset state monoton ilerler. **Tampon aynı Asset'in okumalarını paralel tüketicilere dağıtırsa bu zincir kopar** ve 24 saatlik bir backlog, hot path için sıradan trafik olmaktan çıkıp "sıra dışı" yığınına dönüşür — H-03 gereği hiçbiri değerlendirilmez.

**3. Geçmiş, günler boyunca yeniden okunabilir olmak zorunda.** Üç ayrı yer bunu istiyor: late path consumer'ının ilgili offset'ten yeniden okuması (`bote-model.md` §2.5), replay güvenliğinin dayandığı "aynı aralığı yeniden üret" davranışı (`hld.md` §3.3), ve ADR-0003'ün state restore mekanizması (restore = geriye sarmak). §2.5'in (c) seçeneğini — 24 saatlik veriyi state'te tutmak, 415 GB — eleyen argüman birebir şu cümleydi: ***"bu veri zaten tamponda duruyor."*** O cümle doğru değilse 415 GB geri gelir.

**4. Tüketici paralelliği buradan gelir.** 140.000 kural değerlendirmesi/sn (C-01) tek bir tüketicide değerlendirilmeyecek; paralellik birimi tamponun bölümlenmesidir. Bölüm sayısını sonradan artırmak key→bölüm eşlemesini bozar ve Asset bazlı sıralamayı **tarihsel olarak** kırar — yani bu tek yönlü bir kapı (§2.3).

**Gerilim:** bu dört işi tek bir bileşenden birden istiyoruz. Klasik bir iş kuyruğu 1 ve 4'ü verir, 2 ve 3'ü **tasarımı gereği** vermez (mesaj tüketilince silinir, sıra tüketici sayısıyla bozulur). Bir veritabanı 1 ve 3'ü verir, 4'ü ve akış tüketimini (back-pressure dahil) bize yazdırır. Yani soru "hangi ürün" değil, **"hangi bileşen sınıfı"**: tampon bir *kuyruk* mu, bir *tablo* mu, yoksa *bölümlenmiş ve kalıcı bir log* mu?

## Hesap dayanağı

> Ortalama **20.000 event/sn**, tepe **40.000/sn** (B-06, §2.8) · **346 GB/gün** JSON (§2.3, B-05) · 7 gün retention = **2,4 TB**, × RF 3 ≈ **7 TB** disk · **48 partition** → partition başına **420 event/sn, 84 KB/sn** (§2.3) · Geç veri toleransı **24 saat** (D-03) · Alert hacmi 0,03/sn (§2.11)

**Bu kararı throughput zorlamıyor.** Partition başına 84 KB/sn, herhangi bir mesajlaşma sisteminin sınırının mertebelerce altında; §3'ün dürüst sanity check'i burada da geçerli — *"ölçek için log aldık"* cümlesi bu projede yazılamaz.

Kararı zorlayan üç sayı şunlar:

| Sayı | Neyi zorluyor |
|---|---|
| **24 saat** (D-03) | Tamponun geçmişi, geç verinin penceresinden **uzun** olmak zorunda → retention günler mertebesinde → mesajı tüketince silen bir sınıf elenir |
| **100.000 Asset × tek kuyruk** (C-03) | Key bazında sıralama, 100.000 ayrı kuyruk kurmadan sağlanmak zorunda → sıralamanın key'e göre **bölümlenmeyle** gelmesi gerekir |
| **2,4 TB / 7 gün** | Bu hacmin ikinci bir kopyasını (veritabanı tablosu olarak) tutmak §2.5'in kendi argümanıyla çelişir |

## Değerlendirilen alternatifler

| Alternatif | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|
| **① Hiçbir şey yapmama** — Ingest API kural motorunu senkron çağırır, tampon yok | Yeni bileşen yok, 7 TB disk yok, en az operasyonel yük | Dayanıklılık sınırı kural motoruna kayar (ack = "işlendi") → D-01'in maliyeti artar; recovery burst (S-05 = ×2) doğrudan motora çarpar; replay edilecek bir yer yok → §2.5 (c) geri gelir (415 GB); `hld.md` §7'nin *"ingest'i kısmak kural motorunu kısmaktan önce gelir"* cümlesi anlamsızlaşır | Dört işin dördünü de kaybediyor. ADR-0003 ① ile aynı gerekçe, bu kez tampon tarafından |
| **② Klasik iş kuyruğu** (tüketilince silinen mesaj, tüketici başına ack) | Olgun, basit, iyi back-pressure, kurulumu ucuz | **(a)** Key bazında sıra yok: aynı Asset'in iki okuması iki tüketiciye gidebilir → §2.1'in zinciri kopar. 100.000 ayrı kuyruk ile taklit edilebilir, ki bu bir mimari değil bir arıza. **(b)** Geçmiş yok: mesaj tüketilince silinir → §3.3'ün replay güvenliği, §2.5'in late path'i ve ADR-0003'ün state restore'u dayanaksız kalır. **(c)** 24 saatlik geç veriyi yeniden değerlendirmek için verinin hâlâ orada olması gerekiyor | Dört işten ikisini (2 ve 3) **tasarımı gereği** veremiyor |
| **③ Veritabanı tablosu + polling** (mevcut PostgreSQL'i log olarak kullan) | **Yeni sistem yok** — en büyük operasyonel kazanç. Dayanıklılık, sıra (id) ve geçmiş hazır. Transaction sınırı Alert yazımıyla aynı veritabanında | 7 günde ~12 milyar satır + 2,4 TB; offset yönetimi, tüketici grubu, rebalance ve back-pressure **bizim kodumuzda**; ADR-0003'ün aldığı motor bir log bekliyor (konnektör yok, tüketimi biz yazarız); ve §2.10 zaten *"156 milyar satırı düz PostgreSQL'de çözmek TimescaleDB'yi baştan yazmaktır"* demişti — burada log'u baştan yazmak olur | ADR-0003'ün **yazmamayı seçtiği** mekanizmaların aynısını (offset/state tutarlılığı, rebalance) bu kez tampon tarafında elle yazmak |
| **④ Bölümlenmiş, kalıcı log — Kafka** *(seçilen)* | Dördü birden: `acks=all` + `min.insync.replicas` ile dayanıklılık sınırı (1), partition içi sıra + key'e göre yönlendirme (2), offset'li ve retention'lı geçmiş (3), tüketici grubu paralelliği (4). ADR-0003'ün motoruyla en olgun konnektör yüzeyi; ekosistem (schema registry, connect, exporter) hazır | 3 broker × ~2,5 TB disk — mimarinin **en disk-ağır** bileşeni. PostgreSQL'den sonra ikinci stateful sistem, ADR-0003'ün akış motorundan sonra üçüncü operasyonel yüzey. 48 partition tek yönlü kapı olarak kalıyor | — |
| **⑤ Bölümlenmiş log — Pulsar** | Aynı sınıf. Üstelik iki belgelenmiş acımıza doğrudan değiyor: `key_shared` abonelik ile **tüketici sayısı partition sayısından bağımsız** olabiliyor (48'lik tek yönlü kapı yumuşar), ve multi-tenancy ürünün içinde (C-02 rezervi) | İşletilecek bileşen sayısı daha fazla (broker + ayrı depolama katmanı + metadata); ADR-0003'ün motoruyla konnektör olgunluğu ve topluluk tecrübesi daha ince | **Çözdüğü iki şeyi biz bilinçli olarak erteledik:** C-02 kapsam dışı, 48 partition kapısı ise *baştan 48 seçilerek* (§2.3) zaten azaltıldı. Bugün ödenecek bedel (daha geniş operasyonel yüzey), ertelenmiş iki faydayı aşıyor |
| **⑥ Yönetilen log hizmeti** (bulut sağlayıcısının akış hizmeti veya yönetilen Kafka) | Aynı semantik, sıfır broker operasyonu, disk yönetimi yok | Maliyet; ortam bağımlılığı; k8s üzerinde stateful işletme pratiği bu projenin hedeflerinden biri | **Reddedilmedi — bu ADR'nin konusu değil.** Bu ADR *bileşen sınıfını* ve *protokolü* seçiyor; barındırma biçimi Adım 6'nın dağıtım kararı. Protokol aynı kaldığı sürece geçiş maliyeti düşük (bkz. Geri dönüş) |

### ② ve ③ neden aynı hatayı iki farklı yönden yapıyor

İkisi de tamponu **taşıma aracı** sanıyor. Bu tasarımda tampon bir taşıma aracı değil, **sistemin tek kaynak-of-truth'u olan olay kaydı**: 7 günlük geçmişi, late path'in girdisi, state restore'un kaynağı ve replay'in dayanağı. ② geçmişi atıyor (taşıma bitince mesaj gider), ③ geçmişi tutuyor ama akış tüketimini bize yazdırıyor. Dördü birden isteyen tek sınıf, **kalıcı ve bölümlenmiş log**.

## Karar

**Ingest ile kural değerlendirmesi arasındaki tampon, Kafka olacak.** Parametreler (B-04 ile sabitlenmiş olanlar dahil) kararın kendisidir, ayrıntı değil:

| Ayar | Değer | Hangi gereksinimi karşılıyor |
|---|---|---|
| `replication.factor` | **3** | D-01 |
| `min.insync.replicas` | **2** | D-01 — `hld.md` §1'deki ack tanımının "yeterli sayıda replika"sı budur |
| producer `acks` | **all** | D-01. `acks=1` seçilse ack *lider* broker'a yazıldığında dönerdi; lider o anda ölürse ack dönülmüş bir Reading kaybolur — yani D-01 tek bir ayarla sessizce ihlal edilebilir |
| producer `enable.idempotence` | **true** | Producer retry'ının ürettiği duplicate'i engeller. **D-02'yi ortadan kaldırmaz** (aşağıya bakın) |
| `partitions` | **48**, key = `tenantId:assetId` | §2.3 — key bazında sıra (Bağlam 2) + tüketici paralelliği (Bağlam 4) + C-02 rezervi |
| `retention.ms` | **7 gün** | D-03'ün 24 saati + yeniden işleme payı (§2.3, §2.5) |
| `cleanup.policy` | **delete** (compaction yok) | Aşağıda |
| Topic'ler | `telemetry.readings` (48p) · `telemetry.readings.outoforder` (`hld.md` §2.3) · `telemetry.readings.invalid` | Üçüncüsü FR-04'ü kapatıyor, aşağıda |

**`enable.idempotence` D-02'yi kaldırmıyor.** Sağladığı şey, *producer'ın* ağ retry'ında aynı batch'i iki kez yazmamasıdır. Oysa duplicate'in kaynağı D-02'de yazılı: **cihaz ack'i kaybedip yeniden gönderir** — bu, producer'ın göremediği, uygulama seviyesinde ayrı bir istektir. Dolayısıyla FR-02'nin idempotent işlemesi ve H-01'in (Alert = event-time aralığı + exclusion constraint) zorunluluğu **aynen devam eder**. ADR-0003 aynı uyarıyı motor tarafı için yapmıştı (*"framework aldık, idempotency gereksiz"* sonucu çıkarılmamalı); bu ADR tampon tarafı için tekrarlıyor: **hiçbir altyapı ayarı, cihazdan gelen duplicate'i çözmez.**

**Compaction neden yok.** Log-compaction (key başına yalnızca son değeri tut) cazip görünüyor: Asset'in son durumu bedavaya çıkar. Reddediliyor, çünkü ham okuma log'unun değeri **tam olarak** eski kayıtların durmasıdır (late path §2.5, replay §3.3, 90 günlük arşivin kaynağı R-01). Son-durum ihtiyacı ise zaten H-07'nin projeksiyonuyla karşılanıyor.

**`telemetry.readings.invalid` — FR-04'ün kapanmayan yarısı.** FR-04 reddedilen Reading'in *"kaybolmaması ve incelenebilir bir yere yazılması"* gerektiğini söylüyor; `hld.md` §1 ise reddi yalnızca bir **metrik** olarak gösteriyordu (`rejected_total`). Metrik bir sensörün bozulduğunu sayar, hangi payload'ın neden reddedildiğini söylemez. Bu ADR o yeri bir topic olarak tanımlıyor: reddedilen payload, ret sebebi ve `ingest_time` ile birlikte `telemetry.readings.invalid`'e yazılır (retention 7 gün, 1 partition — hacmi FR-05 reddi hariç ihmal edilebilir). **Tampon kararı alınırken kapanan, tampona ait olmayan bir boşluk.**

## Sonuçlar

- **Kazandığımız:**
  - D-01'in garantisi üç somut ayara indi (`RF=3`, `min.insync.replicas=2`, `acks=all`) — "veri kaybetmiyoruz" cümlesi artık denetlenebilir.
  - `hld.md` §2.1'in tüm sonucu (geç ≠ sıra dışı) sağlam bir zemine oturdu: partition içi sıra + key'e göre yönlendirme.
  - §2.5'in *"bu veri zaten log'da"* argümanı geçerli — 415 GB'lık (c) seçeneği kapalı kalıyor.
  - ADR-0003'ün state restore'u, late path'in yeniden okuması ve §3.3'ün replay'i tek mekanizmaya (offset) indi.
  - FR-04'ün "incelenebilir yer" şartı kapandı.
- **Kabul ettiğimiz bedel / teknik borç:**
  - **7 TB disk** ve mimarinin en disk-ağır bileşeni; 3 broker'ın işletilmesi (PostgreSQL'den sonra ikinci stateful sistem, ADR-0003'ün motorundan sonra üçüncü operasyonel yüzey). Adım 6'nın yükü yine büyüyor.
  - **48 partition tek yönlü kapı olarak kalıyor.** ⑤ bunu yumuşatabilirdi; seçmedik. Kapı, 48'in bugünkü ihtiyacın (4 tüketici) 12 katı seçilmesiyle azaltıldı, kaldırılmadı.
  - **B-05 (JSON) burada faturalanıyor:** 346 GB/gün → 7 TB. Protobuf'a geçiş aynı retention'ı ~1,8 TB'a indirirdi. Serialization kararını yeniden açacak sayı throughput değil, **disk**.
  - Üç topic'in şema uyumluluğu yönetilmesi gereken yeni bir yüzey (schema registry Adım 6'ya bırakıldı; Slice 1'de şema sözleşmesi dokümanla yürür).
- **Etkilenen bileşenler:** Ingest API (producer ayarları + invalid topic), Kural Motoru (tüketici grubu, offset/checkpoint ilişkisi — ADR-0003), Late Path Consumer, `hld.md` §1 diyagramı (invalid topic eklendi), Adım 5 C4 Level 2 (log, mimarinin merkezindeki container), Adım 6 (k8s üzerinde broker işletme, topic provisioning).

## Geri dönüş maliyeti

| Çıkış | Ne zaman gerekir | Maliyet | Neden |
|---|---|---|---|
| **④ → ⑥** (yönetilen hizmete / yönetilen Kafka'ya) | Broker işletme yükü taşınamazsa | **Düşük–Orta** | Protokol aynı; istemci yapılandırması ve veri göçü (veya 7 gün çift yazım) dışında kod değişmez. **Bu ADR'nin sınıf kararı olmasının pratik getirisi bu satırdır.** |
| ④ → ⑤ (başka bir log ürünü) | `key_shared` tipi bir tüketim modeline veya ürün-içi tenancy'ye gerçekten ihtiyaç duyulursa | **Yüksek** | Tüm producer/consumer katmanı, konnektörler, offset geçmişi ve 7 günlük veri. Veri göçü gerekir. |
| ④ → ② veya ③ | — | — | Dört işten ikisini veremedikleri için geri dönülecek yer değil |

| | |
|---|---|
| **Erken uyarı sinyali** | ① **`kafka_consumergroup_lag`** sürekli artıyorsa (tüketim yetişmiyor; B-04'ün metriği) ② **under-replicated / ISR shrink > 0** ise — `min.insync.replicas` sağlanamadığı an producer yazamaz, ingest 5xx döner ve **D-01'in garantisi A-01 kesintisine dönüşür**: bu ikisinin aynı sinyalden çıkması kararın en kritik yan etkisi ③ **disk kullanımı retention'ı 7 günün altına zorluyorsa** (§2.5'in *"veri zaten log'da"* argümanı çürür, late path çözümsüz kalır) ④ **partition skew:** en hızlı partition'ın hızı ortalamanın belirgin üstündeyse (key dağılımı bozuk → hot partition → paralellik işe yaramaz) ⑤ **produce p99 gecikmesi** SLI-02'nin 1 sn bütçesini yiyorsa |

### Durum neden *Kabul*

Beş sinyalin beşi de Slice 1 içinde çalışan bir bileşene ait; Adım 6'da broker exporter'ı + tüketici metrikleriyle observability'ye bağlanır ve Adım 7 load testinde ölçülür. README'nin *Kabul* şartı (erken uyarı sinyalinin gözlemlenebilir olması) sağlanıyor — ADR-0002'nin *Öneri* kalmasının sebebi olan "Faz 2 bileşeni" durumu burada yok.
