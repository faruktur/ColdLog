# Dokümantasyon Kuralları

Projenin çalışma kuralları — hipotez/karar ayrımı, her kararın bir ADR olması, her sayının kaynağı, doküman dili, tasarım-kod sırası — **[`docs/README.md`](../../docs/README.md) içinde yazılıdır ve tek kaynaktır.** Bu dosya o kuralların uygulanış ayrıntısını tutar; çelişki halinde `docs/README.md` geçerlidir.

## ADR yazarken

- Şablon: [`docs/05-adr/template.md`](../../docs/05-adr/template.md). Numara artar, boşluk bırakılmaz.
- Aynı değişiklikte [`karar-haritasi.md`](../../docs/05-adr/karar-haritasi.md) tablosuna satır eklenir: dayandığı SLO/NFR, BOTE satırı, SLI, metrik adı, tahmin. Son kolon (ölçülen) Adım 7'de dolar.
- **Durum alanı ciddiye alınır.** *Kabul* için kararın erken uyarı sinyali seçilen dikey kesit içinde **gözlemlenebilir** olmalıdır. Sinyali ölçülemiyorsa karar *Öneri* kalır — ADR-0002 bu yüzden *Öneri*, ADR-0003 ve ADR-0004 *Kabul*.
- Her ADR *Sonuçlar* bölümünde **kabul edilen bedeli** yazar. Bedeli yazılmamış karar, karar değil tercih beyanıdır.
- Reddedilen alternatifler sayıyla gerekçelendirilir; "daha basit" tek başına gerekçe değildir.

## Revizyon

- Revize edilen satır **silinmez, üstü çizilmez**: neyin değiştiği, ne zaman ve hangi dokümana dayanarak değiştiği satırın içine yazılır (`karar-haritasi.md` H-04 satırı örnektir).
- Bir ADR başka bir ADR'yi geçersiz kılıyorsa iki tarafa da atıf konur.
- Revizyon, doküman başlığında ve `docs/README.md` klasör tablosunda görünür: `**ADR-00xx sonrası revize (YYYY-MM-DD)**`.

## Yeni doküman

- Klasörler peşin açılmaz, sırası gelince açılır (`docs/README.md` — İlerleme sırası).
- Yeni klasör veya doküman eklendiğinde `docs/README.md` klasör düzeni tablosuna, gerekiyorsa `CLAUDE.md` bağlam gruplarına satırı eklenir.
- İlk kez kullanılan terim [`glossary.md`](../../docs/01-project-info/glossary.md)'ye girer.

## Ölçüm boşlukları

SLO'su olmayan bir yol veya metriği olmayan bir karar varsa, bu **bilinçli boşluk olarak yazılır** (`*(SLO yok — bilinçli boşluk)*`). Gizlenmiş boşluk, açıkça yazılmış boşluktan pahalıdır.
