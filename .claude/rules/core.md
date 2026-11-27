# Pazarlıksız Kurallar

Bu dosya her oturumda yüklenir. Buraya yalnızca **ihlali pahalı** olan kurallar girer; ayrıntı diğer kural dosyalarındadır.

## Oturum açılışı

İş başlamadan üç dosya okunur: [`.claude/devir.md`](../devir.md) (geçen oturum nerede kaldı), [`docs/README.md`](../../docs/README.md) (ilerleme sırası — hangi adımdayız) ve [`docs/05-adr/karar-haritasi.md`](../../docs/05-adr/karar-haritasi.md) (hangi karar hangi durumda). Context özetlendiğinde veya oturum bölündüğünde yeniden bu dosyalardan çıpalanılır — hatırlanan değil, yazılan geçerlidir.

Oturum kapanırken `devir.md` güncellenir: nerede kaldık, sıradaki adım, açık konular. Kısa tutulur; ayrıntı dokümanlara yazılır.

## Çalışma akışı

Her iş **plan → kısa tartışma → tasklara bölme → parça parça ilerleme** sırasıyla yürür. Plan onaylanmadan iş başlamaz. Ayrıntı: [`workflow.md`](workflow.md).

## Bağlam zinciri

```
Gereksinim/SLO → BOTE → HLD → ADR → C4 → Kod → Load test
```

Bir halkaya dokunan değişiklik, **aşağı akıştaki halkalar kontrol edilmeden kapanmaz.** SLO değiştiyse BOTE'ye; BOTE değiştiyse ona dayanan ADR'lere ve HLD'ye; HLD değiştiyse C4'e ve koda bakılır. Kontrol edilip etkilenmediği görülen halka için de tek satır not düşülür — sessizce atlanmaz.

## Kurallar

1. **Kaynaksız sayı yazılmaz.** Her sayı ya *varsayım* (gerekçesiyle), ya *türetilmiş* (formülüyle), ya *ölçülmüş* (ölçüm yöntemiyle) olur.
2. **Hipotez karar değildir.** `project-summary.md` teknoloji tablosu bir hipotez listesidir; bir teknoloji ancak kendi ADR'si yazıldığında karardır. Hipotez, karar gibi anlatılmaz.
3. **Her mimari karar bir ADR'dir** ve aynı değişiklikte `karar-haritasi.md`'ye bir satır ekler. Satırı olmayan ADR eksik ADR'dir.
4. **ADR silinmez, numarası değişmez.** Yanlış çıkan ADR'nin durumu *Değiştirildi* olur ve yerine geçen ADR'ye atıf verilir.
5. **`TBD` bir eksik olmak zorunda değildir.** Bilinçli `TBD` satırları (ör. Analytics Database — B-10) kapatacak sayı doğmadan kapatılmaz; tahminle ADR yazılmaz.
6. **Tasarım kodu beklemez, kod tasarımı bekler.** Bir dikey kesidin HLD'si ve ADR'leri yazılmadan o kesidin kodu yazılmaz.
7. **Doküman sorulmadan yeniden yazılmaz.** Mevcut metin korunur, değişiklik hedefli yapılır; gerekçe satırları ve `>` uyarı blokları silinmez.
8. **Dil:** anlatım Türkçe, teknik terim İngilizce (`event-time`, `back-pressure`, `partition`, `idempotency`). Terim çevrilmez, glossary'de açıklanır.
9. **Üretilmiş dosya repoya girmez** (`__pycache__/`, `*.pyc`, build çıktıları, araç çıktı klasörleri).
10. **Emin değilsen sor.** Sayıya dayanmayan bir boşluğu tahminle doldurmak, bu projede hatadan daha pahalıdır.
11. **Oturum içinde commit atılmaz.** `git commit`, `git push`, `git reset`, tag — hiçbiri agent tarafından çalıştırılmaz; kullanıcı istese bile commit **kullanıcının kendi denetiminde** atılır. Agent yalnızca ne commit edilmesi gerektiğini ve mesaj taslağını söyler. Commit mesajı kuralları: [`code.md`](code.md).

## Teknik engel

Kural 4 ve kural 11 metinde kalmıyor: [`.claude/hooks/guard.js`](../hooks/guard.js) bir `PreToolUse` hook'u olarak çalışır ve agent'ın `git commit/push/tag/reset/revert` komutlarını ve durumu *Kabul* olan ADR dosyalarına yazma girişimlerini **reddeder**. Hook bir engeli reddettiğinde yapılacak şey kullanıcıya sormaktır; etrafından dolaşmak (Bash ile dosya yazma, başka komut biçimi) yasaktır.

## Değişiklikten sonra

Dokümana dokunan her değişiklik şunları bırakır: revizyon tarihi, `karar-haritasi.md` satırının güncellenmesi (gerekiyorsa) ve bağlam zincirinde kontrol edilen halkaların kısa listesi.
