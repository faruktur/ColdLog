# ADR-0002: Ham telemetri serisi, PostgreSQL ailesi içinde time-series eklentisiyle saklanacak

| | |
|---|---|
| **Durum** | **Öneri** — *Kabul* değil (gerekçe: "Geri dönüş maliyeti" bölümünün sonu) |
| **Tarih** | 2026-11-26 |
| **İlgili** | `03-capacity/bote-model.md` §2.10, `02-requirements/nfr-slo.md` R-01/R-02/R-03/L-03/L-04, `04-design/hld.md` §2.3, ADR-0003 |

## Bağlam

Ham Reading'ler 90 gün saklanacak (R-01) ve bu süre boyunca iki şekilde sorgulanacak: tek bir Asset'in son 24 saatlik serisi (L-03), ve bir Asset'in belirli bir zaman aralığı (`04-design/hld.md` §2.3 — sıra dışı okumaların geriye dönük yeniden değerlendirilmesi buna bağlı). Ayrıca downsample edilmiş veri 1 yıl saklanacak (R-02), 5 dk / 1 saat kovalarıyla (R-03).

Kısıtlar: veri üretimi hiç durmaz, sabit hızla akar ve retention süresi dolduğunda eski verinin **sistemi yavaşlatmadan** ortadan kaybolması gerekir. Sistem aynı anda yazma altındadır — yani silme işlemi, yazma yolunun yanında çalışan bir arka plan yükü olarak düşünülmek zorundadır.

Gerilim şu: bu bileşen Faz 2'de hayata geçecek, ama kararı **şimdi** vermek zorundayız, çünkü Slice 1'in bilinçli olarak boş bıraktığı yer (sıra dışı okumanın geriye dönük değerlendirilmesi) bu depoya bağımlı. Kararı ertelemek, HLD'deki o boşluğu "ölçülmeyen bir boşluk" olmaktan çıkarıp "tanımlanmamış bir boşluk" hâline getirirdi.

## Hesap dayanağı

> 90 gün ham satır: **155,5 milyar** · ham boyut: **31,1 TB** · sıkıştırılmış (15× varsayımı): **~2,1 TB** · sürekli yazma: **20.000 satır/sn**, tepe 40.000 (`03-capacity/bote-model.md` §2.10, S-03).
>
> L-03 sorgusunun döndürdüğü satır sayısı: `24 × 3600 / 5 =` **17.280** (`02-requirements/nfr-slo.md` L-03, S-02).

**Bu sayıların söylediği birinci şey: bu bir sorgu motoru kararı değil.** L-03 tek Asset için 17.280 satır döndürüyor; doğru indeksle bunu herhangi bir ilişkisel veritabanı 1 saniyenin çok altında yapar. Kararı zorlayan iki şey var ve ikisi de okuma tarafında değil:

1. **Sürekli 20.000 satır/sn yazma.** 155 milyar satırlık tek bir tablonun B-tree indeksi belleğe sığmaz; her insert rastgele disk I/O'suna döner.
2. **90 günün dolması.** `DELETE WHERE time < now() - 90 gün` milyarlarca satır demek: vacuum yükü, şişen tablo ve yazma yolunu yavaşlatan bir arka plan işi.

Dolayısıyla bu ADR'nin konusu **yazma hızı + veri yaşam döngüsü**dür.

## Değerlendirilen alternatifler

| Alternatif | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|
| **① Hiçbir şey yapma** — mevcut PostgreSQL'de düz tablo | Yeni bileşen yok, bildiğimiz sistem | İndeks belleğe sığmaz; retention silme işlemi sistemi ayakta tutamaz | Yukarıdaki iki forsing kısıttan ikisinde de kırılıyor |
| **② PostgreSQL + elle günlük partition + elle arşivleme** | Retention `DROP TABLE reading_YYYY_MM_DD` → anlık, vacuum yok. Partition başına indeks küçük kalır. **Doğru çalışır.** | Sıkıştırma yok → 31 TB disk (satır bazlı depolama columnar sıkıştırmaz). Partition oluşturma/düşürme ve R-02/R-03 downsampling'i **biz** yazar, **biz** bakarız. | ③ aynı işi hazır veriyor, üstüne sıkıştırma ve downsampling ekliyor |
| **③ PostgreSQL + time-series eklentisi (TimescaleDB)** *(seçilen)* | ②'nin tamamı hazır (hypertable = otomatik chunk). Üstüne: native columnar sıkıştırma, declarative retention policy, continuous aggregate → **R-02 ve R-03'ü ek kod olmadan kapatır**. Aynı SQL, aynı bağlantı havuzu, aynı backup aracı. | Tek node yazma — 20.000 satır/sn yapılabilir ama **batch insert zorunlu**. Eklenti olduğu için her managed PostgreSQL'de bulunmaz. | — |
| **④ Ayrı columnar motor (ClickHouse)** | 20.000 satır/sn onun için önemsiz; sıkıştırma 15×'ten iyi; L-04 agregasyonunda açık ara en hızlı | **İkinci veri sistemi:** ayrı backup, ayrı monitoring, ayrı operasyon bilgisi. Tek satır update/delete yok → D-02 idempotency'si farklı çözülür. SQL'e benzer ama aynı değil. | **Reddedilmedi — ertelendi.** Gerekçe aşağıda. |

### ④ neden reddedilmedi de ertelendi

ClickHouse'un gerçekten kazandığı yer L-04'tür: filo geneli, 90 güne kadar agregasyon. Ama o sorgu `docs/README.md`'de **Analytics Database** olarak bilinçli `TBD` duruyor, çünkü FR-19 agregasyonun kaç Asset üzerinden yapılacağını söylemiyor ve tek Asset ile filo geneli arasında ~100.000× fark var. Yani ④'ü zorlayacak sayı **henüz üretilmedi**.

④, bu ADR'nin değil, **FR-19 netleştiğinde yazılacak ADR'nin** adayıdır. Bunu burada yazmanın sebebi: aksi hâlde "ClickHouse neden değerlendirilip alınmadı" sorusu altı ay sonra cevapsız kalır.

## Karar

**Ham telemetri serisini PostgreSQL ailesi içinde, time-series eklentisi (TimescaleDB) üzerinde saklayacağız.** Çünkü kararı zorlayan şey sorgu performansı değil yazma hızı ve retention yönetimidir; ② bu iki problemi doğru çözüyor ama partition yönetimi ile downsampling kodunu bize bırakıyor; ③ aynı çözümü hazır verip üstüne columnar sıkıştırma ve continuous aggregate ekliyor — ve bunların hepsini **ikinci bir veri sistemi işletmek zorunda kalmadan** yapıyor.

## Sonuçlar

- **Kazandığımız:** Tek veri sistemi (aynı SQL, aynı backup, aynı monitoring). R-02 ve R-03 ek kod olmadan kapanıyor. Retention bir politika satırı, bir cron job değil.
- **Kabul ettiğimiz bedel / teknik borç:**
  - **Cold path writer event-by-event yazamaz, batch yazar.** Tek node yazma kısıtının tasarıma yazılması gereken sonucu bu. Hot path etkilenmiyor (o Redis + PostgreSQL alert store'a gidiyor), ama cold path writer'ın tasarımı buna göre yapılacak.
  - **15× sıkıştırma bir varsayım, ölçüm değil.** Aşağıdaki duyarlılık tablosu bunun kararı değiştirmediğini gösteriyor, ama disk bütçesini değiştirir.
  - L-04 (filo geneli agregasyon) bu depoda **en iyi** çözülmüyor, sadece çözülüyor. En iyisi ayrı bir ADR'nin konusu.
- **Etkilenen bileşenler:** Cold path writer (Faz 2), Query API (FR-18/FR-19), Late Path Consumer'ın geriye dönük değerlendirme yolu (`04-design/hld.md` §2.3).

### Sıkıştırma oranına duyarlılık

| Gerçekleşen oran | Disk | Karar değişir mi? |
|---|---|---|
| 15× (varsayım) | 2,1 TB | — |
| 5× | 6,2 TB | Hayır |
| 2× | 15,6 TB | Hayır |
| 1× (sıkıştırma hiç çalışmıyor) | 31,1 TB | Hayır — ② de aynı yerde olurdu |

Bu tablonun ADR'de olma sebebi tek bir cümle: **karar sıkıştırma oranına duyarsız.** Oran kaç çıkarsa çıksın ③ hâlâ ②'den iyidir. Bu, Faz 2 bileşeni için ölçüm beklemeden karar vermeyi savunulabilir kılan argümandır.

## Geri dönüş maliyeti

Ölçülen şey, **seçilen seçenekten çıkmanın** maliyetidir. ③'ten iki ayrı çıkış var ve maliyetleri birbirine benzemiyor:

| Çıkış | Ne zaman gerekir | Maliyet | Neden |
|---|---|---|---|
| **③ → ②** (eklentiden vazgeç, elle partition'a dön) | Sıkıştırma veya yazma hızı beklediğimizi vermezse; eklentinin kurulamadığı bir ortama gitmek gerekirse | **Düşük** | Aynı PostgreSQL, aynı tablo, aynı SQL. Veri yerinde kalır, göç yok. Uygulama kodu değişmez — sadece chunk/retention yönetimini biz yazmaya başlarız. |
| **③ → ④** (ayrı columnar motora geç) | L-04 agregasyonu PostgreSQL ailesinde hiç tutmazsa | **Yüksek** | 31 TB veri göçü, farklı SQL lehçesi, yazma yolu baştan, D-02 idempotency'si yeniden çözülür, ikinci sistemin operasyonu üstlenilir. |

③ → ① diye bir çıkış yoktur; ① elendi, geri dönülecek bir yer değil.

**Bu tablonun söylediği şey:** ③'ün yanlış çıkmasının *en olası* yolu ucuz bir çıkışa açılıyor (ailede kalıyoruz). Pahalı çıkışı zorlayacak sebep ise zaten başka bir ADR'ye ertelenmiş durumda. Bir kararın savunulabilirliğinin en pratik ölçütü budur.

| | |
|---|---|
| **Erken uyarı sinyali** | ① insert p99 artıyorsa (batch yazma varsayımı yetersiz); ② gerçekleşen sıkıştırma oranı 5×'in altına düşerse (disk bütçesi 6 TB'ı geçer); ③ retention silme işleminin süresi yazma gecikmesini etkiliyorsa |

### Durum neden *Öneri*, *Kabul* değil

Şablonun kuralı: *"Yüksek maliyetli kararlar, erken uyarı sinyali observability'ye bir dashboard/alert olarak yansıtılmadan Kabul durumuna geçmez."*

Bu bileşen Faz 2'de ve Adım 7 load testinde **çalışmayacak**. Dolayısıyla yukarıdaki üç sinyalin hiçbirini gözlemleyemeyeceğiz. `karar-haritasi.md`'de bu satırın *tahmin* kolonu dolu, *ölçülen* kolonu uzun süre boş kalacak. Bu durumu gizlemek yerine ADR'nin durum alanına yazmak tercih edildi: karar alınmıştır, gerekçesi yazılıdır, **ama doğrulanmamıştır.**

Durum *Kabul*'e geçer: cold path Faz 2'de hayata geçip üç sinyal dashboard'a bağlandığında.
