# ADR-0001: Mimari kararları ADR formatında kaydetme

| | |
|---|---|
| **Durum** | Kabul |
| **Tarih** | 2026-11-24 |
| **İlgili** | `docs/README.md`, `docs/05-adr/template.md` |

## Bağlam

FleetStream'in birincil amacı çalışan bir sistem üretmek değil, alınan mimari kararların **neden** alındığını anlayıp savunabilmek. Bu durumda en büyük risk, kararın kendisinden çok kararın gerekçesinin kaybolması: hangi sayıya bakarak time-series store seçtiğimizi üç hafta sonra hatırlamazsak, proje "çalışıyor ama neden böyle olduğunu bilmiyorum" durumuna düşer ve öğrenme hedefi boşa gider.

Proje tek kişilik ve bir takıma hesap verme zorunluluğu yok. Yani kayıt tutma dışsal bir zorunluluk değil; sırf kendi muhakemesini sonradan denetleyebilmek için tutulacak. Bu, kayıt formatının **ağır olmaması** kısıtını getiriyor — doldurması yorucu bir şablon doldurulmaz.

## Hesap dayanağı

Hesap gerektirmiyor; süreç kararı. Dayanak nitelikseldir: projede geri dönüşü maliyetli en az 3 teknoloji seçimi var (time-series storage, stream processing, analytics database — hepsi `01-project-info/project-summary.md`'de `TBD`) ve bunların her biri veri modeli ile birlikte kalıcı hâle geliyor.

## Değerlendirilen alternatifler

| Alternatif | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|
| Hiçbir şey yapmamak (kararlar kodda ve kafada kalsın) | Sıfır yazma maliyeti | Gerekçe kaybolur; "neden Kafka?" sorusuna cevap kalmaz | Projenin birincil amacını doğrudan baltalıyor |
| Tek büyük tasarım dokümanı (SDD) | Her şey bir yerde, bütünsel okunur | Kararlar metnin içinde erir, değişince eski gerekçe silinir — **karar geçmişi tutulamaz** | Hangi kararın hangi aşamada ve neye dayanarak değiştiğini göstermiyor |
| ADR per karar (seçilen) | Her karar kendi bağlamı ve alternatifleriyle ayrı dosya; değişiklik eski ADR'yi silmeden üstüne yazılır | Dosya sayısı artar, aralarında atıf disiplini gerekir | — |

## Karar

Geri dönüşü maliyetli her mimari seçim, `docs/05-adr/` altında numaralı bir ADR olarak kaydedilecek. Şablon `template.md`; standart ADR alanlarına ek olarak iki alan zorunlu: **Hesap dayanağı** (kararı zorlayan sayı ve kaynağı) ve **Geri dönüş maliyeti** (çıkış maliyeti + erken uyarı sinyali). ADR'ler silinmez; yanlış çıkan ADR *Değiştirildi* durumuna alınır ve yerine geçen ADR'ye atıf verir.

Günlük implementasyon seçimleri (kütüphane, isimlendirme, klasör yapısı) ADR'ye girmez — ölçüt, **kararı geri almanın bir haftadan fazla iş olması**.

## Sonuçlar

- **Kazandığımız:** Her teknoloji seçimi bir sayıya bağlanmak zorunda. "Hesap dayanağı" alanı boş kalıyorsa karar henüz verilmemiş demektir — bu alan erken uyarı mekanizması olarak çalışıyor.
- **Kabul ettiğimiz bedel:** Her önemli karar öncesi ~20-30 dakikalık yazma işi. Alternatif tablosunda en az iki gerçek alternatif üretme zorunluluğu, kolay kararları da yavaşlatıyor.
- **Etkilenen bileşenler:** Yok (süreç kararı). `docs/` ağacı ve çalışma ritüeli bu karara bağlı.

## Geri dönüş maliyeti

| | |
|---|---|
| **Maliyet** | Düşük (<1 hafta) — şablon değiştirilebilir, yazılan ADR'ler metin olarak kalır |
| **Erken uyarı sinyali** | Bir teknoloji kararı ADR yazılmadan koda girdiyse süreç tutmuyor demektir. İkinci sinyal: ADR'lerde "Hesap dayanağı" alanının düzenli olarak *"hesap gerektirmiyor"* ile doldurulması — bu, BOTE'nin kararları gerçekten yönlendirmediğini gösterir. |
