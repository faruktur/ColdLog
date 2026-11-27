# Kod Kuralları

**Durum:** Henüz kod yok. Slice 1 (Adım 6) başlayınca bu dosya dizin düzeni ve CI akışıyla büyür. Build/test komutları [`.claude/stack.md`](../stack.md) içinde tutulur, burada tekrarlanmaz.

## Ne zaman kod yazılır

Bir dikey kesidin kodu; o kesidin HLD'si ([`docs/04-design/hld.md`](../../docs/04-design/hld.md)), ilgili ADR'leri ve C4 component seviyesi ([`docs/06-c4/c4-model.md`](../../docs/06-c4/c4-model.md)) yazılmadan başlamaz.

**İlk dikey kesit:** telemetri ingest → stream processing → asset state → kural tabanlı uyarı.

## Dikey kesit neyi birlikte içerir

Kod tek başına "biten iş" değildir. Bir kesit şunlarla birlikte kapanır: observability (metrik + log + trace), test, CI, deployment manifest'i. Biri eksikse kesit açık sayılır.

## Observability — kodun ADR'ye bağlandığı nokta

- `karar-haritasi.md`'de **Metrik** kolonunda adı yazan her metrik, kodda **o adla** yayınlanır. Metrik adı serbest seçim değil, dokümanda verilmiş bir sözdür; değişecekse önce doküman değişir.
- SLI-04 enstrümantasyonu ve canary, load test aracından **önce** gelir (H-10).
- Bir metriğin adı veya anlamı değişiyorsa `karar-haritasi.md` aynı değişiklikte güncellenir.

## Hot path disiplini

HLD'nin hot path için koyduğu sınırlar koda aynen geçer: hot path'in Kafka dışı veri bağımlılığı yoktur (H-06); Redis best-effort read projection'dır ve hot path'te değildir (H-07); reorder buffer yoktur (H-03); hot path ve late path ayrı deployment'tır (H-09). Bu sınırlardan birini esnetmek gerekiyorsa kod yazılmaz — önce HLD ve ilgili ADR revize edilir.

## Kısayol kaydı

Bilinen bir sınırla yazılan çözüm yanına tek satır bırakır:

```
shortcut: <sınır ne>, <ne zaman yükseltilecek>
```

Kesit kapanırken kalan kısayollar taranır; mimari etkisi olanlar dokümana (ADR veya HLD notu) taşınır, kalanı kodda kalır.

## Test

Yeni mantık (branch, loop, parser, zaman/state hesabı, güvenlik) testsiz kapanmaz; trivial değişiklik test istemez. Zaman ve state mantığı (event-time, stale timer, dedup aralığı) için test **davranışa** bakar, implementasyon detayına değil.

## Commit

Commit'i agent atmaz ([`core.md`](core.md) — kural 11); aşağıdakiler kullanıcının attığı commit'in kurallarıdır ve agent yalnızca mesaj taslağı önerir.

- commit mesajı türkçe yazılır
- Commit mesajı ne yapıldığını ve hangi dokümana/ADR'ye dayandığını söyler.
- Doküman ve onu uygulayan kod mümkünse aynı commit'te gider; ayrıysa commit mesajı diğerine atıf verir.
- Üretilmiş dosya commit edilmez. Sır içeren dosya (`.env`, credential) hiçbir koşulda commit edilmez.
- Commit mesajı task numarası ile başlar: `TASK-1234`
- 