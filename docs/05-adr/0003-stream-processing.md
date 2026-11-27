# ADR-0003: Kural değerlendirmesi, yönetilen state'e sahip bir stream processing framework'ü (Flink) üzerinde çalışacak

| | |
|---|---|
| **Durum** | **Kabul** |
| **Tarih** | 2026-11-26 |
| **İlgili** | `03-capacity/bote-model.md` §2.4/§2.6/§2.3, `04-design/hld.md` §2.1/§2.2/§3/§7, `02-requirements/nfr-slo.md` L-01/D-01/D-02/C-01, ADR-0002 |

## Bağlam

Sistem, sonsuz bir okuma akışını tek tek işleyip kural ihlallerini tespit etmek zorunda. İşin şekli şu kısıtlar altında:

- **Kural tek bir event'le cevaplanamıyor.** *"8 °C üstünde 2 dakika sürekli"* gibi bir koşul, processor'ın event'ler arasında bir şey hatırlamasını gerektiriyor. Bu hatırlanan şey `assetId` başına tutulur — yani Asset başına ne tutulursa Asset sayısıyla çarpılır.
- **Gecikme bütçesi dar:** uçtan uca p99 ≤ 5 sn (L-01). Bu, akışı biriktirip toplu işleyen (micro-batch) yaklaşımları eliyor, event-by-event işleme zorunlu kılıyor.
- **Ack dönülmüş hiçbir okuma kaybolamaz** (D-01), delivery at-least-once (D-02) — yani aynı okuma birden fazla kez işlenebilir ve bu sonucu değiştirmemek zorunda.
- **Hatırlanan bilgi, bileşen çöktüğünde veya ölçeklendiğinde yeniden kurulmak zorunda.** Paralellik birimi log'un partition sayısıdır; partition el değiştirdiğinde ona ait hatırlanan bilgi de el değiştirir.

Gerilim şurada: **bugünkü kural şekliyle hatırlanacak bilgi çok küçük, ama bu küçüklük bir gereksinimin değil, bizim verdiğimiz bir kısıtın (B-02) sonucu.** Dolayısıyla karar, "bugünkü yüke en az kodla yetişmek" ile "kısıt gevşediğinde mimari sınıfı değişmeyecek bir temel kurmak" arasında.

## Hesap dayanağı

> Kural değerlendirmesi: **140.000 /sn** (C-01) · CPU: **0,40 core** ortalama, 0,80 tepe (`bote-model.md` §2.6) · State (model a): **25 MB** — tüm küme için (§2.4) · Paralellik: **48 partition**, partition başına 417 event/sn (§2.3, B-04) · Gecikme: p99 ≤ 5 sn (L-01)

Ham kapasite sayıları bu kararı **zorlamıyor**: 0,4 core tek çekirdeğin altında, 25 MB herhangi bir process'in belleğinde durur. ADR'de "yüksek throughput için framework aldık" cümlesi kullanılamaz (`bote-model.md` §3'ün dürüst sanity check'i).

Kararı zorlayan sayı, **state'in nasıl büyüdüğü** (§2.4'ün iki modeli). İki büyüme kaldıracını ayırmak gerekiyor çünkü mertebeleri farklı:

**Ölçek kaldıraçları — lineer, mimari sınıfı değiştirmiyor:**

| Senaryo | State (model a) | Çarpan |
|---|---|---|
| Bugün (100K asset, 7 kural, 100 B son-durum) | 25 MB | — |
| Kural 7 → 30 | 70 MB | 2,8× |
| Son-durum alanları 100 B → 500 B | 73 MB | 2,9× |
| Asset 100K → 1M | 254 MB | 10× |
| **Üçü birden** (1M asset, 30 kural, 500 B) | **1,2 GB** | 46× |

**Kural şekli kaldıracı — lineer değil, mimari sınıfı değiştiriyor:**

| Senaryo | State | Çarpan |
|---|---|---|
| Bugün, (a) state'te **sonuç** duruyor | 25 MB | — |
| **Tek bir kural** pencere ortalamasına dönerse → state'te **veri** durur | **2.880 MB** | **115×** |
| Üstüne asset 10× | 28.800 MB | 1.150× |
| Üstüne 500 B payload | 72.000 MB | 2.880× |

(Tablolar `03-capacity/bote.py` ile üretildi; §2.4'teki `O()` ayrımının sayısal hâli.)

**Kararı belirleyen cümle:** Senin saydığın ölçek kaldıraçlarının hepsi birden çekildiğinde state 46× büyüyor ve **hâlâ belleğe sığıyor**. Tek bir kuralın şeklinin değişmesi 115× yapıyor ve **bellekten çıkıyor**. Yani risk ölçekte değil, kural şeklinde — ve kural şeklini sınırlayan şey bir gereksinim değil, B-02.

## Değerlendirilen alternatifler

| Alternatif | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|
| **① Hiçbir şey yapma** — kuralı Ingest API içinde senkron değerlendir | Yeni bileşen yok, Kafka tüketicisi yok, en az kod | Üçü de aşağıda: ölçekleme, ack semantiği, degradation sırası | Kendi mevcut kararlarımızın üçünü birden bozuyor |
| **② Log consumer kütüphanesi + in-memory state** | Stack'ten çıkmaz (.NET); 25 MB bellekte; restore = log'u 2 dk geriye sarmak; mekanizma görünür | State tavanı RAM. Rebalance, state restore ve offset/state tutarlılığını **biz** yazarız — Slice 1'in en sessiz başarısızlık üreten yeri | Kural şekli değişirse mimari sınıf değiştirmek gerekir; ve en kritik mekanizmayı elle yazmak |
| **③ Framework, servis içi kütüphane olarak (Kafka Streams)** | Rebalance + state restore + disk destekli state hazır | **JVM kütüphanesidir: servisin kendisi JVM olmak zorunda.** Kural mantığı Java'da, HTTP katmanı C#'ta. .NET karşılığı yok; topluluk portu, sistemin doğruluk mekanizmasını yeniden-yazıma bağlamak olur | Stack'e verdiği hasar ④'ten büyük: tüm servisi ikinci dile taşır |
| **④ Framework, ayrı cluster olarak (Flink)** *(seçilen)* | Disk destekli, checkpoint'li, savepoint'li yönetilen state → 29 GB sıçramasını kaldırır. Olgun event-time/watermark. Operatör sözlüğü (`window`, `join`, `repartition`) hazır. Built-in back-pressure. **JVM sınırı operasyoneldir, kod içinde değil** — .NET tarafı .NET kalır | **Mimarinin en yüksek operasyonel yüklü bileşeni:** ikinci scheduler, checkpoint depolaması, savepoint yaşam döngüsü, job submit hattı, CI'da ikinci dil. 0,8 core'luk iş için | — |
| **⑤ Log consumer + state uzak bir store'da (Redis)** | **Processor gerçekten stateless olur** — rebalance restore problemi tamamen ortadan kalkar. State tavanı RAM'den Redis'e çıkar. Stack'ten çıkılmaz | Yük: ~20.000 read + ~5.000 write/sn (Asset başına tek hash fetch) — Redis bunu kaldırır. Ama **Redis hot path'in sert bağımlılığı olur**: A-03 (%99,9) Redis erişilebilirliğine bağlanır ve §2.9'un *"Redis bir kapasite kararı değil"* sonucu geçersiz olur | Kural şekli sıçramasını (29 GB) Redis'te karşılamak RAM fiyatıyla ödenir; ve A-03'ün bağımlılık yüzeyini büyütmek, kazandığı sadeliği aşan bir bedel |

### ① neden kırılıyor — üçü de kendi kararlarımızdan çıkıyor

1. **State Asset'e bağlı, Ingest API stateless olmak zorunda.** Ingest 9 pod ve tepede ×2 ölçekleniyor (B-06/B-08). Kural state'i Asset başına tutulduğu için pod'un Asset'e sticky olması gerekir → load balancer yerine partition'a göre yönlendirme gerekir → **log'un yaptığı iş yeniden icat edilir.**
2. **Ack'in anlamı bozulur.** `hld.md` §1'de ack = *"log'a yazıldı ve `min.insync.replicas` kadar replikaya ulaştı"*. Senkron değerlendirme ack'i *"işlendi"*ye çevirir → ingest gecikmesi kural motoruna bağlanır → D-01'in maliyeti artar.
3. **Degradation sırası tersine döner.** `hld.md` §7'nin en önemli satırı *"ingest'i kısmak, kural motorunu kısmaktan önce gelir"*. İkisi aynı process ise bu cümle anlamsızdır — birini kısmak diğerini kısmaktır.

## Karar

**Kural değerlendirmesi, yönetilen ve kalıcılaştırılmış state'e sahip ayrı bir stream processing cluster'ı (Flink) üzerinde çalışacak.** Gerekçe dört madde:

1. **Kural şekli opsiyonu.** Tek bir kuralın pencere tabanlı hâle gelmesi state'i 115× büyütüyor ve bellekten çıkarıyor. Disk destekli, checkpoint'li state bu sıçramayı mimari sınıf değiştirmeden kaldırır. ②'de aynı sıçrama yeni bir ADR ve yeni bir bileşen demektir.
2. **Event-time ve watermark makinesinin gerçek bir evi var.** H-03 (reorder buffer yok) **yalnızca hot path için** geçerli bir karardır; late path'in gecikme SLO'su yoktur (`karar-haritasi.md` B-03/H-03 satırları: *"SLO yok — bilinçli boşluk"*). FR-13'ün tam hâli oraya yazılacak ve watermark'a tam orada ihtiyaç duyulacak.
3. **Operatör sözlüğünün bugün boş olması kapsam artefaktıdır, problemin özelliği değil.** `window` B-02 yüzünden, `join` Shipment kapsam dışı olduğu için, `repartition` FR-19 Faz 2'de olduğu için boş. Üçünün de dokümanlarımızda "Faz 2" veya "kapsam dışı" yazıyor.
4. **Stateful işlemeden kaçınmıyoruz; doğru implementasyonunu satın alıyoruz.** Rebalance, state restore ve offset/state tutarlılığı Slice 1'in en sessiz başarısızlık üreten yeriydi — ②'de bunların hatasını *tespit etmek* için bir canary SLI'a (SLI-04) bel bağlamak zorunda kalırdık. Framework bu mekanizmaları bize bırakmıyor.

### Gerekçe olarak kullanılmayacak argüman

Bu karar tartışılırken *"in-memory consumer, mikroservis mimarisindeki stateless servis kuralına ters"* argümanı öne sürüldü. Bu argüman ADR'nin gerekçesi **değildir**, iki sebeple:

- "Stateless servis" kuralı **istek karşılayan** servisler hakkındadır: load balancer arkasındaki herhangi bir instance herhangi bir isteği karşılayabilsin diye vardır. Partition'a atanmış bir stream processor bu şekle ait değildir; log'un consumer group protokolü **tam olarak state'i partition'a bağlamak için** vardır. Ingest API stateless olmak zorundadır (①'in elenme gerekçesi bu), kural motoru değildir.
- **Flink stateless değildir.** TaskManager'ların yerel diskinde state tutar, periyodik checkpoint alır, rescale ederken savepoint'ten state'i yeniden dağıtır. Seçilen şey "state tutmayan çözüm" değil, "state'i yönetilen çözüm"dür.

O prensip tutarlı uygulandığında ④'ü değil **⑤'i** seçerdi — masadaki tek gerçekten stateless seçenek ⑤'ti ve A-03'ün bağımlılık yüzeyini büyüttüğü için reddedildi.

### Bu kararın dayandığı bahis

Hesap bu kararı tek başına belirlemiyor; şu soru belirliyor: **B-02 ("kural şekli eşik + sürekli süre ile sınırlı") ne kadar kalıcı bir kısıt?**

- Kalıcı bir kısıtsa ② doğru seçimdir — framework'ün sattığı şeylerin çoğu gerçekten karşılıksızdır.
- Önümüzdeki aylarda gevşeyecek bir kolaylıksa ④ doğru seçimdir — 115× sıçramayı in-memory consumer karşılamaz.

**Bu ADR, B-02'nin gevşeyeceği yönünde bir bahistir ve bahis hesaba değil, gereksinim oynaklığına dair tecrübeye dayanıyor.** Kayda geçen görüş ayrılığı: tek kişilik bir .NET projesinde JVM'in karmaşıklık maliyetinin opsiyon değerini aşabileceği, dolayısıyla ② + "saf fonksiyon" kısıtı + yeniden açma tetikleyicisinin de savunulabilir bir yol olduğu belirtildi. Karar ④ yönünde alındı.

**Bahsin kazanıldığının işareti:** ilk pencere tabanlı veya çoklu-akış kuralı talebi geldiğinde bu ADR'ye dokunmak gerekmiyorsa.
**Bahsin kaybedildiğinin işareti:** Slice 1 ve Faz 2 boyunca `window`, `join` ve `repartition` operatörlerinin hiçbiri kullanılmadıysa — o durumda ADR *Değiştirildi* durumuna geçer ve bedel, boşuna taşınmış bir operasyonel yük olarak yazılır.

## Sonuçlar

- **Kazandığımız:** Yönetilen, kalıcılaştırılmış state (kural şekli opsiyonu). Olgun event-time/watermark desteği → late path'in Faz 2 tasarımı hazır mekanizmalara oturur. Built-in back-pressure → `hld.md` §7'nin ④. maddesi framework'ün kendi mekanizmasıyla desteklenir. Rebalance ve state restore doğruluğu bizim kodumuzda değil.
- **Kabul ettiğimiz bedel / teknik borç:**
  - **Adım 6 (dikey kesit kodu) büyüyor:** k8s üzerinde Flink dağıtımı, checkpoint depolaması, job submit hattı, CI'da ikinci bir dil. Projenin başında konan *"önceliğim dikey kesiti tamamlamak"* hedefine karşı çalışan bilinçli bir maliyet.
  - **Exactly-once Alert store'a ulaşmıyor.** Framework'ün transactional garantisi log → log sınırları içindedir; Alert yazımız PostgreSQL'e gidiyor ve o transaction'ın içinde değil. **Yani H-01 (Alert = event-time aralığı + exclusion constraint) framework alınsa da alınmasa da zorunludur.** Bu ADR, H-01'e bağımlıdır; ileride "framework aldık, idempotency gereksiz" sonucu çıkarılmamalı.
  - Checkpoint aralığı yeni bir ayar düğmesi: kısa aralık = hızlı toparlanma + sürekli I/O; uzun aralık = düşük I/O + çöküşte daha fazla yeniden işleme. L-01 bütçesi içinde ayarlanacak.
  - İş hacmi (0,8 core tepe) ile operasyonel yük arasındaki oransızlık kalıcıdır ve kabul edilmiştir.
- **Etkilenen bileşenler:** Hot Path Consumer, Late Path Consumer (Faz 2), `bote-model.md` §3 altyapı tablosu (stream processor satırı), Adım 5 C4 Level 2 (container sınırı ve stateful etiketi), Adım 6 CI/deploy.

**Kapasite etkisi yok:** JobManager (HA için 2 × 1 vCPU) + TaskManager (3 × 2 vCPU) ≈ 8 vCPU — mevcut planlanan 4 × 2 vCPU ile aynı mertebe. Bu kararın bedeli vCPU değil, **operasyonel yüzeydir.** (`bote-model.md` §3'ün "kümenin boyutunu throughput belirlemiyor" sonucunun bu karardaki karşılığı.)

### Çıkışı ucuz tutan tasarım kısıtı

> **Kural değerlendirme mantığı, akış motorundan habersiz saf bir fonksiyon olacak:** `(state, reading) → violation?`. Job topolojisi, state backend erişimi, checkpoint ve offset yönetimi bu fonksiyonun dışında kalacak.

Bu kısıt, ④'ten çıkış maliyetini *Yüksek*'ten *Orta*'ya indiren tek şeydir. Adım 6'da bu ayrımın korunması bir kod review kuralıdır.

**Bilinçli olarak bu ADR'de karara bağlanmayan:** job'un hangi dilde/arayüzde yazılacağı (Java/Scala, Python API, veya deklaratif SQL + örüntü eşleme). Üçü de aynı motoru kullanıyor, geri dönüşü ucuz ve seçimi Adım 6'nın implementasyon detayı. Bu ADR'nin konusu motor sınıfıdır.

## Geri dönüş maliyeti

| Çıkış | Ne zaman gerekir | Maliyet | Neden |
|---|---|---|---|
| **④ → ②** (framework'ü bırak, kendi consumer'ına dön) | Operasyonel yük taşınamazsa, veya bahis kaybedilip operatörlerin hiçbiri kullanılmazsa | **Orta** | Saf fonksiyon taşınır; job topolojisi, deployment, checkpoint altyapısı ve CI hattı sökülür. State 25 MB'da kaldığı sürece teknik engel yok. |
| **④ → ⑤** (state'i uzak store'a taşı) | Checkpoint/savepoint operasyonu sürdürülemez bulunursa | **Orta** | Saf fonksiyon taşınır; A-03'ün bağımlılık yüzeyi ve §2.9 yeniden hesaplanır. |
| **④ → ③** | — | — | ③ elendi (servisi JVM'e taşıma bedeli); geri dönülecek bir yer değil |

| | |
|---|---|
| **Erken uyarı sinyali** | ① **consumer lag** sürekli artıyorsa (işleme yetişmiyor); ② **checkpoint süresi ve başarısızlık oranı** yükseliyorsa (state beklenenden büyük veya depolama yetersiz); ③ **back-pressure oranı** sıfırdan farklıysa (downstream darboğaz); ④ **savepoint/rescale süresi** dakikaları aşıyorsa (ölçekleme pratikte yapılamaz hâle gelir); ⑤ **SLI-04 (canary alert age)** sessiz başarısızlığı yakalarsa |

### Durum neden *Kabul*

Beş sinyalin beşi de Adım 6'da observability'ye bağlanabilir ve Adım 7 load testinde ölçülebilir — çünkü bu bileşen Slice 1'in içinde çalışıyor. Şablonun *Kabul* için istediği şart sağlanıyor.

ADR-0002'nin *Öneri*, bu ADR'nin *Kabul* olması bir tutarsızlık değil: aradaki tek fark, bu kararın erken uyarı sinyalinin gözlemlenebilir olması. Kuralın çalıştığının kanıtı.
