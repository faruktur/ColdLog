# FleetStream — Agent Yönlendirmesi

Bu dosya **proje bilgisi tutmaz**, nerede ne olduğunu söyler. Her bilgi tek bir dosyada yaşar; burada yalnızca adresi vardır. Bir bilgi iki yerde yazıyorsa biri eskimiştir — kaynak her zaman `docs/` altındaki dosyadır.

**Proje:** Hareket halindeki varlıkların yüksek hacimli telemetrisini işleyen gerçek zamanlı filo ve soğuk zincir takip sistemi. → [`docs/01-project-info/project-summary.md`](docs/01-project-info/project-summary.md)

**Çalışma düzeni, ilerleme sırası ve doküman kuralları:** → [`docs/README.md`](docs/README.md)

@.claude/rules/core.md

## Bağlam grupları

Bir konuya dokunuyorsan, o satırdaki dosyaların **tamamı** okunur. Tek dosyaya bakıp karar vermek bu projede eksik karardır.

| Çalıştığın konu | Birlikte okunacaklar |
|---|---|
| Gereksinim, SLO, kapsam | [`02-requirements/nfr-slo.md`](docs/02-requirements/nfr-slo.md) · [`functional.md`](docs/02-requirements/functional.md) · [`out-of-scope.md`](docs/02-requirements/out-of-scope.md) |
| Kapasite, sayı, büyüklük | [`03-capacity/bote-model.md`](docs/03-capacity/bote-model.md) · [`bote.py`](docs/03-capacity/bote.py) |
| Tasarım, akış, bileşen | [`04-design/hld.md`](docs/04-design/hld.md) · [`06-c4/c4-model.md`](docs/06-c4/c4-model.md) |
| Mimari karar (yeni / revizyon) | [`05-adr/karar-haritasi.md`](docs/05-adr/karar-haritasi.md) · [`05-adr/template.md`](docs/05-adr/template.md) · ilgili ADR · [`.claude/rules/docs.md`](.claude/rules/docs.md) |
| Terim, isimlendirme | [`01-project-info/glossary.md`](docs/01-project-info/glossary.md) |
| Teknoloji seçimi, araç | [`.claude/stack.md`](.claude/stack.md) · ilgili ADR |
| Kod (Slice 1) | [`04-design/hld.md`](docs/04-design/hld.md) · ADR-0003 · ADR-0004 · [`.claude/rules/code.md`](.claude/rules/code.md) |
| Load test, doğrulama | [`05-adr/karar-haritasi.md`](docs/05-adr/karar-haritasi.md) (son iki kolon) · [`03-capacity/bote-model.md`](docs/03-capacity/bote-model.md) |

## Kural dosyaları

| Dosya | Ne zaman okunur |
|---|---|
| [`.claude/rules/core.md`](.claude/rules/core.md) | Her oturumda otomatik yüklenir — pazarlıksız kurallar |
| [`.claude/rules/workflow.md`](.claude/rules/workflow.md) | Bir işe başlarken — plan, tartışma, tasklara bölme |
| [`.claude/devir.md`](.claude/devir.md) | Oturum başında ve sonunda — kaldığımız yer |
| [`.claude/rules/docs.md`](.claude/rules/docs.md) | Doküman veya ADR yazarken / revize ederken |
| [`.claude/rules/code.md`](.claude/rules/code.md) | Kod, test, CI veya deployment'a dokunurken |
| [`.claude/stack.md`](.claude/stack.md) | Teknoloji, versiyon veya araç sorusunda |
