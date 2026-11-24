# ADR-NNNN: <Kararın tek cümlelik başlığı>

| | |
|---|---|
| **Durum** | Öneri / Kabul / Reddedildi / Değiştirildi (ADR-NNNN ile) / Geri alındı |
| **Tarih** | YYYY-MM-DD |
| **İlgili** | ADR-NNNN, `docs/...` |

## Bağlam

Hangi problemi çözmek zorundayız ve hangi kısıtlar altında? Burada **teknoloji adı geçmez** — sadece problem, kısıtlar ve gerilim yazılır. Bu bölümü okuyan biri kararı kendi başına verebilecek bilgiye sahip olmalı.

## Hesap dayanağı

Bu kararı zorlayan **sayı** nedir? Kaynağına atıf ver:

> Örnek: ortalama 20.000 event/sn, tepe 40.000 event/sn (`03-capacity/bote-model.md#ingest-yuku`), alarm p99 gecikme hedefi 5 sn (`02-requirements/nfr-slo.md#alarm`).

Sayıya dayanmayan bir karar ise bunu açıkça yaz: *"Hesap gerektirmiyor; gerekçe <X>."* Bu alanı boş bırakmak, kararın savunulamaz olduğunu kabul etmek demektir.

## Değerlendirilen alternatifler

| Alternatif | Artı | Eksi | Neden seçilmedi |
|---|---|---|---|
| A | | | |
| B | | | |
| C (seçilen) | | | — |

En az bir alternatif **"hiçbir şey yapmamak / mevcutla devam etmek"** olmalı. Tek alternatifli ADR, karar değil gerekçelendirmedir.

## Karar

Tek paragraf, net ve emir kipinde. *"X kullanacağız, çünkü ..."*

## Sonuçlar

- **Kazandığımız:**
- **Kabul ettiğimiz bedel / teknik borç:**
- **Etkilenen bileşenler:**

## Geri dönüş maliyeti

| | |
|---|---|
| **Maliyet** | Düşük (<1 hafta) / Orta (1-4 hafta) / Yüksek (>1 ay, veri göçü gerekir) |
| **Erken uyarı sinyali** | Bu kararın yanlış olduğunu hangi metrik gösterir? Örn: *consumer lag sürekli artıyorsa*, *p99 sorgu süresi 2 sn'yi geçiyorsa*. |

Yüksek maliyetli kararlar, erken uyarı sinyali observability'ye bir dashboard/alert olarak yansıtılmadan *Kabul* durumuna geçmez.
